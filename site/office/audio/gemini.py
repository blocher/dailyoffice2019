"""Gemini office audio via the Gemini API (google-genai) TTS models.

Uses multi-speaker TTS so dialogue segments (e.g. leader + congregation) are
synthesized in a single request with natural conversational pacing. Reuses v2
batching/assembly; stores files under MEDIA_ROOT/audio_gemini/.

Docs: https://ai.google.dev/gemini-api/docs/speech-generation
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import tempfile
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from django.conf import settings

from office.audio.v2 import (
    CLIPS_SUBDIR,
    ClipSpec,
    _absolute_url,
    _ensure_subdir,
    _media_url,
    _run_ffmpeg,
    audio_duration,
    audio_provider,
    build_v2_audio,
    clip_generation_lock,
)
from office.utils import generate_uuid_from_string

logger = logging.getLogger(__name__)

AUDIO_GEMINI_SUBDIR = "audio_gemini"

# Gemini occasionally "runs away" and recites past the supplied text, more so on
# long passages. Smaller chunks make that far less likely and make any rejected
# clip cheap to regenerate. But every chunk is an independent TTS call with its own
# pitch/register, so more chunks means more audible pitch jumps on the same speaker.
# This value balances the two: larger than the runaway-safe minimum to keep a
# reading's register consistent, still well under the v2 baseline (1500). Consecutive
# same-speaker chunks are joined with a 0ms gap so splitting never hurts flow.
GEMINI_MAX_CHUNK_CHARS = 1200

# Gemini API prebuilt voices.
ROLE_VOICES = {
    "leader": "Iapetus",
    "congregation": "Erinome",
    "reader": "Schedar",
}

READER_VOICES = (
    "Anilam",
    "Leda",
    "Zubenelgenubi",
    "Orus",
    "Zephyr",
)

# The reader voice for a single office is chosen once (see build_gemini_audio)
# and shared by every reader chunk via this contextvar, so the scripture reader
# never switches voices mid-office. copy_context() in v2._run_spoken_tasks
# propagates it into the parallel synthesis worker threads. When unset (e.g. a
# direct generate_gemini_dialogue_clip call), we fall back to a random choice.
_reader_voice: ContextVar[str | None] = ContextVar("gemini_reader_voice", default=None)


@dataclass
class BatchChunk:
    """A single cache-miss segment queued for asynchronous batch synthesis."""

    cache_key: str
    prompt: str
    file_path: str
    spoken_chars: int
    roles: list = field(default_factory=list)
    voices: dict = field(default_factory=dict)


class BatchClipCollector:
    """Thread-safe registry of cache-miss chunks gathered during a dry-run render.

    Dedupes by cache key (the same text can appear in many offices/variants) so
    each unique clip is synthesized exactly once by the batch job.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._chunks: dict[str, BatchChunk] = {}

    def record(self, chunk: BatchChunk):
        with self._lock:
            self._chunks.setdefault(chunk.cache_key, chunk)

    def chunks(self) -> list[BatchChunk]:
        with self._lock:
            return list(self._chunks.values())

    def __len__(self):
        with self._lock:
            return len(self._chunks)


# When set (during a batch pre-warm's collection pass), cache-miss segments are
# recorded here instead of being synthesized in real time; see
# generate_gemini_dialogue_clip.
_batch_collector: ContextVar[BatchClipCollector | None] = ContextVar("gemini_batch_collector", default=None)


@contextmanager
def collecting_batch_chunks():
    """Within this context, gemini synthesis records cache-miss chunks instead of
    calling the API, and every office renders as "unavailable" (no assembly).

    Yields the collector so the caller can hand the gathered chunks to the batch
    synthesizer. Interactive requests must never run inside this context.
    """
    collector = BatchClipCollector()
    token = _batch_collector.set(collector)
    try:
        yield collector
    finally:
        _batch_collector.reset(token)


# Speaker labels used in multi-speaker transcripts (must be alphanumeric).
ROLE_SPEAKERS = {
    "leader": "Leader",
    "congregation": "Congregation",
    "reader": "Reader",
}

# Gemini TTS output is raw 16-bit PCM at 24 kHz, mono.
PCM_SAMPLE_RATE = 24000
# Preview TTS models intermittently 404/500 for a few seconds; retry patiently.
MAX_SYNTHESIS_ATTEMPTS = 4

# Duration guardrails. Gemini TTS occasionally keeps talking after a short
# text and recites the rest of the passage from memory (in whatever
# translation it prefers). Normal English speech is ~13-17 chars/second, so
# audio far outside these bounds means the model did not read the text as
# given and the clip must be rejected before it poisons the cache.
MAX_SECONDS_BASE = 6.0
MAX_SECONDS_PER_CHAR = 1 / 6.0  # far slower than any real reading
MIN_SECONDS_PER_CHAR = 1 / 40.0  # far faster than any real reading

# Gemini bills audio output at 25 tokens per second of speech. We size
# max_output_tokens off the plausible-duration ceiling so a runaway recitation
# stops early (cheap, fast) instead of generating minutes of audio we would
# reject anyway. The small margin above 25 keeps legitimate reads (which run far
# below the ceiling) from ever being truncated even if a voice paces slightly
# slower than expected.
AUDIO_TOKENS_PER_SECOND = 30

# NOTE: Keep prompts in the documented "TTS the following..." shape. Elaborate
# sectioned prompts (headings like GLOBAL PERFORMANCE PROFILE / DIRECTOR'S
# NOTES) intermittently fail Gemini's speech-synthesis prompt classifier and
# return 400 INVALID_ARGUMENT.

# Repeated verbatim for every module/chunk to reduce tonal drift between calls.
GLOBAL_PERFORMANCE_INSTRUCTIONS = (
    "This is one continuous Daily Office church service recorded in the same "
    "quiet room. Keep the voice identity, American English accent, tone, "
    "energy, volume, and steady conversational pace consistent across all "
    "segments: calm, warm, natural, and reverent, never like an announcer or "
    "actor. Each speaker is exactly one solo person speaking. Never sing, "
    "chant, harmonize, layer voices, double a voice, create a chorus, imitate "
    "a crowd, or add music or sound effects. Pause only at natural sentence "
    'endings and speaker changes. Pronounce Amen as "Ahh-men" (open "ah" as '
    "in father). Fully finish every final word and syllable without fading "
    "or cutting it off. Speak only the words of the provided text exactly as "
    "written, then stop. Never continue past the end of the text, and never "
    "add, improvise, or recite any other sentences, verses, or passages from "
    "memory, even if the text looks like an introduction or seems incomplete."
)

ROLE_PERFORMANCE_INSTRUCTIONS = {
    "leader": (
        "The Leader is one consistent solo officiant: calm, warm, clear, and "
        "conversational, guiding the prayer without theatrical emphasis."
    ),
    "congregation": (
        "The Congregation is voiced by one single solo respondent, not a "
        "crowd: a single person speaking each response clearly, steadily, and "
        "naturally at the same volume and pace as the Leader. Do not sing, "
        "chant, or use multiple or layered voices."
    ),
    "reader": (
        "The Reader is one consistent solo scripture reader: clear, measured, "
        "natural, and continuous, with a gentle storytelling sense but no "
        "dramatic character acting and no unnecessary pauses."
    ),
}


def gemini_model():
    return getattr(settings, "GEMINI_TTS_MODEL", None) or "gemini-3.1-flash-tts-preview"


def gemini_temperature():
    """Lower temperature => less pitch/prosody drift between independent TTS calls.

    Temperature does not change the spoken words, only voice style/prosody/register.
    Each chunk is a separate call with no cross-call audio conditioning, so a lower
    value keeps the same speaker's register more consistent from line to line. We
    default to 0.4; very low values can occasionally fail generation, which the
    synthesizer's retry loop absorbs.
    """
    value = getattr(settings, "GEMINI_TTS_TEMPERATURE", None)
    if value in (None, ""):
        return 0.4
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.4


_client_lock = threading.Lock()
_client_cache: dict[str, object] = {}


def _genai_client():
    from google import genai

    # Pass the key explicitly. When api_key is supplied, google-genai uses it and
    # never falls back to GOOGLE_API_KEY (this project's Custom Search key), so we
    # don't need to mutate os.environ — which was not thread-safe under the
    # parallel synthesis workers and could briefly hide the key from other code.
    api_key = (getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    # Reuse one client per key: genai.Client is safe to share across threads and
    # avoids re-initializing (and re-reading credentials) for every chunk.
    with _client_lock:
        client = _client_cache.get(api_key)
        if client is None:
            client = genai.Client(api_key=api_key)
            _client_cache[api_key] = client
        return client


def _dialogue_turns(items):
    """Merge adjacent lines spoken by the same role into one natural turn."""
    turns = []
    for item in items:
        role = item["role"]
        if turns and turns[-1]["role"] == role:
            turns[-1]["text"] = f"{turns[-1]['text']} {item['text']}"
        else:
            turns.append({"role": role, "text": item["text"]})
    return turns


def _segment_transcript(items):
    """Speaker-labeled transcript; also the sole basis for the cache key."""
    return "\n".join(f"{ROLE_SPEAKERS.get(turn['role'], 'Reader')}: {turn['text']}" for turn in _dialogue_turns(items))


def _segment_cache_key(transcript):
    # Uniqueness is by the text of the segment only (not voice or model), so
    # voice tweaks don't invalidate the whole cache.
    return generate_uuid_from_string(transcript)


def _office_reader_voice(modules):
    """Deterministically pick one reader voice for an entire office.

    Derived from the office content so the same office always sounds the same
    (even across separate processes / cache misses), while different offices
    still get some variety across the reader voice pool.
    """
    hasher = hashlib.sha256()
    for module in modules or []:
        hasher.update((module.get("name") or "").encode("utf-8"))
        for line in module.get("lines", []) or []:
            hasher.update(str(line.get("id") or "").encode("utf-8"))
            hasher.update(str(line.get("content") or "").encode("utf-8"))
    index = int.from_bytes(hasher.digest()[:8], "big") % len(READER_VOICES)
    return READER_VOICES[index]


def _voices_for_generation(roles):
    voices = {role: ROLE_VOICES[role] for role in roles}
    if "reader" in voices:
        # One voice for the whole office (set in build_gemini_audio); fall back to
        # a random choice only when called outside an office build.
        voices["reader"] = _reader_voice.get() or random.choice(READER_VOICES)
    return voices


def _speech_config(roles, voices):
    from google.genai import types

    if len(roles) > 1:
        speaker_voice_configs = [
            types.SpeakerVoiceConfig(
                speaker=ROLE_SPEAKERS[role],
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voices[role])
                ),
            )
            for role in roles
        ]
        return types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(speaker_voice_configs=speaker_voice_configs)
        )
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voices[roles[0]]))
    )


TRANSCRIPT_BOUNDARY_INSTRUCTIONS = (
    "Speak only the transcript between BEGIN_TRANSCRIPT and END_TRANSCRIPT. Do not "
    "read, repeat, continue, explain, translate, or improvise anything outside those "
    "markers, do not say the marker words themselves, and stop immediately after the "
    "last word of the transcript."
)


def _build_prompt(items, roles):
    notes = " ".join(ROLE_PERFORMANCE_INSTRUCTIONS[role] for role in roles)
    style = f"Style: {GLOBAL_PERFORMANCE_INSTRUCTIONS} {notes}"
    if len(roles) > 1:
        speakers = " and ".join(ROLE_SPEAKERS[role] for role in roles)
        header = f"TTS the following Daily Office dialogue between {speakers}."
        transcript = _segment_transcript(items)
    else:
        header = f"TTS the following Daily Office text spoken by the {ROLE_SPEAKERS[roles[0]]}."
        transcript = " ".join(item["text"] for item in items)
    return (
        f"{header}\n\n{style}\n\n{TRANSCRIPT_BOUNDARY_INSTRUCTIONS}\n\n"
        f"BEGIN_TRANSCRIPT\n{transcript}\nEND_TRANSCRIPT"
    )


def _check_duration_plausible(pcm, spoken_chars):
    seconds = len(pcm) / (2 * PCM_SAMPLE_RATE)
    max_seconds = MAX_SECONDS_BASE + spoken_chars * MAX_SECONDS_PER_CHAR
    min_seconds = spoken_chars * MIN_SECONDS_PER_CHAR
    if seconds > max_seconds:
        raise RuntimeError(
            f"Gemini TTS audio is implausibly long ({seconds:.1f}s for {spoken_chars} chars, "
            f"max {max_seconds:.1f}s); the model likely recited beyond the provided text"
        )
    if seconds < min_seconds:
        raise RuntimeError(
            f"Gemini TTS audio is implausibly short ({seconds:.1f}s for {spoken_chars} chars, "
            f"min {min_seconds:.1f}s); the clip is likely truncated"
        )


def _max_output_tokens(spoken_chars):
    max_seconds = MAX_SECONDS_BASE + spoken_chars * MAX_SECONDS_PER_CHAR
    return int(max_seconds * AUDIO_TOKENS_PER_SECOND)


def _finish_reason_name(candidate):
    """finish_reason may be an enum, a string, or None; return a plain string."""
    finish_reason = getattr(candidate, "finish_reason", None)
    name = getattr(finish_reason, "name", None)
    if isinstance(name, str):
        return name
    return str(finish_reason) if finish_reason is not None else ""


def _extract_pcm(response):
    """Pull raw PCM out of a generate_content response, or raise a clear error.

    When a runaway recitation hits max_output_tokens the API returns a
    candidate with finish_reason=MAX_TOKENS and no parts at all, so every
    attribute in the chain can be None. When it hits the cap after emitting some
    audio, we get partial (truncated) PCM plus finish_reason=MAX_TOKENS; reject
    that too so a chopped-off clip never gets cached.
    """
    candidates = getattr(response, "candidates", None) or []
    candidate = candidates[0] if candidates else None
    content = getattr(candidate, "content", None)
    parts = getattr(content, "parts", None) or []
    inline_data = getattr(parts[0], "inline_data", None) if parts else None
    pcm = getattr(inline_data, "data", None)
    finish_reason = _finish_reason_name(candidate)
    if not pcm:
        raise RuntimeError(
            f"Gemini TTS returned no audio (finish_reason={finish_reason or None}); "
            "if MAX_TOKENS, the model recited beyond the provided text and hit the output cap"
        )
    if finish_reason == "MAX_TOKENS":
        raise RuntimeError(
            "Gemini TTS hit the output token cap (finish_reason=MAX_TOKENS); the audio is "
            "truncated or the model recited beyond the provided text"
        )
    return pcm


def build_generate_content_config(roles, voices, spoken_chars):
    """Identical request config for real-time and batch synthesis, so a clip
    sounds the same however it was produced."""
    from google.genai import types

    return types.GenerateContentConfig(
        temperature=gemini_temperature(),
        response_modalities=["AUDIO"],
        speech_config=_speech_config(roles, voices),
        max_output_tokens=_max_output_tokens(spoken_chars),
    )


def encode_pcm_to_mp3(pcm, file_path):
    """Encode raw 24 kHz mono 16-bit PCM to an MP3 at file_path, atomically.

    Writing to a temp file and os.replace()-ing into place means a crash or a
    concurrent reader can never see a truncated cached clip. Shared by the
    real-time and batch paths.
    """
    pcm_fd, pcm_path = tempfile.mkstemp(suffix=".pcm")
    temp_mp3 = f"{file_path}.{os.getpid()}.{threading.get_ident()}.tmp.mp3"
    try:
        with os.fdopen(pcm_fd, "wb") as out:
            out.write(pcm)
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "s16le",
                "-ar",
                str(PCM_SAMPLE_RATE),
                "-ac",
                "1",
                "-i",
                pcm_path,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "128k",
                temp_mp3,
            ]
        )
        if not (os.path.isfile(temp_mp3) and os.path.getsize(temp_mp3) > 0):
            raise RuntimeError("Gemini TTS encoding produced an empty MP3 file")
        os.replace(temp_mp3, file_path)
    finally:
        if os.path.exists(pcm_path):
            os.unlink(pcm_path)
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)


def _synthesize_to_mp3(prompt, roles, voices, file_path, spoken_chars):
    client = _genai_client()
    last_error = None
    for attempt in range(1, MAX_SYNTHESIS_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=gemini_model(),
                contents=prompt,
                config=build_generate_content_config(roles, voices, spoken_chars),
            )
            pcm = _extract_pcm(response)
            _check_duration_plausible(pcm, spoken_chars)
            break
        except Exception as exc:  # occasional 500s / 404s / text-token returns; retry
            last_error = exc
            logger.warning(
                "Gemini TTS attempt %s/%s failed (text=%r): %s",
                attempt,
                MAX_SYNTHESIS_ATTEMPTS,
                prompt[-120:],
                exc,
            )
            if attempt == MAX_SYNTHESIS_ATTEMPTS:
                raise
            # Exponential backoff with jitter so parallel workers hitting a
            # transient 429/500 don't retry in lockstep.
            time.sleep(1.5 * attempt + random.uniform(0, 0.75))
    else:  # pragma: no cover
        raise last_error

    encode_pcm_to_mp3(pcm, file_path)


def generate_gemini_dialogue_clip(items):
    """Synthesize one segment (possibly multi-speaker) as a single Gemini TTS call."""
    items = [item for item in items if item.get("text") and item.get("role") in ROLE_VOICES]
    if not items:
        return None

    roles = []
    for item in items:
        if item["role"] not in roles:
            roles.append(item["role"])

    transcript = _segment_transcript(items)
    cache_key = _segment_cache_key(transcript)
    filename = f"{cache_key}.mp3"
    clips_dir = _ensure_subdir(CLIPS_SUBDIR)
    file_path = os.path.join(clips_dir, filename)
    media_path = _media_url(CLIPS_SUBDIR, filename)
    url = _absolute_url(media_path)
    line_segments = [{"id": item["line_id"] or cache_key, "chars": max(len(item["text"]), 1)} for item in items]

    # In-memory per-key lock: parallel workers building overlapping offices
    # wait for the first synthesis of a segment instead of duplicating it.
    with clip_generation_lock(cache_key):
        exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        collector = _batch_collector.get()
        if collector is not None:
            # Collection pass for a batch pre-warm: record cache misses for later
            # asynchronous synthesis and never assemble (return None for every
            # segment, so build_v2_audio produces no partial/poisoned track).
            if not exists:
                collector.record(
                    BatchChunk(
                        cache_key=cache_key,
                        prompt=_build_prompt(items, roles),
                        file_path=file_path,
                        spoken_chars=sum(len(item["text"]) for item in items),
                        roles=list(roles),
                        voices=_voices_for_generation(roles),
                    )
                )
            return None
        if not exists:
            prompt = _build_prompt(items, roles)
            voices = _voices_for_generation(roles)
            spoken_chars = sum(len(item["text"]) for item in items)
            try:
                _synthesize_to_mp3(prompt, roles, voices, file_path, spoken_chars)
            except Exception as exc:
                if os.path.exists(file_path):
                    os.remove(file_path)
                logger.exception(
                    "Gemini TTS failed for roles=%s model=%s: %s",
                    roles,
                    gemini_model(),
                    exc,
                )
                raise

    return ClipSpec(
        line_id=items[0]["line_id"] or cache_key,
        module_name="",
        role=items[0]["role"],
        end_role=items[-1]["role"],
        kind="spoken",
        text=transcript,
        file_path=file_path,
        media_path=media_path,
        url=url,
        duration=audio_duration(file_path),
        line_segments=line_segments,
    )


def build_gemini_audio(modules):
    reader_voice = _office_reader_voice(modules)
    with audio_provider(
        subdir=AUDIO_GEMINI_SUBDIR,
        synthesize_chunk=generate_gemini_dialogue_clip,
        chunk_role_limit=2,
        chunk_char_limit=GEMINI_MAX_CHUNK_CHARS,
    ):
        # Set after entering audio_provider so v2._run_spoken_tasks' copy_context()
        # captures a fully-configured context for each parallel worker.
        token = _reader_voice.set(reader_voice)
        try:
            return build_v2_audio(modules)
        finally:
            _reader_voice.reset(token)

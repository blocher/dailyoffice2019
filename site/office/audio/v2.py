"""V2 office audio: gpt-4o-mini-tts, new voices, intentional gaps, re-encode concat.

Files are stored under MEDIA_ROOT/audio_v2/ and never touch legacy MEDIA_ROOT clips.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.sites.models import Site
from mutagen import File as MutagenFile

from office.utils import generate_uuid_from_string

logger = logging.getLogger(__name__)

# Allow alternate providers (e.g. Gemini) to reuse batching/assembly with another
# media subdirectory and synthesize function.
_audio_subdir: ContextVar[str] = ContextVar("office_audio_subdir", default="audio_v2")
_synthesize_fn: ContextVar[object | None] = ContextVar("office_audio_synthesize", default=None)
# Chunk-level hook: receives a list of {"line_id", "text", "role"} turns so a
# provider can synthesize multi-speaker dialogue in a single request.
_synthesize_chunk_fn: ContextVar[object | None] = ContextVar("office_audio_synthesize_chunk", default=None)
# How many distinct roles may share one TTS chunk (multi-speaker providers use 2).
_chunk_role_limit: ContextVar[int] = ContextVar("office_audio_chunk_role_limit", default=1)

SPOKEN_LINE_TYPES = {
    "reader",
    "leader",
    "congregation",
    "leader_dialogue",
    "congregation_dialogue",
}
NAVIGABLE_LINE_TYPES = SPOKEN_LINE_TYPES | {"html"}

ROLE_VOICES = {
    "leader": "cedar",
    "leader_dialogue": "cedar",
    "congregation": "marin",
    "congregation_dialogue": "marin",
    "reader": "cedar",
    "html": "cedar",
}

ROLE_SPEEDS = {
    "leader": 1.0,
    "leader_dialogue": 1.0,
    "congregation": 1.0,
    "congregation_dialogue": 1.0,
    "reader": 1.0,
    "html": 1.0,
}

OPENAI_MODEL = "gpt-4o-mini-tts"

# Shared pronunciation / finish rules for every role.
SHARED_SPEECH_RULES = (
    'Always pronounce "Amen" in the Latin liturgical way: "Ahh-men" '
    '(open "ah" as in father, then "men") — never "Ay-men" or "A-men". '
    "Fully finish the last word of every line — especially Amen, Alleluia, and "
    "Lord — with no trailing cut-off or fade on the final syllable."
)

ROLE_INSTRUCTIONS = {
    "leader": (
        "Casual, natural liturgical reading — like a calm person speaking clearly, "
        "not a formal announcer. Keep a steady conversational flow; do not pause "
        "mid-sentence or after every phrase. Only take a short breath at periods "
        "or natural sentence ends. Warm and reverent without being stiff. "
        f"{SHARED_SPEECH_RULES}"
    ),
    "leader_dialogue": (
        "Casual, natural liturgical reading — like a calm person speaking clearly, "
        "not a formal announcer. Keep a steady conversational flow; do not pause "
        "mid-sentence or after every phrase. Only take a short breath at periods "
        "or natural sentence ends. Warm and reverent without being stiff. "
        f"{SHARED_SPEECH_RULES}"
    ),
    "reader": (
        "Casual, natural scripture reading — clear and continuous, not overly "
        "dramatic. Avoid mid-sentence pauses; keep verses flowing. Short breath "
        "only at sentence ends. "
        f"{SHARED_SPEECH_RULES}"
    ),
    "html": (
        "Casual, natural scripture reading — clear and continuous, not overly "
        "dramatic. Avoid mid-sentence pauses; keep verses flowing. Short breath "
        "only at sentence ends. "
        f"{SHARED_SPEECH_RULES}"
    ),
    "congregation": (
        "Speak as the gathered people: clear, steady, and complete. Hold the "
        "final syllable of each response so words like Amen and Alleluia are "
        "never chopped off. Do not rush the ending. "
        f"{SHARED_SPEECH_RULES}"
    ),
    "congregation_dialogue": (
        "Speak as the gathered people: clear, steady, and complete. Hold the "
        "final syllable of each response so words like Amen and Alleluia are "
        "never chopped off. Do not rush the ending. "
        f"{SHARED_SPEECH_RULES}"
    ),
}

# Same-speaker lines are batched into one TTS clip, so no gap between them.
SPEAKER_CHANGE_GAP_MS = 280
SAME_SPEAKER_GAP_MS = 0
MODULE_BOUNDARY_GAP_MS = 600
SILENCE_RUBRIC_SECONDS = 4.0
TARGET_LOUDNESS_LUFS = -18.0
MAX_SPOKEN_CHUNK_CHARS = 1500
JOIN_FADE_IN_SECONDS = 0.015
TRAILING_PAD_SECONDS = 0.18
ASSEMBLY_CACHE_VERSION = "v4-trim-trailing-silence"
# Uncached chunks are synthesized concurrently (bounded to stay under TTS rate limits).
PARALLEL_TTS_WORKERS = 4

# Max characters per synthesized chunk. Providers can lower this (e.g. Gemini)
# so long passages are split into smaller requests, which both reduces the odds
# of a runaway recitation and makes any rejected clip cheaper to regenerate.
_chunk_char_limit: ContextVar[int] = ContextVar("office_audio_chunk_char_limit", default=MAX_SPOKEN_CHUNK_CHARS)

AUDIO_V2_SUBDIR = "audio_v2"
CLIPS_SUBDIR = "clips"
FULL_SUBDIR = "full"
SILENCE_SUBDIR = "silence"


@dataclass
class ClipSpec:
    line_id: str
    module_name: str
    role: str
    kind: str  # spoken | silence
    text: str = ""
    seconds: float = 0.0
    file_path: str = ""
    media_path: str = ""
    url: str = ""
    duration: float = 0.0
    # For multi-line TTS chunks: [{"id": line_id, "chars": n}, ...]
    line_segments: list = field(default_factory=list)
    # Role of the final speaker in a multi-speaker chunk (for gap calculation).
    end_role: str = ""


def _site_base_url():
    """Prefer SITE_ADDRESS (env) so local/prod URLs match the API the app calls."""
    base = getattr(settings, "SITE_ADDRESS", None) or ""
    base = str(base).rstrip("/")
    if base:
        return base
    domain = Site.objects.get_current().domain
    if domain.startswith("http://") or domain.startswith("https://"):
        return domain.rstrip("/")
    return f"https://{domain}"


def _absolute_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{_site_base_url()}{path}"


def get_audio_subdir():
    return _audio_subdir.get() or AUDIO_V2_SUBDIR


def _provider_root():
    path = os.path.join(settings.MEDIA_ROOT, get_audio_subdir())
    os.makedirs(path, exist_ok=True)
    return path


def _ensure_subdir(*parts):
    path = os.path.join(_provider_root(), *parts)
    os.makedirs(path, exist_ok=True)
    return path


def _media_url(*parts):
    return settings.MEDIA_URL + "/".join([get_audio_subdir(), *parts])


@contextmanager
def audio_provider(*, subdir, synthesize=None, synthesize_chunk=None, chunk_role_limit=1, chunk_char_limit=None):
    """Temporarily use another TTS backend + media subdirectory."""
    subdir_token = _audio_subdir.set(subdir)
    synth_token = _synthesize_fn.set(synthesize)
    chunk_token = _synthesize_chunk_fn.set(synthesize_chunk)
    limit_token = _chunk_role_limit.set(max(int(chunk_role_limit or 1), 1))
    char_limit = MAX_SPOKEN_CHUNK_CHARS if chunk_char_limit is None else max(int(chunk_char_limit), 1)
    char_token = _chunk_char_limit.set(char_limit)
    try:
        yield
    finally:
        _audio_subdir.reset(subdir_token)
        _synthesize_fn.reset(synth_token)
        _synthesize_chunk_fn.reset(chunk_token)
        _chunk_role_limit.reset(limit_token)
        _chunk_char_limit.reset(char_token)


def _max_chunk_chars():
    try:
        return max(int(_chunk_char_limit.get()), 1)
    except (TypeError, ValueError):
        return MAX_SPOKEN_CHUNK_CHARS


# Per-cache-key locks so concurrent requests don't synthesize the same clip
# twice. Plain in-memory threading locks: they exist only inside this process,
# so a crashed request/worker can never leave a stale lock behind.
_generation_locks: dict[str, threading.Lock] = {}
_generation_locks_guard = threading.Lock()


@contextmanager
def clip_generation_lock(key):
    with _generation_locks_guard:
        lock = _generation_locks.setdefault(str(key), threading.Lock())
    with lock:
        yield


def normalize_audio_text(text):
    text = BeautifulSoup(str(text or ""), "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("LORD", "Lord").replace("Lᴏʀᴅ", "Lord")
    # Nudge TTS toward Latin liturgical "Ahh-men" (display text is unchanged upstream).
    text = re.sub(r"\bAmen\b", "Ahhmen", text, flags=re.IGNORECASE)
    return text


def instructions_for_role(role):
    return ROLE_INSTRUCTIONS.get(role) or ROLE_INSTRUCTIONS["reader"]


def voice_for_line_type(line_type):
    line_type = (line_type or "").lower()
    if "leader" in line_type:
        return ROLE_VOICES["leader"]
    if "congregation" in line_type:
        return ROLE_VOICES["congregation"]
    if line_type in ("html", "reader") or "reader" in line_type:
        return ROLE_VOICES["reader"]
    return None


def role_for_line_type(line_type):
    """Canonical role: dialogue variants collapse into their base role so all
    providers (and the multi-speaker role limit) see leader/congregation/reader."""
    line_type = (line_type or "").lower()
    if "leader" in line_type:
        return "leader"
    if "congregation" in line_type:
        return "congregation"
    return "reader"


def is_silence_rubric(line):
    if (line.get("line_type") or "").lower() != "rubric":
        return False
    content = (line.get("content") or "").lower()
    return "silence" in content or "silent" in content


def audio_duration(file_path, fallback=0.0):
    try:
        return float(MutagenFile(file_path).info.length)
    except Exception:
        return float(fallback)


def _run_ffmpeg(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")


def _clip_cache_key(role, voice, text, speed):
    instructions = instructions_for_role(role)
    payload = "|".join(
        [
            "v2",
            OPENAI_MODEL,
            role,
            voice,
            f"{speed:.3f}",
            hashlib.sha256(instructions.encode("utf-8")).hexdigest()[:16],
            text,
        ]
    )
    return generate_uuid_from_string(payload)


def generate_spoken_clip(role, text, line_id=None):
    custom = _synthesize_fn.get()
    if custom is not None:
        return custom(role, text, line_id=line_id)

    voice = ROLE_VOICES.get(role) or voice_for_line_type(role)
    if not voice or not text:
        return None
    speed = float(ROLE_SPEEDS.get(role, 1.0))
    cache_key = _clip_cache_key(role, voice, text, speed)
    filename = f"{cache_key}.mp3"
    clips_dir = _ensure_subdir(CLIPS_SUBDIR)
    file_path = os.path.join(clips_dir, filename)
    media_path = _media_url(CLIPS_SUBDIR, filename)
    url = _absolute_url(media_path)

    with clip_generation_lock(cache_key):
        if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
            return ClipSpec(
                line_id=line_id or cache_key,
                module_name="",
                role=role,
                kind="spoken",
                text=text,
                file_path=file_path,
                media_path=media_path,
                url=url,
                duration=audio_duration(file_path),
                line_segments=[{"id": line_id or cache_key, "chars": max(len(text), 1)}],
            )

        temp_path = f"{file_path}.{os.getpid()}.{threading.get_ident()}.tmp.mp3"
        try:
            from openai import OpenAI

            client = OpenAI()
            response = client.audio.speech.create(
                model=OPENAI_MODEL,
                voice=voice,
                input=text,
                instructions=instructions_for_role(role),
                speed=speed,
            )
            response.stream_to_file(temp_path)
            os.replace(temp_path, file_path)
        except Exception as exc:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.exception(
                "OpenAI TTS failed for role=%s voice=%s model=%s: %s",
                role,
                voice,
                OPENAI_MODEL,
                exc,
            )
            raise

    return ClipSpec(
        line_id=line_id or cache_key,
        module_name="",
        role=role,
        kind="spoken",
        text=text,
        file_path=file_path,
        media_path=media_path,
        url=url,
        duration=audio_duration(file_path),
        line_segments=[{"id": line_id or cache_key, "chars": max(len(text), 1)}],
    )


def generate_spoken_chunk(role, items):
    """Generate one TTS clip for consecutive lines so paragraphs flow."""
    items = [item for item in items if item.get("text")]
    if not items:
        return None
    for item in items:
        item.setdefault("role", role)

    custom_chunk = _synthesize_chunk_fn.get()
    if custom_chunk is not None:
        return custom_chunk(items)

    if len(items) == 1:
        clip = generate_spoken_clip(role, items[0]["text"], line_id=items[0]["line_id"])
        return clip

    combined = " ".join(item["text"] for item in items)
    clip = generate_spoken_clip(role, combined, line_id=items[0]["line_id"])
    if not clip:
        return None
    clip.line_segments = [{"id": item["line_id"], "chars": max(len(item["text"]), 1)} for item in items]
    return clip


def generate_silence_clip(seconds):
    seconds = max(0.1, min(float(seconds), 300.0))
    key = generate_uuid_from_string(f"v2-silence-{seconds:.3f}")
    filename = f"{key}.mp3"
    silence_dir = _ensure_subdir(SILENCE_SUBDIR)
    file_path = os.path.join(silence_dir, filename)
    media_path = _media_url(SILENCE_SUBDIR, filename)
    url = _absolute_url(media_path)
    if not (os.path.isfile(file_path) and os.path.getsize(file_path) > 0):
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                f"{seconds:.3f}",
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                file_path,
            ]
        )
    return ClipSpec(
        line_id=key,
        module_name="",
        role="silence",
        kind="silence",
        seconds=seconds,
        file_path=file_path,
        media_path=media_path,
        url=url,
        duration=audio_duration(file_path, fallback=seconds),
    )


def _normalize_to_wav(input_path, output_path, kind):
    if kind == "silence":
        filters = "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
    else:
        # Trim leading AND trailing hush so the only pauses between clips come
        # from our deterministic gap constants, not from whatever variable
        # silence the TTS model appended (that was the source of the long,
        # "arbitrary" pauses between sentences and modules). Trailing silence is
        # removed by reversing, stripping the new leading silence, and reversing
        # back. The -50dB threshold only strips near-digital-silence, so a held
        # final syllable (Amen/Alleluia) stays intact — no end fade. A fixed pad
        # is re-added afterward so joins never clip the last syllable.
        trim = "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB"
        filters = (
            f"{trim},"
            f"areverse,{trim},areverse,"
            f"loudnorm=I={TARGET_LOUDNESS_LUFS}:LRA=11:TP=-1.5,"
            f"afade=t=in:st=0:d={JOIN_FADE_IN_SECONDS},"
            f"apad=pad_dur={TRAILING_PAD_SECONDS},"
            "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
        )
    _run_ffmpeg(["ffmpeg", "-y", "-i", input_path, "-af", filters, output_path])


def _gap_ms(previous_role, current_role, module_changed):
    if module_changed:
        return MODULE_BOUNDARY_GAP_MS
    if not previous_role:
        return 0
    if previous_role == "silence" or current_role == "silence":
        return 0
    if previous_role != current_role:
        return SPEAKER_CHANGE_GAP_MS
    return SAME_SPEAKER_GAP_MS


def assemble_full_track(clips):
    """Normalize, insert gaps, re-encode. Returns (file_url, media_path, module_tracks, line_tracks)."""
    if not clips:
        return "", "", [], []

    cache_parts = [
        ASSEMBLY_CACHE_VERSION,
        str(SPEAKER_CHANGE_GAP_MS),
        str(SAME_SPEAKER_GAP_MS),
        str(MODULE_BOUNDARY_GAP_MS),
        str(TRAILING_PAD_SECONDS),
    ]
    for clip in clips:
        end_role = getattr(clip, "end_role", "")
        if not isinstance(end_role, str):
            end_role = ""
        cache_parts.extend(
            [
                clip.file_path,
                clip.module_name,
                clip.role,
                end_role,
                clip.kind,
            ]
        )
    audio_id = generate_uuid_from_string("|".join(cache_parts))
    filename = f"{audio_id}.mp3"
    full_dir = _ensure_subdir(FULL_SUBDIR)
    file_path = os.path.join(full_dir, filename)
    metadata_path = os.path.join(full_dir, f"{audio_id}.json")
    media_path = _media_url(FULL_SUBDIR, filename)
    file_url = _absolute_url(f"/api/v1/audio_track/{get_audio_subdir()}/{FULL_SUBDIR}/{filename}")

    if (
        os.path.isfile(file_path)
        and os.path.getsize(file_path) > 0
        and os.path.isfile(metadata_path)
        and os.path.getsize(metadata_path) > 0
    ):
        try:
            with open(metadata_path, encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
            return file_url, media_path, metadata["module_tracks"], metadata["line_tracks"]
        except (OSError, KeyError, TypeError, ValueError):
            logger.warning("Rebuilding invalid office audio timeline metadata: %s", metadata_path)

    temp_dir = tempfile.mkdtemp(prefix="office-audio-v2-")
    try:
        normalized_clips = []
        for index, clip in enumerate(clips):
            wav_path = os.path.join(temp_dir, f"clip_{index:04d}.wav")
            try:
                _normalize_to_wav(clip.file_path, wav_path, clip.kind)
            except Exception:
                # Evict corrupt/truncated cached clips so the next request
                # regenerates them instead of failing on the same file forever.
                logger.exception("Removing unreadable cached audio clip: %s", clip.file_path)
                try:
                    os.remove(clip.file_path)
                except OSError:
                    pass
                raise
            fallback = float(clip.duration or 0)
            if clip.kind == "spoken":
                fallback += TRAILING_PAD_SECONDS
            normalized_clips.append((clip, wav_path, audio_duration(wav_path, fallback=fallback)))

        module_tracks = []
        line_tracks = []
        timeline_pieces = []
        start_time = 0.0
        current_module = ""
        previous_role = ""
        previous_module = ""

        # Derive timestamps from the normalized WAVs that are actually concatenated.
        # This accounts for leading-silence trimming and prevents cumulative seek drift.
        for clip, wav_path, clip_duration in normalized_clips:
            module_changed = bool(previous_module) and clip.module_name != previous_module
            gap_ms = _gap_ms(previous_role, clip.role, module_changed)
            if gap_ms > 0:
                gap_seconds = gap_ms / 1000.0
                timeline_pieces.append(("gap", gap_seconds, None))
                start_time += gap_seconds
            if clip.module_name != current_module:
                current_module = clip.module_name
                module_tracks.append({"name": clip.module_name, "start_time": start_time})
            if clip.kind == "spoken":
                segments = list(getattr(clip, "line_segments", None) or [])
                if not segments:
                    segments = [{"id": clip.line_id, "chars": max(len(clip.text or ""), 1)}]
                total_chars = sum(max(int(seg.get("chars") or 0), 1) for seg in segments) or 1
                speech_duration = max(clip_duration - TRAILING_PAD_SECONDS, 0)
                offset = 0.0
                for seg in segments:
                    frac = max(int(seg.get("chars") or 0), 1) / total_chars
                    seg_duration = speech_duration * frac
                    line_tracks.append(
                        {
                            "id": seg.get("id") or clip.line_id,
                            "start_time": start_time + offset,
                            "duration": seg_duration,
                        }
                    )
                    offset += seg_duration
            timeline_pieces.append(("clip", clip_duration, wav_path))
            start_time += clip_duration
            end_role = getattr(clip, "end_role", "")
            previous_role = end_role if isinstance(end_role, str) and end_role else clip.role
            previous_module = clip.module_name

        wav_files = []
        gap_cache = {}
        for piece_kind, duration, wav_path in timeline_pieces:
            if piece_kind == "gap":
                key = f"{duration:.3f}"
                if key not in gap_cache:
                    gap_path = os.path.join(temp_dir, f"gap_{key}.wav")
                    _run_ffmpeg(
                        [
                            "ffmpeg",
                            "-y",
                            "-f",
                            "lavfi",
                            "-i",
                            "anullsrc=r=44100:cl=mono",
                            "-t",
                            f"{duration:.3f}",
                            "-acodec",
                            "pcm_s16le",
                            gap_path,
                        ]
                    )
                    gap_cache[key] = gap_path
                wav_files.append(gap_cache[key])
                continue

            wav_files.append(wav_path)

        list_path = os.path.join(temp_dir, "files.txt")
        with open(list_path, "w", encoding="utf-8") as list_file:
            for wav_file in wav_files:
                list_file.write(f"file '{os.path.abspath(wav_file)}'\n")

        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path,
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                file_path,
            ]
        )
        metadata_temp_path = os.path.join(temp_dir, "timeline.json")
        with open(metadata_temp_path, "w", encoding="utf-8") as metadata_file:
            json.dump({"module_tracks": module_tracks, "line_tracks": line_tracks}, metadata_file)
        os.replace(metadata_temp_path, metadata_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return file_url, media_path, module_tracks, line_tracks


def _html_chunk_item_lists(content, base_id):
    """Split an HTML block into reader chunk item-lists (no synthesis)."""
    items = []
    sentences = re.split(r"(?<=[.!?])", str(content))
    for sentence in sentences:
        soup = BeautifulSoup(sentence, "html.parser")
        plain_text = soup.get_text()
        text_without_verses = re.sub(r"(\b\d+\b\s)", "", plain_text)
        text = normalize_audio_text(text_without_verses)
        if not text:
            continue
        anchor = soup.find(attrs={"data-line-id": True})
        # DOM identity must come from rendered content, never a TTS cache key.
        line_id = anchor.get("data-line-id") if anchor else base_id
        items.append({"line_id": line_id, "text": text, "role": "reader"})

    chunk_lists = []
    chunk = []
    chunk_chars = 0
    char_limit = _max_chunk_chars()
    for item in items:
        item_len = len(item["text"])
        if chunk and chunk_chars + item_len > char_limit:
            chunk_lists.append(chunk)
            chunk = []
            chunk_chars = 0
        chunk.append(item)
        chunk_chars += item_len
    if chunk:
        chunk_lists.append(chunk)
    return chunk_lists


def _clips_from_html(content, base_id, module_name):
    """One continuous TTS reading per HTML block; keep sentence-level line ids for sync."""
    clips = []
    for chunk in _html_chunk_item_lists(content, base_id):
        clip = generate_spoken_chunk("reader", chunk)
        if clip:
            clip.module_name = module_name
            clips.append(clip)
    return clips


def _headings(modules):
    headings = []
    for module in modules:
        lines = module.get("lines", [])
        for index, line in enumerate(lines):
            if (line.get("line_type") or "").lower() != "heading":
                continue
            look_ahead = None
            for candidate in lines[index + 1 :]:
                candidate_type = (candidate.get("line_type") or "").lower()
                if candidate_type in NAVIGABLE_LINE_TYPES and "<iframe" not in str(candidate.get("content", "")):
                    look_ahead = candidate
                    break
            if look_ahead:
                headings.append({"heading": line.get("content"), "next_id": look_ahead.get("id")})
    return headings


def _generation_failed_result(headings, detail=None):
    message = (
        "Audio could not be generated right now. " "Please try again later, or contact support if this continues."
    )
    if detail:
        logger.error("Office audio v2 generation failed: %s", detail)
    return {
        "tracks": [],
        "headings": headings,
        "single_track": [],
        "available": False,
        "unavailable_reason": "generation_failed",
        "unavailable_message": message,
    }


def _collect_audio_tasks(modules):
    """First pass: plan every clip (spoken chunks and silences) in document order."""
    tasks = []

    for module in modules:
        module_name = module.get("name") or "Module"
        spoken_buffer = []

        def flush_spoken():
            if not spoken_buffer:
                return
            tasks.append(
                {
                    "kind": "spoken",
                    "module_name": module_name,
                    "role": spoken_buffer[0]["role"],
                    "items": list(spoken_buffer),
                }
            )
            spoken_buffer.clear()

        for line in module.get("lines", []):
            line_type = (line.get("line_type") or "").lower()
            content = line.get("content")

            if is_silence_rubric(line):
                flush_spoken()
                tasks.append({"kind": "silence", "module_name": module_name, "line_id": line.get("id")})
                continue

            if line_type == "html":
                flush_spoken()
                if "<iframe" in str(content):
                    continue
                parts = str(line.get("id", "")).split("_")
                temp_id = "_".join([parts[0], parts[-1]]) if parts else None
                for chunk in _html_chunk_item_lists(content, temp_id):
                    tasks.append({"kind": "spoken", "module_name": module_name, "role": "reader", "items": chunk})
                continue

            if line_type not in SPOKEN_LINE_TYPES:
                flush_spoken()
                continue

            text = normalize_audio_text(content)
            if not text:
                continue
            role = role_for_line_type(line_type)
            item = {"line_id": line.get("id"), "text": text, "role": role}
            if spoken_buffer:
                roles = {entry["role"] for entry in spoken_buffer} | {role}
                too_many_roles = len(roles) > _chunk_role_limit.get()
                too_long = sum(len(entry["text"]) for entry in spoken_buffer) + len(text) > _max_chunk_chars()
                if too_many_roles or too_long:
                    flush_spoken()
            spoken_buffer.append(item)

        flush_spoken()

    return tasks


def _run_spoken_tasks(tasks):
    """Synthesize spoken chunks with bounded parallelism, preserving task order.

    Contexts are copied on the calling thread (one per task, since a Context
    cannot be entered concurrently) so provider hooks like the Gemini
    synthesize_chunk contextvar dispatch correctly inside worker threads.
    """
    spoken_tasks = [task for task in tasks if task["kind"] == "spoken"]
    jobs = [(task, contextvars.copy_context()) for task in spoken_tasks]

    if len(jobs) <= 1:
        results = [_run_spoken_task(task, ctx) for task, ctx in jobs]
    else:
        with ThreadPoolExecutor(max_workers=PARALLEL_TTS_WORKERS) as executor:
            futures = [executor.submit(_run_spoken_task, task, ctx) for task, ctx in jobs]
            results = [future.result() for future in futures]

    for task, (clip, error) in zip(spoken_tasks, results):
        task["clip"] = clip
        task["error"] = error


def _run_spoken_task(task, ctx):
    try:
        return ctx.run(generate_spoken_chunk, task["role"], task["items"]), None
    except Exception as exc:
        logger.exception("Spoken chunk generation failed for module=%s", task.get("module_name"))
        return None, exc


def build_v2_audio(modules):
    modules = [module for module in modules if module and module.get("lines")]
    headings = _headings(modules)

    tasks = _collect_audio_tasks(modules)
    _run_spoken_tasks(tasks)

    clips = []
    tracks = []
    spoken_count = 0
    generation_error = None

    for task in tasks:
        module_name = task["module_name"]

        if task["kind"] == "silence":
            silence = generate_silence_clip(SILENCE_RUBRIC_SECONDS)
            silence.module_name = module_name
            silence.line_id = task.get("line_id") or silence.line_id
            clips.append(silence)
            continue

        generation_error = generation_error or task.get("error")
        clip = task.get("clip")
        if not clip:
            continue
        clip.module_name = module_name
        clips.append(clip)
        spoken_count += 1
        for seg in clip.line_segments or [{"id": clip.line_id}]:
            tracks.append(
                {
                    "line_id": seg.get("id") or clip.line_id,
                    "module": module_name,
                    "url": clip.url,
                    "path": clip.media_path,
                }
            )

    if spoken_count == 0:
        return _generation_failed_result(headings, detail=generation_error or "no spoken clips generated")

    try:
        file_url, media_path, module_tracks, line_tracks = assemble_full_track(clips)
    except Exception as exc:
        # Never let an assembly failure (e.g. one corrupt cached clip) take
        # down the whole office response; report audio as unavailable instead.
        return _generation_failed_result(headings, detail=exc)
    return {
        "tracks": tracks,
        "headings": headings,
        "single_track": [file_url, media_path, module_tracks, line_tracks],
        "available": True,
    }

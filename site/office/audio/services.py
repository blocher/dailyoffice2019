import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from decimal import Decimal

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from mutagen.mp3 import MP3

from office.audio.providers import AudioProviderError, get_audio_provider
from office.models import (
    AudioCostRate,
    AudioGeneratedFile,
    AudioGenerationConfig,
    AudioGenerationEvent,
    AudioUsage,
    AudioVoice,
)


SPOKEN_LINE_TYPES = {
    "leader",
    "leader_dialogue",
    "congregation",
    "congregation_dialogue",
    "reader",
}
HTML_LINE_TYPE = "html"
SOUND_LINE_TYPE = "sound"
SILENCE_LINE_TYPE = "silence"
NAVIGABLE_LINE_TYPES = SPOKEN_LINE_TYPES | {HTML_LINE_TYPE}

OPENAI_DEFAULT_VOICES = {
    "leader": "onyx",
    "leader_dialogue": "onyx",
    "congregation": "ash",
    "congregation_dialogue": "ash",
    "reader": "echo",
}

DEFAULT_COST_RATES = {
    ("openai", "tts-1", AudioGeneratedFile.GenerationType.SPOKEN): (
        AudioCostRate.Unit.CHARACTER,
        Decimal("0.000015"),
    ),
}


@dataclass
class AudioItem:
    module_name: str
    line_id: str
    line_type: str
    role: str
    text: str
    kind: str = AudioGeneratedFile.GenerationType.SPOKEN
    seconds: Decimal | None = None
    selector_key: str = ""


@dataclass
class ArtifactResult:
    generated_file: AudioGeneratedFile
    file_path: str
    url: str
    media_path: str
    duration: Decimal
    line_segments: list[dict] = field(default_factory=list)
    kind: str = ""


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "pk"):
        return str(value.pk)
    return str(value)


def hash_payload(payload):
    encoded = json.dumps(payload, sort_keys=True, default=_json_default, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_line_type(line_type):
    return (line_type or "").strip().lower()


def normalize_audio_text(text):
    text = BeautifulSoup(str(text or ""), "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("LORD", "Lord").replace("Lᴏʀᴅ", "Lord")


def safe_settings_snapshot(settings_dict):
    snapshot = {}
    for key, value in dict(settings_dict or {}).items():
        if key == "extra_collects":
            snapshot[key] = [str(getattr(item, "pk", item)) for item in value]
        else:
            snapshot[key] = value
    return json.loads(json.dumps(snapshot, default=_json_default))


def line_reference_cache_key(line_type, text, provider_mode=None):
    payload = {
        "provider_mode": provider_mode or AudioGenerationConfig.get_solo().provider_mode,
        "line_type": normalize_line_type(line_type),
        "text": normalize_audio_text(text),
    }
    return hash_payload(payload)


def site_base_url():
    return settings.SITE_ADDRESS.rstrip("/")


def absolute_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{site_base_url()}{path}"


def line_reference_url(line_type, text, provider_mode=None):
    cache_key = line_reference_cache_key(line_type, text, provider_mode=provider_mode)
    filename = f"audio_ref_{cache_key[:32]}.mp3"
    media_path = settings.MEDIA_URL + filename
    return absolute_url(media_path), media_path


def media_file_name(cache_key, suffix="mp3"):
    random_part = hashlib.sha1(os.urandom(16)).hexdigest()[:12]
    return f"audio_{cache_key[:24]}_{random_part}.{suffix}"


def media_path_for_file(file_name):
    return os.path.join(settings.MEDIA_ROOT, file_name)


def public_media_path(file_name):
    return settings.MEDIA_URL + file_name


def track_url(file_name):
    return absolute_url(f"/api/v1/audio_track/{file_name}")


def file_url(file_name):
    return absolute_url(public_media_path(file_name))


def audio_duration(file_path, fallback=Decimal("0")):
    try:
        return Decimal(str(round(MP3(file_path).info.length, 3)))
    except Exception:
        return fallback


def parse_silence_seconds(text):
    match = re.search(r"(\d+(?:\.\d+)?)", str(text or ""))
    if not match:
        return Decimal("1.0")
    seconds = Decimal(match.group(1))
    return min(max(seconds, Decimal("0.1")), Decimal("300.0"))


def decimal_seconds(value):
    return Decimal(str(round(float(value or 0), 3)))


def json_seconds(value):
    return float(decimal_seconds(value))


class AudioCache:
    def __init__(self, context):
        self.context = context

    def reusable(self, cache_key):
        candidates = AudioGeneratedFile.objects.filter(
            cache_key=cache_key,
            status=AudioGeneratedFile.Status.READY,
            disabled_at__isnull=True,
            deleted_at__isnull=True,
        ).order_by("-created")
        for generated_file in candidates:
            if generated_file.file_name and os.path.exists(media_path_for_file(generated_file.file_name)):
                self.event(AudioGenerationEvent.Action.CACHE_HIT, generated_file)
                return generated_file
            generated_file.status = AudioGeneratedFile.Status.MISSING
            generated_file.save(update_fields=["status", "updated"])
            self.event(
                AudioGenerationEvent.Action.CACHE_SKIP,
                generated_file,
                error_message="Cached audio record pointed at a missing file.",
            )
        return None

    def create_pending(self, **kwargs):
        return AudioGeneratedFile.objects.create(
            status=AudioGeneratedFile.Status.PENDING,
            settings_hash=self.context.settings_hash,
            settings_snapshot=self.context.settings_snapshot,
            office=self.context.office_name,
            office_date=self.context.office_date,
            provider_mode=self.context.provider_mode,
            **kwargs,
        )

    def event(self, action, generated_file=None, **kwargs):
        AudioGenerationEvent.objects.create(
            generated_file=generated_file,
            action=action,
            provider=getattr(generated_file, "provider", kwargs.pop("provider", None)),
            provider_mode=getattr(generated_file, "provider_mode", self.context.provider_mode),
            generation_type=getattr(generated_file, "generation_type", kwargs.pop("generation_type", None)),
            model_id=getattr(generated_file, "model_id", kwargs.pop("model_id", None)),
            cache_key=getattr(generated_file, "cache_key", kwargs.pop("cache_key", None)),
            office=self.context.office_name,
            office_date=self.context.office_date,
            module_name=getattr(generated_file, "module_name", kwargs.pop("module_name", None)),
            settings_hash=self.context.settings_hash,
            characters=getattr(generated_file, "characters", kwargs.pop("characters", 0)),
            cost_units=getattr(generated_file, "cost_units", kwargs.pop("cost_units", 0)),
            cost_usd=getattr(generated_file, "cost_usd", kwargs.pop("cost_usd", 0)),
            request_id=getattr(generated_file, "request_id", kwargs.pop("request_id", None)),
            **kwargs,
        )


class AudioContext:
    def __init__(self, office, config, provider_mode):
        self.office = office
        self.config = config
        self.provider_mode = provider_mode
        self.settings_snapshot = safe_settings_snapshot(getattr(office, "settings", {}))
        self.settings_hash = hash_payload(self.settings_snapshot)
        self.office_name = office.__class__.__name__
        date = getattr(getattr(office, "date", None), "date", None)
        self.office_date = date.date() if hasattr(date, "date") else date
        self.request_path = getattr(getattr(office, "request", None), "get_full_path", lambda: "")()


class VoiceResolver:
    def __init__(self, provider, provider_mode):
        self.provider = provider
        self.provider_mode = provider_mode
        self.provider_name = "elevenlabs" if provider.provider_name == "elevenlabs" else "openai"
        self._voices = None

    @property
    def voices(self):
        if self._voices is None:
            self._voices = list(
                AudioVoice.objects.filter(provider=self.provider_name, enabled=True).order_by("role", "order", "name")
            )
        return self._voices

    def for_role(self, role, selector_key=""):
        role = normalize_line_type(role)
        role_voices = [voice for voice in self.voices if voice.role == role]
        if role == AudioVoice.Role.READER and role_voices:
            index = int(hash_payload({"selector": selector_key or role})[:8], 16) % len(role_voices)
            return role_voices[index].voice_id
        if role_voices:
            return role_voices[0].voice_id
        if self.provider_name == "openai":
            return OPENAI_DEFAULT_VOICES.get(role)
        return None


class FFMPEGAudioAssembler:
    def __init__(self, config):
        self.config = config

    def generate_silence(self, output_path, seconds):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            str(seconds),
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            output_path,
        ]
        self._run(command)

    def assemble(self, pieces, output_path, padding_ms=None):
        if not pieces:
            raise ValueError("Cannot assemble an empty audio track.")

        temp_dir = tempfile.mkdtemp(prefix="office-audio-")
        try:
            wav_files = []
            padding_file = None
            padding_seconds = Decimal(str((padding_ms if padding_ms is not None else 0) / 1000))
            for index, piece in enumerate(pieces):
                wav_path = os.path.join(temp_dir, f"{index:04d}.wav")
                self._normalize(piece.file_path, wav_path, piece.kind)
                wav_files.append(wav_path)
                if padding_seconds > 0 and index < len(pieces) - 1:
                    if padding_file is None:
                        padding_file = os.path.join(temp_dir, "padding.wav")
                        self._generate_silence_wav(padding_file, padding_seconds)
                    wav_files.append(padding_file)

            list_path = os.path.join(temp_dir, "files.txt")
            with open(list_path, "w", encoding="utf-8") as list_file:
                for wav_file in wav_files:
                    list_file.write(f"file '{os.path.abspath(wav_file)}'\n")

            command = [
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
                output_path,
            ]
            self._run(command)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _normalize(self, input_path, output_path, kind):
        if kind == AudioGeneratedFile.GenerationType.SILENCE:
            filters = "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
        elif kind == AudioGeneratedFile.GenerationType.MODULE:
            filters = (
                f"loudnorm=I={self.config.assembly_target_loudness_lufs}:LRA=11:TP=-1.5,"
                "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
            )
        else:
            target = (
                self.config.sound_target_loudness_lufs
                if kind == AudioGeneratedFile.GenerationType.SOUND
                else self.config.assembly_target_loudness_lufs
            )
            filters = (
                "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB:"
                "stop_periods=1:stop_duration=0.10:stop_threshold=-50dB,"
                f"loudnorm=I={target}:LRA=11:TP=-1.5,"
                "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
            )
        command = ["ffmpeg", "-y", "-i", input_path, "-af", filters, output_path]
        self._run(command)

    def _generate_silence_wav(self, output_path, seconds):
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            str(seconds),
            "-acodec",
            "pcm_s16le",
            output_path,
        ]
        self._run(command)

    @staticmethod
    def _run(command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise AudioProviderError(f"ffmpeg failed: {result.stderr}")


class OfficeAudioBuilder:
    def __init__(self, office, modules=None):
        self.office = office
        self.modules = modules
        self.config = AudioGenerationConfig.get_solo()
        self.provider, self.provider_mode = get_audio_provider(self.config)
        self.context = AudioContext(office, self.config, self.provider_mode)
        self.cache = AudioCache(self.context)
        self.voice_resolver = VoiceResolver(self.provider, self.provider_mode)
        self.assembler = FFMPEGAudioAssembler(self.config)

    def build(self):
        office_settings = getattr(self.office, "settings", {})
        bible_translation = getattr(office_settings, "bible_translation", None)
        if bible_translation and bible_translation not in ["esv", "kjv"]:
            return []

        modules = self.modules or [module for module in self.office.get_modules()]
        modules = [module for module in modules if module and module.get("lines")]
        headings = self._headings(modules)
        module_results = []
        tracks = []
        for module in modules:
            try:
                module_result = self._build_module(module)
            except Exception as exc:
                self.cache.event(
                    AudioGenerationEvent.Action.ERROR,
                    provider=self.provider.provider_name,
                    generation_type=AudioGeneratedFile.GenerationType.MODULE,
                    module_name=module.get("name"),
                    error_message=str(exc),
                )
                continue
            if module_result:
                module_results.append(module_result)
                tracks.extend(self._tracks_from_module(module_result))

        if not module_results:
            return {"tracks": [], "headings": headings, "single_track": []}

        final_result, track_list, short_track_list = self._assemble_final(module_results)
        self._record_usage(final_result.generated_file, module_name="Full Office", generation_type="final")
        return {
            "tracks": tracks,
            "headings": headings,
            "single_track": [final_result.url, final_result.media_path, track_list, short_track_list],
        }

    def legacy_line_audio(self, line, no_generate=False):
        line_type = normalize_line_type(line.get("line_type"))
        if line_type not in SPOKEN_LINE_TYPES and line_type != HTML_LINE_TYPE:
            return None, None
        text = normalize_audio_text(line.get("content"))
        if no_generate:
            return line_reference_url(line_type, text, provider_mode=self.provider_mode)
        item = AudioItem(
            module_name="Legacy",
            line_id=line_reference_cache_key(line_type, text, provider_mode=self.provider_mode),
            line_type=line_type,
            role="reader" if line_type == HTML_LINE_TYPE else line_type,
            text=text,
            selector_key=f"Legacy:{text}",
        )
        artifact = self._generate_spoken_items([item])[0]
        return artifact.url, artifact.media_path

    def _headings(self, modules):
        headings = []
        for module in modules:
            lines = module.get("lines", [])
            for index, line in enumerate(lines):
                if normalize_line_type(line.get("line_type")) != "heading":
                    continue
                look_ahead_line = None
                for candidate in lines[index + 1 :]:
                    candidate_type = normalize_line_type(candidate.get("line_type"))
                    if candidate_type in NAVIGABLE_LINE_TYPES and "<iframe" not in str(candidate.get("content", "")):
                        look_ahead_line = candidate
                        break
                if look_ahead_line:
                    headings.append({"heading": line.get("content"), "next_id": look_ahead_line.get("id")})
        return headings

    def _build_module(self, module):
        items = self._items_for_module(module)
        if not items:
            return None

        pieces = []
        spoken_buffer = []

        def flush_spoken():
            nonlocal spoken_buffer
            if spoken_buffer:
                pieces.extend(self._generate_spoken_items(spoken_buffer))
                spoken_buffer = []

        for item in items:
            if item.kind == AudioGeneratedFile.GenerationType.SPOKEN:
                spoken_buffer.append(item)
                continue
            flush_spoken()
            if item.kind == AudioGeneratedFile.GenerationType.SILENCE:
                pieces.append(self._generate_silence(item))
            elif item.kind == AudioGeneratedFile.GenerationType.SOUND:
                sound_piece = self._generate_sound(item)
                if sound_piece:
                    pieces.append(sound_piece)
        flush_spoken()

        if not pieces:
            return None

        module_result = self._assemble_artifacts(
            pieces,
            AudioGeneratedFile.GenerationType.MODULE,
            module_name=module.get("name"),
        )
        self._record_usage(module_result.generated_file, module_name=module.get("name"), generation_type="module")
        return {
            "name": module.get("name"),
            "artifact": module_result,
            "pieces": pieces,
            "line_segments": module_result.line_segments,
        }

    def _items_for_module(self, module):
        module_name = module.get("name") or "Module"
        items = []
        for line in module.get("lines", []):
            line_type = normalize_line_type(line.get("line_type"))
            content = line.get("content")
            if line_type == HTML_LINE_TYPE:
                if "<iframe" in str(content):
                    continue
                items.extend(self._items_from_html(content, line, module_name))
                continue
            if line_type in SPOKEN_LINE_TYPES:
                text = normalize_audio_text(content)
                if text:
                    items.append(
                        AudioItem(
                            module_name=module_name,
                            line_id=line.get("id") or line_reference_cache_key(line_type, text, self.provider_mode),
                            line_type=line_type,
                            role=line_type,
                            text=text,
                            selector_key=f"{self.context.office_date}:{self.context.office_name}:{module_name}",
                        )
                    )
                continue
            if line_type == SILENCE_LINE_TYPE:
                seconds = parse_silence_seconds(content)
                items.append(
                    AudioItem(
                        module_name=module_name,
                        line_id=line.get("id")
                        or line_reference_cache_key(line_type, str(seconds), self.provider_mode),
                        line_type=line_type,
                        role=line_type,
                        text=str(seconds),
                        kind=AudioGeneratedFile.GenerationType.SILENCE,
                        seconds=seconds,
                    )
                )
                continue
            if line_type == SOUND_LINE_TYPE and self.provider.provider_name == "elevenlabs":
                prompt = normalize_audio_text(content)
                if prompt:
                    items.append(
                        AudioItem(
                            module_name=module_name,
                            line_id=line.get("id") or line_reference_cache_key(line_type, prompt, self.provider_mode),
                            line_type=line_type,
                            role=line_type,
                            text=prompt,
                            kind=AudioGeneratedFile.GenerationType.SOUND,
                        )
                    )
        return items

    def _items_from_html(self, html, line, module_name):
        base_id = "_".join([str(line.get("id", "")).split("_")[0], str(line.get("id", "")).split("_")[-1]])
        items = []
        sentences = re.split(r"(?<=[.!?])", str(html))
        for sentence in sentences:
            soup = BeautifulSoup(sentence, "html.parser")
            plain_text = soup.get_text()
            text_without_verses = re.sub(r"(\b\d+\b\s)", "", plain_text)
            text = normalize_audio_text(text_without_verses)
            if not text:
                continue
            cache_key = line_reference_cache_key("reader", text, self.provider_mode)
            line_id = re.sub(r"_[^_]+$", f"_{cache_key[:32]}", base_id) if base_id else cache_key[:32]
            items.append(
                AudioItem(
                    module_name=module_name,
                    line_id=line_id,
                    line_type="reader",
                    role="reader",
                    text=text,
                    selector_key=f"{self.context.office_date}:{self.context.office_name}:{module_name}",
                )
            )
        return items

    def _generate_spoken_items(self, items):
        if self.provider.provider_name == "openai":
            return [self._generate_openai_spoken_item(item) for item in items]
        artifacts = []
        for chunk in self._spoken_chunks(items):
            artifacts.append(self._generate_elevenlabs_dialogue_chunk(chunk))
        return artifacts

    def _generate_openai_spoken_item(self, item):
        voice_id = self.voice_resolver.for_role(item.role, item.selector_key)
        payload = {
            "provider": "openai",
            "provider_mode": self.provider_mode,
            "generation_type": "spoken",
            "model_id": self.config.openai_model,
            "voice_id": voice_id,
            "line_type": item.line_type,
            "text": item.text,
            "settings_hash": self.context.settings_hash,
        }
        cache_key = hash_payload(payload)
        cached = self.cache.reusable(cache_key)
        if cached:
            artifact = self._artifact_from_file(cached)
            self._record_line_usage(artifact, item)
            return artifact

        generated_file = self.cache.create_pending(
            provider=AudioGeneratedFile.Provider.OPENAI,
            generation_type=AudioGeneratedFile.GenerationType.SPOKEN,
            cache_key=cache_key,
            content_hash=hash_payload({"text": item.text}),
            text_preview=item.text[:1000],
            voice_key=voice_id,
            voices={item.role: voice_id},
            model_id=self.config.openai_model,
            endpoint="openai.audio.speech",
            module_name=item.module_name,
            line_type=item.line_type,
            line_id=item.line_id,
        )
        file_name = media_file_name(cache_key)
        output_path = media_path_for_file(file_name)
        try:
            result = self.provider.generate_spoken_file(item.text, voice_id, output_path)
            duration = audio_duration(output_path)
            cost_usd, cost_source = self._estimate_cost(
                "openai",
                self.config.openai_model,
                AudioGeneratedFile.GenerationType.SPOKEN,
                characters=result.characters,
                cost_units=result.cost_units,
                duration=duration,
            )
            line_segments = [{"id": item.line_id, "start_time": 0.0, "duration": json_seconds(duration)}]
            self._mark_ready(
                generated_file,
                file_name,
                duration,
                result,
                cost_usd,
                cost_source,
                line_segments=line_segments,
            )
            self.cache.event(AudioGenerationEvent.Action.GENERATED, generated_file)
        except Exception as exc:
            self._mark_failed(generated_file, exc)
            raise
        artifact = self._artifact_from_file(generated_file)
        self._record_line_usage(artifact, item)
        return artifact

    def _generate_elevenlabs_dialogue_chunk(self, chunk):
        inputs = []
        voices = {}
        for item in chunk:
            voice_id = self.voice_resolver.for_role(item.role, item.selector_key)
            if not voice_id:
                raise AudioProviderError(f"No ElevenLabs voice is enabled for {item.role}.")
            voices[item.role] = voice_id
            inputs.append({"text": item.text, "voice_id": voice_id})

        payload = {
            "provider": "elevenlabs",
            "provider_mode": self.provider_mode,
            "generation_type": "spoken",
            "model_id": "eleven_v3",
            "output_format": self.config.elevenlabs_output_format,
            "apply_text_normalization": self.config.elevenlabs_apply_text_normalization,
            "language_code": self.config.elevenlabs_language_code,
            "seed": self.config.elevenlabs_seed,
            "inputs": inputs,
            "line_ids": [item.line_id for item in chunk],
            "settings_hash": self.context.settings_hash,
        }
        cache_key = hash_payload(payload)
        cached = self.cache.reusable(cache_key)
        if cached:
            artifact = self._artifact_from_file(cached)
            for item in chunk:
                self._record_line_usage(artifact, item)
            return artifact

        text_preview = " ".join(item.text for item in chunk)[:1000]
        generated_file = self.cache.create_pending(
            provider=AudioGeneratedFile.Provider.ELEVENLABS,
            generation_type=AudioGeneratedFile.GenerationType.SPOKEN,
            cache_key=cache_key,
            content_hash=hash_payload({"inputs": inputs}),
            text_preview=text_preview,
            voice_key=hash_payload(voices),
            voices=voices,
            model_id="eleven_v3",
            endpoint="/v1/text-to-dialogue/with-timestamps",
            module_name=chunk[0].module_name,
            line_type="dialogue_chunk",
            line_id=chunk[0].line_id if len(chunk) == 1 else None,
        )
        file_name = media_file_name(cache_key)
        output_path = media_path_for_file(file_name)
        try:
            result = self.provider.generate_dialogue_file(inputs, output_path)
            duration = audio_duration(output_path)
            line_segments = self._line_segments_from_voice_segments(chunk, result.voice_segments, duration)
            cost_usd, cost_source = self._estimate_cost(
                "elevenlabs",
                "eleven_v3",
                AudioGeneratedFile.GenerationType.SPOKEN,
                characters=result.characters,
                cost_units=result.cost_units,
                duration=duration,
            )
            self._mark_ready(
                generated_file,
                file_name,
                duration,
                result,
                cost_usd,
                cost_source,
                line_segments=line_segments,
            )
            self.cache.event(AudioGenerationEvent.Action.GENERATED, generated_file)
        except Exception as exc:
            self._mark_failed(generated_file, exc)
            raise
        artifact = self._artifact_from_file(generated_file)
        for item in chunk:
            self._record_line_usage(artifact, item)
        return artifact

    def _generate_sound(self, item):
        duration = item.seconds or self.config.sound_default_duration_seconds
        payload = {
            "provider": "elevenlabs",
            "provider_mode": self.provider_mode,
            "generation_type": "sound",
            "model_id": self.config.elevenlabs_sound_model_id,
            "output_format": self.config.elevenlabs_output_format,
            "prompt": item.text,
            "duration_seconds": str(duration) if duration else None,
            "loop": self.config.sound_loop,
            "prompt_influence": str(self.config.sound_prompt_influence),
        }
        cache_key = hash_payload(payload)
        cached = self.cache.reusable(cache_key)
        if cached:
            artifact = self._artifact_from_file(cached)
            self._record_line_usage(artifact, item)
            return artifact

        generated_file = self.cache.create_pending(
            provider=AudioGeneratedFile.Provider.ELEVENLABS,
            generation_type=AudioGeneratedFile.GenerationType.SOUND,
            cache_key=cache_key,
            content_hash=hash_payload({"prompt": item.text}),
            text_preview=item.text[:1000],
            model_id=self.config.elevenlabs_sound_model_id,
            endpoint="/v1/sound-generation",
            module_name=item.module_name,
            line_type=SOUND_LINE_TYPE,
            line_id=item.line_id,
        )
        file_name = media_file_name(cache_key)
        output_path = media_path_for_file(file_name)
        try:
            result = self.provider.generate_sound_file(item.text, output_path, duration_seconds=duration)
            actual_duration = audio_duration(output_path, fallback=Decimal(str(duration or 0)))
            line_segments = [{"id": item.line_id, "start_time": 0.0, "duration": json_seconds(actual_duration)}]
            cost_usd, cost_source = self._estimate_cost(
                "elevenlabs",
                self.config.elevenlabs_sound_model_id,
                AudioGeneratedFile.GenerationType.SOUND,
                characters=result.characters,
                cost_units=result.cost_units,
                duration=actual_duration,
            )
            self._mark_ready(
                generated_file,
                file_name,
                actual_duration,
                result,
                cost_usd,
                cost_source,
                line_segments=line_segments,
            )
            self.cache.event(AudioGenerationEvent.Action.GENERATED, generated_file)
        except Exception as exc:
            self._mark_failed(generated_file, exc)
            raise
        artifact = self._artifact_from_file(generated_file)
        self._record_line_usage(artifact, item)
        return artifact

    def _generate_silence(self, item):
        payload = {
            "provider": "local",
            "provider_mode": self.provider_mode,
            "generation_type": "silence",
            "duration_seconds": str(item.seconds),
            "output": "mp3_44100_128",
        }
        cache_key = hash_payload(payload)
        cached = self.cache.reusable(cache_key)
        if cached:
            artifact = self._artifact_from_file(cached)
            self._record_line_usage(artifact, item)
            return artifact

        generated_file = self.cache.create_pending(
            provider=AudioGeneratedFile.Provider.LOCAL,
            generation_type=AudioGeneratedFile.GenerationType.SILENCE,
            cache_key=cache_key,
            content_hash=hash_payload({"seconds": item.seconds}),
            text_preview=f"{item.seconds} seconds",
            model_id="local_silence",
            endpoint="ffmpeg.anullsrc",
            module_name=item.module_name,
            line_type=SILENCE_LINE_TYPE,
            line_id=item.line_id,
        )
        file_name = media_file_name(cache_key)
        output_path = media_path_for_file(file_name)
        try:
            self.assembler.generate_silence(output_path, item.seconds)
            duration = audio_duration(output_path, fallback=item.seconds)
            line_segments = [{"id": item.line_id, "start_time": 0.0, "duration": json_seconds(duration)}]
            generated_file.file_name = file_name
            generated_file.media_path = public_media_path(file_name)
            generated_file.duration_seconds = duration
            generated_file.status = AudioGeneratedFile.Status.READY
            generated_file.response_metadata = {"line_segments": line_segments}
            generated_file.save()
            self.cache.event(AudioGenerationEvent.Action.GENERATED, generated_file)
        except Exception as exc:
            self._mark_failed(generated_file, exc)
            raise
        artifact = self._artifact_from_file(generated_file)
        self._record_line_usage(artifact, item)
        return artifact

    def _assemble_artifacts(self, pieces, generation_type, module_name=None):
        payload = {
            "provider_mode": self.provider_mode,
            "generation_type": generation_type,
            "child_files": [str(piece.generated_file.pk) for piece in pieces],
            "child_cache_keys": [piece.generated_file.cache_key for piece in pieces],
            "target_loudness": str(self.config.assembly_target_loudness_lufs),
            "sound_loudness": str(self.config.sound_target_loudness_lufs),
            "padding_ms": self.config.module_boundary_padding_ms,
            "module_name": module_name,
            "settings_hash": self.context.settings_hash,
        }
        cache_key = hash_payload(payload)
        cached = self.cache.reusable(cache_key)
        if cached:
            return self._artifact_from_file(cached, track_url_mode=True)

        generated_file = self.cache.create_pending(
            provider=AudioGeneratedFile.Provider.LOCAL,
            generation_type=generation_type,
            cache_key=cache_key,
            content_hash=hash_payload(payload["child_cache_keys"]),
            text_preview=f"Assembled {len(pieces)} audio pieces",
            model_id="local_ffmpeg",
            endpoint="ffmpeg.concat",
            module_name=module_name,
            response_metadata={"child_files": payload["child_files"]},
        )
        file_name = media_file_name(cache_key)
        output_path = media_path_for_file(file_name)
        try:
            self.assembler.assemble(pieces, output_path, padding_ms=self.config.module_boundary_padding_ms)
            duration = audio_duration(output_path, fallback=sum((piece.duration for piece in pieces), Decimal("0")))
            line_segments = self._offset_line_segments(pieces)
            generated_file.file_name = file_name
            generated_file.media_path = public_media_path(file_name)
            generated_file.duration_seconds = duration
            generated_file.status = AudioGeneratedFile.Status.READY
            generated_file.response_metadata = {
                "child_files": payload["child_files"],
                "line_segments": line_segments,
                "padding_ms": self.config.module_boundary_padding_ms,
            }
            generated_file.save()
            self.cache.event(AudioGenerationEvent.Action.ASSEMBLED, generated_file)
        except Exception as exc:
            self._mark_failed(generated_file, exc)
            raise
        return self._artifact_from_file(generated_file, track_url_mode=True)

    def _assemble_final(self, module_results):
        pieces = [module_result["artifact"] for module_result in module_results]
        final = self._assemble_artifacts(pieces, AudioGeneratedFile.GenerationType.FINAL, module_name="Full Office")
        track_list = []
        short_track_list = []
        current = Decimal("0")
        padding = Decimal(str(self.config.module_boundary_padding_ms / 1000))
        for index, module_result in enumerate(module_results):
            module_name = module_result["name"]
            track_list.append({"name": module_name, "start_time": float(current)})
            for segment in module_result["line_segments"]:
                short_track_list.append(
                    {"id": segment["id"], "start_time": float(current + Decimal(str(segment["start_time"])))}
                )
            current += module_result["artifact"].duration
            if padding > 0 and index < len(module_results) - 1:
                current += padding
        return final, track_list, self._dedupe_segments(short_track_list)

    def _spoken_chunks(self, items):
        split_items = []
        for item in items:
            split_items.extend(self._split_long_item(item))

        chunks = []
        chunk = []
        count = 0
        target = min(self.config.spoken_chunk_target_characters, self.config.spoken_chunk_max_characters)
        for item in split_items:
            item_length = len(item.text)
            if chunk and count + item_length > target:
                chunks.append(chunk)
                chunk = []
                count = 0
            chunk.append(item)
            count += item_length
        if chunk:
            chunks.append(chunk)
        return chunks

    def _split_long_item(self, item):
        max_characters = self.config.spoken_chunk_max_characters
        if len(item.text) <= max_characters:
            return [item]
        parts = []
        words = item.text.split()
        current = []
        count = 0
        for word in words:
            if current and count + len(word) + 1 > max_characters:
                parts.append(" ".join(current))
                current = []
                count = 0
            current.append(word)
            count += len(word) + 1
        if current:
            parts.append(" ".join(current))
        return [replace(item, text=part) for part in parts]

    def _line_segments_from_voice_segments(self, chunk, voice_segments, duration):
        by_index = {}
        for segment in voice_segments or []:
            index = segment.get("dialogue_input_index")
            if index is None:
                continue
            start = Decimal(str(segment.get("start_time_seconds", 0)))
            end = Decimal(str(segment.get("end_time_seconds", 0)))
            existing = by_index.get(index)
            if existing is None:
                by_index[index] = [start, end]
            else:
                existing[0] = min(existing[0], start)
                existing[1] = max(existing[1], end)
        if by_index:
            return [
                {
                    "id": item.line_id,
                    "start_time": json_seconds(by_index.get(index, [Decimal("0"), Decimal("0")])[0]),
                    "duration": json_seconds(
                        by_index.get(index, [Decimal("0"), Decimal("0")])[1]
                        - by_index.get(index, [Decimal("0"), Decimal("0")])[0]
                    ),
                }
                for index, item in enumerate(chunk)
            ]

        duration_per_item = duration / Decimal(len(chunk)) if chunk else Decimal("0")
        return [
            {
                "id": item.line_id,
                "start_time": json_seconds(duration_per_item * index),
                "duration": json_seconds(duration_per_item),
            }
            for index, item in enumerate(chunk)
        ]

    def _offset_line_segments(self, pieces):
        line_segments = []
        current = Decimal("0")
        padding = Decimal(str(self.config.module_boundary_padding_ms / 1000))
        for index, piece in enumerate(pieces):
            for segment in piece.line_segments:
                line_segments.append(
                    {
                        "id": segment["id"],
                        "start_time": json_seconds(current + Decimal(str(segment.get("start_time", 0)))),
                        "duration": json_seconds(segment.get("duration", 0)),
                    }
                )
            current += piece.duration
            if padding > 0 and index < len(pieces) - 1:
                current += padding
        return self._dedupe_segments(line_segments)

    def _dedupe_segments(self, segments):
        seen = set()
        deduped = []
        for segment in segments:
            segment_id = segment.get("id")
            if segment_id in seen:
                continue
            seen.add(segment_id)
            deduped.append(segment)
        return deduped

    def _artifact_from_file(self, generated_file, track_url_mode=False):
        line_segments = generated_file.response_metadata.get("line_segments", [])
        return ArtifactResult(
            generated_file=generated_file,
            file_path=media_path_for_file(generated_file.file_name),
            url=track_url(generated_file.file_name) if track_url_mode else file_url(generated_file.file_name),
            media_path=generated_file.media_path,
            duration=generated_file.duration_seconds,
            line_segments=line_segments,
            kind=generated_file.generation_type,
        )

    def _tracks_from_module(self, module_result):
        tracks = []
        for piece in module_result["pieces"]:
            for segment in piece.line_segments:
                tracks.append(
                    {
                        "line_id": segment["id"],
                        "module": module_result["name"],
                        "url": piece.url,
                        "path": piece.media_path,
                    }
                )
        return tracks

    def _mark_ready(self, generated_file, file_name, duration, result, cost_usd, cost_source, line_segments):
        metadata = result.metadata.copy()
        metadata["line_segments"] = line_segments
        if result.alignment:
            metadata["alignment"] = result.alignment
        metadata = json.loads(json.dumps(metadata, default=_json_default))
        generated_file.file_name = file_name
        generated_file.media_path = public_media_path(file_name)
        generated_file.duration_seconds = duration
        generated_file.characters = result.characters
        generated_file.cost_units = result.cost_units
        generated_file.cost_usd = cost_usd
        generated_file.cost_source = cost_source
        generated_file.request_id = result.request_id
        generated_file.response_metadata = metadata
        generated_file.status = AudioGeneratedFile.Status.READY
        generated_file.save()

    def _mark_failed(self, generated_file, exc):
        generated_file.status = AudioGeneratedFile.Status.FAILED
        generated_file.error_message = str(exc)
        generated_file.save(update_fields=["status", "error_message", "updated"])
        self.cache.event(AudioGenerationEvent.Action.ERROR, generated_file, error_message=str(exc))

    def _estimate_cost(self, provider, model_id, generation_type, characters, cost_units, duration):
        rate = (
            AudioCostRate.objects.filter(
                provider=provider,
                model_id=model_id,
                generation_type=generation_type,
                enabled=True,
                effective_at__lte=timezone.now(),
            )
            .order_by("-effective_at")
            .first()
        )
        source = "configured_rate"
        if not rate:
            default = DEFAULT_COST_RATES.get((provider, model_id, generation_type))
            if not default:
                return Decimal("0"), "unpriced"
            unit, usd_per_unit = default
            source = "default_rate"
        else:
            unit = rate.unit
            usd_per_unit = rate.usd_per_unit

        quantity = Decimal("0")
        if unit == AudioCostRate.Unit.CHARACTER:
            quantity = Decimal(characters or 0)
        elif unit == AudioCostRate.Unit.COST_UNIT:
            quantity = Decimal(cost_units or 0)
        elif unit == AudioCostRate.Unit.MINUTE:
            quantity = Decimal(duration or 0) / Decimal("60")
        elif unit == AudioCostRate.Unit.FILE:
            quantity = Decimal("1")
        return (quantity * Decimal(usd_per_unit)).quantize(Decimal("0.000001")), source

    def _record_line_usage(self, artifact, item):
        self._record_usage(
            artifact.generated_file,
            module_name=item.module_name,
            line_id=item.line_id,
            line_type=item.line_type,
            generation_type=artifact.generated_file.generation_type,
            duration=artifact.duration,
        )

    def _record_usage(
        self,
        generated_file,
        module_name=None,
        line_id=None,
        line_type=None,
        generation_type=None,
        start_time=Decimal("0"),
        duration=Decimal("0"),
    ):
        AudioUsage.objects.create(
            generated_file=generated_file,
            office=self.context.office_name,
            office_date=self.context.office_date,
            module_name=module_name,
            line_id=line_id,
            line_type=line_type,
            provider_mode=self.provider_mode,
            generation_type=generation_type or generated_file.generation_type,
            settings_hash=self.context.settings_hash,
            settings_snapshot=self.context.settings_snapshot,
            start_time_seconds=start_time,
            duration_seconds=duration,
            request_path=self.context.request_path,
        )

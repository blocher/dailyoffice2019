"""Offline seven-day Gemini Batch API bootstrap; never called by web requests.

Prepare captures the real serializer's grouped clips without synthesis, alignment,
media writes, or full-track assembly. Submit uses bounded inline batches; import
publishes each successful clip independently. Manifests are resumable local state.
API schemas: https://ai.google.dev/api/batch-api and /api/generate-content.
"""

import base64
import binascii
import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

import requests
from django.conf import settings
from django.test import RequestFactory
from django.urls import resolve
from mutagen.mp3 import MP3

from office.api.views import index
from office.api.views.tts import GeminiTTSProvider
from office.models import AudioClip

API = "https://generativelanguage.googleapis.com/v1beta"
SERIALIZER = index.GenericDailyOfficeSerializer

OFFICES = [
    "office/morning_prayer",
    "office/midday_prayer",
    "office/evening_prayer",
    "office/compline",
    "family/morning_prayer",
    "family/midday_prayer",
    "family/early_evening_prayer",
    "family/close_of_day_prayer",
]

BASE_SETTINGS = {
    "language_style": "contemporary",
    "psalm_translation": "contemporary",
    "bible_translation": "esv",
    "psalter": "60",
    "reading_cycle": "1",
    "reading_length": "full",
    "reading_audio": "off",
    "canticle_rotation": "1979",
    "psalm_style": "whole_verse",
    "lectionary": "daily-office-readings",
    "confession": "long-on-fast",
    "absolution": "lay",
    "morning_prayer_invitatory": "invitatory_traditional",
    "reading_headings": "off",
    "language_style_for_our_father": "traditional",
    "national_holidays": "all",
    "suffrages": "rotating",
    "collects": "rotating",
    "mp_great_litany": "mp_litany_on",
    "ep_great_litany": "ep_litany_on",
    "general_thanksgiving": "on",
    "chrysostom": "on",
    "grace": "rotating",
    "o_antiphons": "literal",
    "family_readings": "brief",
    "family_reading_audio": "off",
    "family_collect": "time_of_day",
    "family-opening-sentence": "family-opening-sentence-fixed",
    "family-creed": "family-creed-yes",
    "extra_collects": "",
    "include_audio_links": "true",
}

STYLES = [
    {
        "language_style": "contemporary",
        "psalm_translation": "contemporary",
        "bible_translation": "esv",
        "language_style_for_our_father": "contemporary",
    },
    {
        "language_style": "traditional",
        "psalm_translation": "traditional",
        "bible_translation": "kjv",
        "language_style_for_our_father": "traditional",
    },
]

VARIATIONS = [
    {"psalter": "30"},
    {"canticle_rotation": "default"},
    {"canticle_rotation": "2011"},
    {"psalm_style": "half_verse"},
    {"psalm_style": "unison"},
    {"lectionary": "mass-readings"},
    {"absolution": "priest"},
    {"morning_prayer_invitatory": "invitatory_jubilate_on_feasts"},
    {"morning_prayer_invitatory": "celebratory_always"},
    {"morning_prayer_invitatory": "invitatory_rotating"},
    {"reading_length": "abbreviated"},
]


def provider():
    active = index.TTS_PROVIDER
    if not isinstance(active, GeminiTTSProvider) or not active.model.startswith("gemini-3.8-"):
        raise ValueError("Batch bootstrap requires TTS_PROVIDER=gemini and a Gemini 3.8 TTS model.")
    return active


def save_manifest(path, manifest):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = handle.name
        json.dump(manifest, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def manifest_lock(path):
    """Prevent concurrent submit/import processes using the same manifest."""
    with open(f"{path}.lock", "a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another process is using this manifest.") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def load_manifest(path):
    manifest = json.loads(Path(path).read_text())
    active = provider()
    if (
        manifest.get("version") != 1
        or manifest.get("signature") != active.cache_signature()
        or manifest.get("model") != active.model
        or manifest.get("style") != active.effective_instructions
    ):
        raise ValueError("Manifest version or Gemini configuration changed; restore the original configuration.")
    for key, clip in manifest["clips"].items():
        if key != str(SERIALIZER.tts_clip_key(clip["voice"], clip["text"])):
            raise ValueError("Manifest clip key does not match its voice/text/configuration.")
    return manifest


def clip_path(key):
    # Keys are validated against the serializer hash before any filesystem write.
    return Path(settings.MEDIA_ROOT) / "gemini" / f"{key}.mp3"


def nonempty(path):
    return path.is_file() and path.stat().st_size > 0


def office_requests(start, days):
    for offset in range(days):
        day = start + timedelta(days=offset)
        for office in OFFICES:
            for style in STYLES:
                # Include the baseline as well as each scheduled variation.
                for variation in [{}, *VARIATIONS]:
                    yield f"/api/v1/{office}/{day:%Y-%m-%d}", BASE_SETTINGS | style | variation


def prepare(start, days=7, batch_size=50, progress=None):
    if not 1 <= days <= 31 or not 1 <= batch_size <= 100:
        raise ValueError("Days must be 1–31 and batch size must be 1–100.")
    active = provider()
    clips, resolved = {}, {}

    def collect(text, line_type, kind, no_generate=False):
        if no_generate:
            # HTML decoration asks for IDs for optional text, not synthesis.
            voice = active.voice_for_text(line_type, text)
            if not voice:
                return None, None
            key = SERIALIZER.tts_clip_key(voice, text)
            path = settings.MEDIA_URL + f"gemini/{key}.mp3"
            return f"{index.audio_base_url()}{path}", path
        role = active.role_for_line_type(line_type)
        identity = (role, text)
        if identity in resolved:
            return resolved[identity]
        reusable = SERIALIZER.find_reusable_reader(text, line_type)
        voice = active.voice_for_text(line_type, text)
        if not voice or not text.strip():
            return None, None
        key = str(SERIALIZER.tts_clip_key(voice, text))
        filename = reusable.filename if reusable else f"gemini/{key}.mp3"
        if not reusable and not nonempty(clip_path(key)):
            clips.setdefault(key, {"text": text, "voice": voice, "line_type": line_type, "kind": kind})
        path = settings.MEDIA_URL + filename
        resolved[identity] = (f"{index.audio_base_url()}{path}", path)
        return resolved[identity]

    token = index.AUDIO_CLIP_COLLECTOR.set(collect)
    count = 0
    try:
        for url, params in office_requests(start, days):
            request = RequestFactory().get(url, data=params)
            request._audio_prewarm = True
            match = resolve(url)
            response = match.func(request, *match.args, **match.kwargs)
            if response.status_code >= 400:
                raise ValueError(f"Unable to plan {url}: HTTP {response.status_code}.")
            count += 1
            if progress and count % 24 == 0:
                progress(f"Planned {count} office variants; {len(clips)} missing unique clips.")
    finally:
        index.AUDIO_CLIP_COLLECTOR.reset(token)
    keys = list(clips)
    return {
        "version": 1,
        "start_date": start.isoformat(),
        "days": days,
        "model": active.model,
        "signature": active.cache_signature(),
        "style": active.effective_instructions,
        "clips": clips,
        "chunks": [{"keys": keys[i : i + batch_size], "state": "prepared"} for i in range(0, len(keys), batch_size)],
    }


def batch_request(clip, style):
    # Gemini 3.8 batch TTS returns WAV by default. Explicit responseFormat
    # currently causes per-request INVALID_ARGUMENT, even though the generic
    # generateContent schema lists it. Verified against a live diagnostic batch.
    return {
        "contents": [{"role": "user", "parts": [{"text": clip["text"], "speechMetadata": {"style": style}}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"voice": clip["voice"]}},
        },
    }


class BatchHTTPError(ValueError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Gemini batch request failed: HTTP {status}.")


class BatchClient:
    """Small REST client; never retry a potentially accepted creation request."""

    def validate(self):
        key = getattr(settings, "GEMINI_API_KEY", "")
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        return key

    def request(self, method, url, **kwargs):
        response = requests.request(
            method,
            url,
            headers={"x-goog-api-key": self.validate()},
            timeout=(15, 180),
            allow_redirects=False,
            **kwargs,
        )
        if not 200 <= response.status_code < 300:
            response.close()
            raise BatchHTTPError(response.status_code)
        return response

    def create(self, model, payload):
        if not re.fullmatch(r"gemini-[a-zA-Z0-9.-]+", model):
            raise ValueError("Invalid Gemini model name.")
        with self.request("POST", f"{API}/models/{model}:batchGenerateContent", json=payload) as response:
            return response.json()

    def get(self, name):
        if not re.fullmatch(r"batches/[a-zA-Z0-9_-]+", name):
            raise ValueError("Expected a batches/<id> job name.")
        with self.request("GET", f"{API}/{name}") as response:
            return response.json()

    def results(self, operation):
        output = operation.get("response", {})
        if "inlinedResponses" in output:
            yield from output["inlinedResponses"]["inlinedResponses"]
            return
        name = output.get("responsesFile", "")
        if not re.fullmatch(r"files/[a-zA-Z0-9_-]+", name):
            raise ValueError("Completed job has no supported batch output.")
        url = f"https://generativelanguage.googleapis.com/download/v1beta/{name}:download?alt=media"
        with self.request("GET", url, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)


def submit(path, manifest, client):
    client.validate()
    for number, chunk in enumerate(manifest["chunks"]):
        if chunk.get("job"):
            continue
        if chunk["state"] != "prepared":
            raise ValueError(f"Chunk {number} has an uncertain submission. Use attach with its Google job name.")
        payload = {
            "batch": {
                "displayName": f"dailyoffice-{manifest['start_date']}-{Path(path).stem}-{number}",
                "inputConfig": {
                    "requests": {
                        "requests": [
                            {
                                "request": batch_request(manifest["clips"][key], manifest["style"]),
                                "metadata": {"key": key},
                            }
                            for key in chunk["keys"]
                        ]
                    }
                },
            }
        }
        if len(json.dumps(payload).encode("utf-8")) >= 19_000_000:
            raise ValueError("Chunk exceeds inline request size; prepare with a smaller --batch-size.")
        # Persist before sending: a crash/timeout must never silently duplicate a paid job.
        chunk["state"] = "submitting"
        save_manifest(path, manifest)
        try:
            operation = client.create(manifest["model"], payload)
        except BatchHTTPError as exc:
            if exc.status in {400, 401, 403, 404, 413, 429}:
                # A definite rejection, including quota exhaustion, can be retried.
                chunk["state"] = "prepared"
                save_manifest(path, manifest)
            raise
        name = operation.get("name", "")
        if not re.fullmatch(r"batches/[a-zA-Z0-9_-]+", name):
            raise ValueError("Submission returned no valid job name; reconcile before resubmitting.")
        chunk.update(job=name, state="submitted")
        save_manifest(path, manifest)


def attach(path, manifest, client, number, name):
    if number is None or not 0 <= number < len(manifest["chunks"]):
        raise ValueError("Provide a valid zero-based --chunk.")
    chunk = manifest["chunks"][number]
    if chunk.get("job") or chunk["state"] != "submitting":
        raise ValueError("Only an uncertain submission can be attached.")
    operation = client.get(name)
    expected = f"dailyoffice-{manifest['start_date']}-{Path(path).stem}-{number}"
    if operation.get("metadata", {}).get("displayName") != expected:
        raise ValueError("Job display name does not match this manifest/chunk.")
    chunk.update(job=name, state="submitted")
    save_manifest(path, manifest)


def import_clip(key, clip, result):
    target = clip_path(key)
    if not nonempty(target):
        candidates = result.get("candidates", [])
        if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
            raise ValueError("Missing, blocked, or incomplete audio candidate.")
        blocks = [
            part["inlineData"] for part in candidates[0].get("content", {}).get("parts", []) if "inlineData" in part
        ]
        if len(blocks) != 1 or blocks[0].get("mimeType", "").split(";")[0] not in {"audio/wav", "audio/x-wav"}:
            raise ValueError("Expected one complete WAV audio block.")
        try:
            audio = base64.b64decode(blocks[0]["data"], validate=True)
        except (KeyError, ValueError, binascii.Error) as exc:
            raise ValueError("Invalid base64 audio.") from exc
        provider().write_wav(audio, str(target))
    # Unlike interactive best-effort tracking, fail and retry import on DB errors.
    duration = MP3(target).info.length
    AudioClip.objects.get_or_create(
        key=key,
        defaults={
            **clip,
            "filename": f"gemini/{key}.mp3",
            "provider": "gemini",
            "model": provider().model,
            "speed": provider().speed,
            "duration": duration,
        },
    )


def refresh(path, manifest, client, import_results=False, progress=None):
    problems = 0
    for number, chunk in enumerate(manifest["chunks"]):
        if not chunk.get("job") or chunk.get("imported"):
            continue
        operation = client.get(chunk["job"])
        state = operation.get("metadata", {}).get("state", "UNKNOWN")
        chunk["state"] = state
        stats = operation.get("metadata", {}).get("batchStats", {})
        chunk["stats"] = stats
        save_manifest(path, manifest)
        if progress:
            progress(
                f"Chunk {number}: {chunk['job']} {state}; "
                f"{stats.get('successfulRequestCount', 0)} succeeded, "
                f"{stats.get('failedRequestCount', 0)} failed, "
                f"{stats.get('pendingRequestCount', 0)} pending requests"
            )
        if operation.get("error") or state in {
            "JOB_STATE_FAILED",
            "JOB_STATE_CANCELLED",
            "JOB_STATE_EXPIRED",
            "BATCH_STATE_FAILED",
            "BATCH_STATE_CANCELLED",
            "BATCH_STATE_EXPIRED",
        }:
            problems += 1
            continue
        if not import_results:
            problems += int(stats.get("failedRequestCount", 0))
            continue
        if not operation.get("done"):
            continue
        expected = set(chunk["keys"])
        seen, failed = set(), {}
        for result in client.results(operation):
            key = result.get("key") or result.get("metadata", {}).get("key")
            if key not in expected or key in seen:
                raise ValueError("Batch output has an unknown, missing, or duplicate clip key.")
            seen.add(key)
            try:
                if result.get("error"):
                    code = result["error"].get("code", "unknown")
                    label = {3: "INVALID_ARGUMENT", 7: "PERMISSION_DENIED", 8: "RESOURCE_EXHAUSTED"}.get(code, "ERROR")
                    raise ValueError(f"Gemini per-clip error: {label} (code {code}).")
                import_clip(key, manifest["clips"][key], result.get("response", {}))
            except (ValueError, RuntimeError, OSError) as exc:
                failed[key] = str(exc)
        for key in expected - seen:
            failed[key] = "Missing batch response."
        chunk["failures"] = failed
        chunk["imported"] = not failed
        problems += len(failed)
        save_manifest(path, manifest)
    return problems

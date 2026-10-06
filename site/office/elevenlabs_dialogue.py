"""Content-cached dialogue clips with request-local, short-lived continuity."""

import base64
import hashlib
import json
import os
import math
import tempfile
import time
from pathlib import Path
from email.utils import parsedate_to_datetime

import bugsnag
import requests
from django.conf import settings


class DialogueRequestError(RuntimeError):
    """Report retry decisions without recording vendor bodies or request data."""

    def __init__(self, status, attempts, reason, waited, retry_after):
        message = f"ElevenLabs dialogue failed (HTTP {status})" if status else "ElevenLabs dialogue connection failed"
        super().__init__(message)
        self.retry_details = {
            "http_status": status,
            "attempts": attempts,
            "retry_stop_reason": reason,
            "retry_wait_seconds": waited,
            "retry_after_seconds": retry_after if retry_after is None or math.isfinite(retry_after) else None,
            "retry_after_exceeds_budget": retry_after is not None and retry_after > 30,
        }


class DialogueSession:
    """Never share stitching state between offices or concurrent requests."""

    def __init__(self, provider):
        self.provider = provider
        self.previous = []

    def reset(self):
        self.previous = []

    def speaking_turns(self, lines):
        """Printed line breaks are not changes of speaker."""
        turns = []
        for index, line in enumerate(lines):
            voice = line.get("audio_voice") or self.provider.voice_for_text(line["line_type"], line["content"])
            if not voice:
                raise ValueError("No dialogue voice configured")
            if turns and turns[-1]["voice"] == voice:
                turn = turns[-1]
                start = len(turn["text"]) + 1
                turn["text"] += " " + line["content"]
                turn["ranges"].append((start, len(turn["text"]), index))
            else:
                turns.append({"voice": voice, "text": line["content"], "ranges": [(0, len(line["content"]), index)]})
        return turns

    def chunks(self, lines, normalize):
        chunk = []
        for line in lines:
            words = normalize(line["content"]).split()
            part = []
            for word in words:
                candidate = {**line, "content": " ".join(part + [word])}
                proposed = chunk + [candidate]
                size = sum(len(self.provider.prepare_text(turn["text"])[0]) for turn in self.speaking_turns(proposed))
                if size > 2000:
                    if part:
                        chunk.append({**line, "content": " ".join(part)})
                    if not chunk:
                        raise ValueError("A dialogue word exceeds the request size limit")
                    yield chunk
                    chunk, part = [], []
                    if len(self.provider.prepare_text(word)[0]) > 2000:
                        raise ValueError("A dialogue word exceeds the request size limit")
                part.append(word)
            if part:
                chunk.append({**line, "content": " ".join(part)})
        if chunk:
            yield chunk

    def clip(self, lines):
        """Return path and line-labelled timing; failed clips never abort the office."""
        try:
            return self._clip(lines)
        except Exception as exc:
            self.reset()
            try:
                bugsnag.notify(
                    exc,
                    severity="error",
                    context="office_audio_dialogue",
                    metadata={
                        "audio": {
                            "provider": "elevenlabs",
                            "lines": len(lines),
                            **getattr(exc, "retry_details", {}),
                        }
                    },
                )
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Bugsnag dialogue reporting failed")
            return None, []

    @staticmethod
    def _retry_after(response):
        """Accept RFC 9110 seconds or HTTP-date; never expose the raw header."""
        value = response.headers.get("Retry-After")
        if not isinstance(value, str) or not value.strip():
            return None
        value = value.strip()
        try:
            if value.isascii() and value.isdecimal():
                return float(value)  # Overflow to infinity still means do not retry early.
            else:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    return None
                delay = max(0.0, date.timestamp() - time.time())
            return delay if math.isfinite(delay) else None
        except (TypeError, ValueError, OverflowError):
            return None

    def _request(self, payload, api_key):
        """At most five attempts and 30 seconds of retry sleeps per clip.

        If provider guidance cannot fit the sleep budget, stop instead of
        shortening it and retrying before the provider permits. Request timeouts
        remain separate from this sleep budget.
        """
        max_retries = min(max(self.provider.max_retries, 0), 4)
        waited = 0
        for attempt in range(max_retries + 1):
            status, retry_after = None, None
            try:
                response = requests.post(
                    "https://api.elevenlabs.io/v1/text-to-dialogue/with-timestamps",
                    headers={"xi-api-key": api_key},
                    json=payload,
                    params={"output_format": "mp3_44100_128"},
                    timeout=self.provider.timeout,
                )
                status = response.status_code
                if status < 400:
                    return response
                retry_after = self._retry_after(response)
            except (requests.ConnectionError, requests.Timeout):
                pass
            reason = None
            if status is not None and status not in self.provider._RETRY_STATUSES:
                reason = "non_retryable_status"
            elif attempt == max_retries:
                reason = "attempts_exhausted"
            delay = max(2**attempt, retry_after or 0)
            if reason is None and waited + delay > 30:
                reason = "sleep_budget_exceeded"
            if reason:
                raise DialogueRequestError(status, attempt + 1, reason, waited, retry_after) from None
            time.sleep(delay)
            waited += delay

    def _clip(self, lines):
        turns = []
        prepared = []
        speaking_turns = self.speaking_turns(lines)
        for turn in speaking_turns:
            text = turn["text"]
            submitted, positions = self.provider.prepare_text(text)
            turns.append({"text": submitted, "voice_id": turn["voice"]})
            prepared.append((text, submitted, positions))
        signature = json.dumps(["dialogue-v2", self.provider.cache_signature(), turns], sort_keys=True)
        key = hashlib.sha256(signature.encode()).hexdigest()
        relative = f"elevenlabs/dialogue_{key}.mp3"
        path = Path(settings.MEDIA_ROOT) / relative
        sidecar = path.with_suffix(".dialogue.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        # A process-safe lock avoids paying twice for the same module.
        import fcntl

        with open(str(path) + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if path.exists() and path.stat().st_size and sidecar.exists():
                timing = json.loads(sidecar.read_text())
                self.reset()  # Cached audio cannot supply a fresh conditioning ID.
            else:
                api_key = settings.ELEVENLABS_API_KEY
                if not api_key:
                    raise ValueError("ELEVENLABS_API_KEY is not configured")
                payload = {
                    "inputs": turns,
                    "model_id": self.provider.model,
                    "settings": {"speed": self.provider.speed},
                }
                locators = self.provider.pronunciation_locators()
                if locators:
                    payload["pronunciation_dictionary_locators"] = locators
                recent = [rid for rid, created in self.previous if time.time() - created < 7200]
                if recent:
                    payload["previous_request_ids"] = recent[-3:]
                response = self._request(payload, api_key)
                data = response.json()
                audio = base64.b64decode(data["audio_base64"], validate=True)
                if not audio:
                    raise ValueError("Empty dialogue audio")
                segments = data.get("voice_segments", [])
                if {segment.get("dialogue_input_index") for segment in segments} != set(range(len(turns))):
                    raise ValueError("Dialogue response omitted one or more speaking turns")
                timing = []
                alignment = data.get("alignment") or data.get("normalized_alignment") or {}
                previous_end = 0
                previous_character = 0
                for i, turn in enumerate(speaking_turns):
                    matching = [segment for segment in segments if segment["dialogue_input_index"] == i]
                    first = min(segment["character_start_index"] for segment in matching)
                    last = max(segment["character_end_index"] for segment in matching)
                    if first < previous_character or last <= first:
                        raise ValueError("Dialogue speaking turns overlap or are out of order")
                    previous_character = last
                    sliced = {
                        k: alignment.get(k, [])[first:last]
                        for k in ("characters", "character_start_times_seconds", "character_end_times_seconds")
                    }
                    words = self.provider.original_word_alignment(sliced, *prepared[i])
                    if not words:
                        raise ValueError("Dialogue transcript could not be matched to the prayer")
                    for word in words:
                        start, end = word["start_time"], word["end_time"]
                        if not (
                            math.isfinite(start)
                            and math.isfinite(end)
                            and start >= previous_end - 0.02
                            and end > start
                        ):
                            raise ValueError("Dialogue word timings overlap or are out of order")
                        previous_end = end
                        timing.append({**word, "input_index": i})
                # Publish only complete audio; cache contains no office-specific line IDs.
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(audio)
                    temporary = handle.name
                os.replace(temporary, path)
                sidecar.write_text(json.dumps(timing))
                rid = response.headers.get("request-id")
                if rid:
                    self.previous = [(rid, time.time())]
                else:
                    self.reset()

        def member_index(word):
            return next(
                index
                for begin, finish, index in speaking_turns[word["input_index"]]["ranges"]
                if begin <= word["char_start"] < finish
            )

        labelled = [
            {
                **word,
                "id": lines[member_index(word)]["id"],
                "speaker": self.provider.role_for_line_type(lines[member_index(word)]["line_type"]),
            }
            for word in timing
        ]
        return settings.MEDIA_URL + relative, labelled

"""Content-cached dialogue clips with request-local, short-lived continuity."""

import base64
import hashlib
import json
import os
import math
import tempfile
import time
from pathlib import Path

import bugsnag
import requests
from django.conf import settings


class DialogueTimingError(ValueError):
    """Keep numeric failure evidence without logging prayer text or credentials."""

    def __init__(self, reason, input_index, word_index, start, end, previous_end):
        super().__init__("Dialogue word timings overlap or are out of order")
        self.timing_details = {
            "reason": reason,
            "input_index": input_index,
            "word_index": word_index,
            "start": repr(start),
            "end": repr(end),
            "previous_end": repr(previous_end),
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
                            **getattr(exc, "timing_details", {}),
                        }
                    },
                )
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Bugsnag dialogue reporting failed")
            return None, []

    def _timing(self, alignment, segments, speaking_turns, prepared):
        """Validate one complete alignment in script order; never sort or invent times."""
        timing = []
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
            for word_index, word in enumerate(words):
                start, end = word["start_time"], word["end_time"]
                reason = None
                if not (math.isfinite(start) and math.isfinite(end)):
                    reason = "non_finite"
                elif start < 0 or end <= start:
                    reason = "invalid_duration"
                elif start < previous_end - 0.02:
                    reason = "overlap_or_out_of_order"
                if reason:
                    raise DialogueTimingError(reason, i, word_index, start, end, previous_end)
                previous_end = end
                timing.append({**word, "input_index": i})
        return timing

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
                for attempt in range(self.provider.max_retries + 1):
                    try:
                        response = requests.post(
                            "https://api.elevenlabs.io/v1/text-to-dialogue/with-timestamps",
                            headers={"xi-api-key": api_key},
                            json=payload,
                            params={"output_format": "mp3_44100_128"},
                            timeout=self.provider.timeout,
                        )
                        if response.status_code >= 400:
                            if (
                                response.status_code in self.provider._RETRY_STATUSES
                                and attempt < self.provider.max_retries
                            ):
                                time.sleep(min(2**attempt, 30))
                                continue
                            raise RuntimeError(f"ElevenLabs dialogue failed (HTTP {response.status_code})")
                        break
                    except (requests.ConnectionError, requests.Timeout):
                        if attempt == self.provider.max_retries:
                            raise RuntimeError("ElevenLabs dialogue connection failed") from None
                        time.sleep(min(2**attempt, 30))
                data = response.json()
                audio = base64.b64decode(data["audio_base64"], validate=True)
                if not audio:
                    raise ValueError("Empty dialogue audio")
                segments = data.get("voice_segments", [])
                if {segment.get("dialogue_input_index") for segment in segments} != set(range(len(turns))):
                    raise ValueError("Dialogue response omitted one or more speaking turns")
                alignment = data.get("alignment") or data.get("normalized_alignment") or {}
                try:
                    timing = self._timing(alignment, segments, speaking_turns, prepared)
                except ValueError:
                    normalized = data.get("normalized_alignment") or {}
                    # Voice segment indices cannot safely be reused if normalization
                    # changes the character sequence (numbers, IPA, etc.).
                    if not normalized or normalized.get("characters") != alignment.get("characters"):
                        raise
                    timing = self._timing(normalized, segments, speaking_turns, prepared)
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

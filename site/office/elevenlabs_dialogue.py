"""Content-cached dialogue clips with request-local, short-lived continuity."""

import base64
import hashlib
import json
import os
import math
import tempfile
import time
import subprocess
from pathlib import Path
from email.utils import parsedate_to_datetime

import bugsnag
import requests
from django.conf import settings

from office.audio_builds import AudioNotReady, generation_deferred, release_db_connections

# The decoded MP3 can run slightly shorter than the end the API reports for the
# last segment (encoder padding is a frame or two, about 26 ms each); anything
# beyond this means the audio really was cut off.
SEGMENT_END_TOLERANCE_SECONDS = 0.06


class DialogueTimingError(ValueError):
    """Keep numeric failure evidence without logging prayer text or credentials."""

    def __init__(self, reason, input_index, word_index, start, end, previous_end):
        super().__init__("Dialogue word timings overlap or are out of order")
        self.timing_details = {
            "reason": reason,
            "input_index": input_index,
            "word_index": word_index,
            "start": repr(start)[:64] if type(start) in (int, float) else type(start).__name__,
            "end": repr(end)[:64] if type(end) in (int, float) else type(end).__name__,
            "previous_end": repr(previous_end)[:64],
        }


class DialogueTimingMetadataError(ValueError):
    """Recognize unusable timing arrays without accepting transcript mismatches."""

    def __init__(self, reason):
        super().__init__("Dialogue character timing metadata is unavailable or inconsistent")
        self.timing_details = {"reason": reason}


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
        self.highlighting_available = True

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
        """Return audio/timing, or a failure sentinel the caller must handle explicitly."""
        self.highlighting_available = True
        try:
            return self._clip(lines)
        except AudioNotReady:
            raise
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
                            **getattr(exc, "retry_details", {}),
                            **getattr(exc, "alignment_details", {}),
                        }
                    },
                )
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Bugsnag dialogue reporting failed")
            return None, []

    def _timing(self, alignment, segments, speaking_turns, prepared):
        """Validate one complete alignment in script order; never sort or invent times."""
        characters = alignment.get("characters")
        if (
            not isinstance(characters, list)
            or not characters
            or any(not isinstance(character, str) or len(character) != 1 for character in characters)
        ):
            raise ValueError("Dialogue character structure is unavailable or invalid")
        starts = alignment.get("character_start_times_seconds")
        ends = alignment.get("character_end_times_seconds")
        if not isinstance(starts, list) or not isinstance(ends, list) or not starts or not ends:
            raise DialogueTimingMetadataError("unavailable_character_timing")
        if len(starts) != len(characters) or len(ends) != len(characters):
            raise DialogueTimingMetadataError("unequal_character_timing_lengths")
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
                if type(start) not in (int, float) or type(end) not in (int, float):
                    reason = "non_numeric"
                elif not (math.isfinite(start) and math.isfinite(end)):
                    reason = "non_finite"
                elif start < 0 or end <= start:
                    reason = "invalid_duration"
                elif start < previous_end - 0.02:
                    reason = "overlap_or_out_of_order"
                if reason:
                    error = DialogueTimingError(reason, i, word_index, start, end, previous_end)
                    aligned = "".join(sliced["characters"])
                    if aligned == turn["text"]:
                        indices = range(word["char_start"], word["char_end"])
                    else:
                        indices = [
                            j
                            for j, position in enumerate(prepared[i][2])
                            if position is not None and word["char_start"] <= position < word["char_end"]
                        ]
                    intervals = [
                        (sliced["character_start_times_seconds"][j], sliced["character_end_times_seconds"][j])
                        for j in indices
                        if j < len(sliced["character_start_times_seconds"])
                    ]
                    numeric = [(a, b) for a, b in intervals if type(a) in (int, float) and type(b) in (int, float)]
                    error.timing_details.update(
                        character_interval_count=len(intervals),
                        positive_character_intervals=sum(b > a for a, b in numeric),
                        zero_character_intervals=sum(b == a for a, b in numeric),
                    )
                    raise error
                previous_end = end
                timing.append({**word, "input_index": i})
        return timing

    @staticmethod
    def _alignment_details(error, alignment):
        details = {"reason": "unmatched_transcript", **getattr(error, "timing_details", {})}
        for key in ("characters", "character_start_times_seconds", "character_end_times_seconds"):
            value = alignment.get(key)
            details[key + "_count"] = len(value) if isinstance(value, list) else 0
        return details

    @staticmethod
    def _fallback_segment_end(alignment, segments, speaking_turns, prepared):
        """Require complete ordered script/voice metadata independently of word times."""
        characters = alignment.get("characters")
        if not isinstance(characters, list) or not characters or len(characters) > 10000:
            raise ValueError("invalid_character_structure")
        if any(not isinstance(c, str) or len(c) != 1 for c in characters):
            raise ValueError("invalid_character_structure")
        if not isinstance(segments, list) or not segments or len(segments) > 200:
            raise ValueError("invalid_segment_structure")
        previous_character, previous_end, previous_input = 0, 0, -1
        grouped = [[] for turn in speaking_turns]
        for segment in segments:
            index = segment.get("dialogue_input_index")
            first, last = segment.get("character_start_index"), segment.get("character_end_index")
            start, end = segment.get("start_time_seconds"), segment.get("end_time_seconds")
            if type(index) is not int or not 0 <= index < len(speaking_turns) or index < previous_input:
                raise ValueError("invalid_turn_order")
            if segment.get("voice_id") != speaking_turns[index]["voice"]:
                raise ValueError("mismatched_voice")
            if (
                type(first) is not int
                or type(last) is not int
                or not previous_character <= first < last <= len(characters)
            ):
                raise ValueError("invalid_character_bounds")
            if "".join(characters[previous_character:first]).strip():
                raise ValueError("unassigned_transcript")
            if any(type(t) not in (int, float) or not math.isfinite(t) for t in (start, end)):
                raise ValueError("invalid_segment_times")
            if start < previous_end or end <= start:
                raise ValueError("invalid_segment_times")
            grouped[index].append((first, last))
            previous_character, previous_end, previous_input = last, end, index
        if "".join(characters[previous_character:]).strip():
            raise ValueError("unassigned_transcript")
        for index, bounds in enumerate(grouped):
            if not bounds:
                raise ValueError("missing_turn")
            text = "".join(characters[bounds[0][0] : bounds[-1][1]])
            if text not in (speaking_turns[index]["text"], prepared[index][1]):
                raise ValueError("mismatched_transcript")
        return previous_end

    @staticmethod
    def _decoded_duration(audio, directory):
        """Fully decode bounded MP3 bytes; header duration alone misses cut files."""
        if len(audio) > 16 * 1024 * 1024:
            raise ValueError("audio_too_large")
        with tempfile.TemporaryDirectory(prefix="dialogue-check-", dir=directory) as temp:
            source, decoded = Path(temp) / "source.mp3", Path(temp) / "decoded.pcm"
            source.write_bytes(audio)
            limit = 16000 * 2 * 600
            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-nostdin",
                        "-v",
                        "error",
                        "-xerror",
                        "-err_detect",
                        "explode",
                        "-f",
                        "mp3",
                        "-i",
                        str(source),
                        "-map",
                        "0:a:0",
                        "-vn",
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        "-f",
                        "s16le",
                        "-fs",
                        str(limit),
                        str(decoded),
                    ],
                    capture_output=True,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired):
                raise ValueError("audio_decode_failed") from None
            size = decoded.stat().st_size if decoded.exists() else 0
            if result.returncode or not 0 < size < limit:
                raise ValueError("audio_decode_failed")
            return size / 32000

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
            except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError):
                # A reset mid-body raises ChunkedEncodingError, which is not a
                # ConnectionError but is the same transient failure.
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
        if generation_deferred() and not (path.exists() and path.stat().st_size and sidecar.exists()):
            # Checked before the lock: a web request must not wait on a build.
            raise AudioNotReady()
        path.parent.mkdir(parents=True, exist_ok=True)
        # A process-safe lock avoids paying twice for the same module.
        import fcntl

        with open(str(path) + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if path.exists() and path.stat().st_size and sidecar.exists():
                cached = json.loads(sidecar.read_text())
                if isinstance(cached, dict):
                    if (
                        cached.get("version") != 1
                        or cached.get("highlighting_available") is not False
                        or cached.get("word_timing") != []
                    ):
                        raise ValueError("Invalid dialogue fallback cache")
                    if hashlib.sha256(path.read_bytes()).hexdigest() != cached.get("audio_sha256"):
                        raise ValueError("Dialogue fallback cache audio changed")
                    duration = cached.get("decoded_duration")
                    if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
                        raise ValueError("Invalid dialogue fallback cache duration")
                    timing = []
                    self.highlighting_available = False
                elif isinstance(cached, list):
                    timing = cached
                else:
                    raise ValueError("Invalid dialogue cache")
                self.reset()  # Cached audio cannot supply a fresh conditioning ID.
            else:
                if path.exists() and path.stat().st_size:
                    raise ValueError("Dialogue cache metadata is unavailable; audio retained")
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
                release_db_connections()
                response = self._request(payload, api_key)
                data = response.json()
                audio = base64.b64decode(data["audio_base64"], validate=True)
                if not audio:
                    raise ValueError("Empty dialogue audio")
                segments = data.get("voice_segments", [])
                if {segment.get("dialogue_input_index") for segment in segments} != set(range(len(turns))):
                    raise ValueError("Dialogue response omitted one or more speaking turns")
                alignment = data.get("alignment") or data.get("normalized_alignment") or {}
                cache_data = None
                try:
                    timing = self._timing(alignment, segments, speaking_turns, prepared)
                except ValueError as raw_error:
                    diagnostics = {"raw_alignment": self._alignment_details(raw_error, alignment)}
                    normalized = data.get("normalized_alignment") or {}
                    timing_error = raw_error
                    try:
                        if not normalized or normalized.get("characters") != alignment.get("characters"):
                            raise ValueError("Normalized character sequence cannot reuse segment offsets")
                        timing = self._timing(normalized, segments, speaking_turns, prepared)
                    except ValueError as normalized_error:
                        diagnostics["normalized_alignment"] = self._alignment_details(normalized_error, normalized)
                        if isinstance(normalized_error, (DialogueTimingError, DialogueTimingMetadataError)):
                            timing_error = normalized_error
                        try:
                            # A transcript/index mismatch is not merely failed word timing.
                            if not isinstance(raw_error, (DialogueTimingError, DialogueTimingMetadataError)):
                                raise ValueError("not_word_timing_failure")
                            segment_end = self._fallback_segment_end(alignment, segments, speaking_turns, prepared)
                            duration = self._decoded_duration(audio, path.parent)
                            diagnostics["last_segment_end"] = segment_end
                            diagnostics["decoded_duration"] = duration
                            if segment_end > duration + SEGMENT_END_TOLERANCE_SECONDS:
                                raise ValueError("audio_shorter_than_segments")
                        except ValueError as rejected:
                            diagnostics["fallback_rejected"] = str(rejected)
                            timing_error.alignment_details = diagnostics
                            raise timing_error from None
                        timing = []
                        self.highlighting_available = False
                        cache_data = {
                            "version": 1,
                            "highlighting_available": False,
                            "word_timing": [],
                            "audio_sha256": hashlib.sha256(audio).hexdigest(),
                            "decoded_duration": duration,
                        }
                        diagnostics["playback_only"] = True
                        diagnostics["decoded_duration"] = duration
                        try:
                            bugsnag.notify(
                                timing_error,
                                severity="warning",
                                context="office_audio_dialogue",
                                metadata={"audio": {"provider": "elevenlabs", "lines": len(lines), **diagnostics}},
                            )
                        except Exception:
                            pass  # Telemetry must not discard validated playback.
                # Publish only complete audio; cache contains no office-specific line IDs.
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(audio)
                    temporary = handle.name
                # mkstemp-style files are 0600; the web workers must read what a
                # warm-up or management command (another user) published.
                os.chmod(temporary, 0o644)
                os.replace(temporary, path)
                with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
                    json.dump(cache_data if cache_data is not None else timing, handle)
                    temporary_metadata = handle.name
                os.chmod(temporary_metadata, 0o644)
                os.replace(temporary_metadata, sidecar)
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

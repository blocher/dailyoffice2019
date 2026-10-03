"""Cached second-pass Gemini transcription, matched to the original TTS text."""

import base64
import fcntl
import json
import logging
import math
import os
import re
import tempfile
import time
from difflib import SequenceMatcher
from pathlib import Path

from django.conf import settings
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)
TOKEN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


class AlignmentValidationError(ValueError):
    """Safe, local validation reason containing no vendor response or credentials."""


def canonical(word):
    word = word.casefold().replace("’", "'")
    return "o" if word == "oh" else word


def interpolate_short_gaps(text, words):
    """Estimate up to two interior words without moving measured anchors.

    Only bridge short, punctuation-free gaps within a clip. Estimates are
    explicitly marked and can be applied to cached timings without another API
    request. Longer gaps and leading/trailing omissions remain unaligned.
    """
    tokens = list(TOKEN.finditer(text))
    indices = {(token.start(), token.end()): i for i, token in enumerate(tokens)}
    result = []
    for left, right in zip(words, words[1:]):
        result.append(left)
        left_index = indices.get((left.get("char_start"), left.get("char_end")))
        right_index = indices.get((right.get("char_start"), right.get("char_end")))
        if left_index is None or right_index is None:
            continue
        missing = right_index - left_index - 1
        if missing not in (1, 2):
            continue
        start, end = left["end_time"], right["start_time"]
        gap = end - start
        between = text[left["char_end"] : right["char_start"]]
        if not math.isfinite(gap) or not 0.08 * missing <= gap <= 0.8 * missing:
            continue
        if re.search(r"[,.;:!?—–\n]", between):
            continue
        omitted = tokens[left_index + 1 : right_index]
        total_weight = sum(len(token[0]) for token in omitted)
        elapsed_weight = 0
        for token in omitted:
            word_start = start + gap * elapsed_weight / total_weight
            elapsed_weight += len(token[0])
            result.append(
                {
                    "word": token[0],
                    "char_start": token.start(),
                    "char_end": token.end(),
                    "start_time": word_start,
                    "end_time": start + gap * elapsed_weight / total_weight,
                    "estimated": True,
                }
            )
    if words:
        result.append(words[-1])
    return result


def match_words(text, annotations, duration):
    source = list(TOKEN.finditer(text))
    recognized = []
    previous_end = 0
    for item in annotations:
        if item.get("type") != "word_info":
            continue
        start = float(str(item["start_offset"]).removesuffix("s"))
        end = float(str(item["end_offset"]).removesuffix("s"))
        if (
            not all(math.isfinite(v) for v in (start, end))
            or not 0 <= start <= end <= duration + 0.1
            or start < previous_end
        ):
            raise AlignmentValidationError("Invalid transcription timestamps")
        tokens = TOKEN.findall(item.get("text", ""))
        if len(tokens) != 1:
            raise AlignmentValidationError("Expected one word per timestamp")
        recognized.append((tokens[0], start, end))
        previous_end = end
    matcher = SequenceMatcher(
        None, [canonical(m[0]) for m in source], [canonical(w[0]) for w in recognized], autojunk=False
    )
    words = []
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            token = source[block.a + offset]
            _, start, end = recognized[block.b + offset]
            words.append(
                {
                    "word": token[0],
                    "char_start": token.start(),
                    "char_end": token.end(),
                    "start_time": start,
                    "end_time": end,
                }
            )
    # Check transcript confidence before adding any estimated timings.
    if not source or len(words) / max(len(source), len(recognized), 1) < 0.9:
        raise AlignmentValidationError("Transcription does not match the prayer closely enough")
    return interpolate_short_gaps(text, words)


def align_clip(provider, text, file_path):
    """Align the final MP3 once; failures preserve audio and retry after an hour.

    Locking also prevents concurrent office requests from duplicating paid work.
    The cache is separate from synthesis: enabling alignment never changes voices.
    """
    if not getattr(settings, "GEMINI_TTS_ALIGNMENT", True):
        return []
    path = Path(file_path)
    cache = Path(str(path) + ".gemini-alignment.json")
    with open(str(path) + ".alignment.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        signature = [
            path.stat().st_size,
            path.stat().st_mtime_ns,
            text,
            getattr(settings, "GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe"),
            1,
        ]
        try:
            saved = json.loads(cache.read_text())
            if saved.get("signature") == signature:
                if saved.get("words") or time.time() < saved.get("retry_after", 0):
                    return saved.get("words", [])
        except (OSError, ValueError):
            pass
        words = []
        try:
            if path.stat().st_size > 18 * 1024 * 1024:
                raise ValueError("Clip exceeds inline transcription size limit")
            payload = {
                "model": signature[3],
                "store": False,
                "input": [
                    {"type": "audio", "mime_type": "audio/mp3", "data": base64.b64encode(path.read_bytes()).decode()}
                ],
                "generation_config": {
                    "transcription_config": {
                        "language_codes": ["en-US"],
                        "mode": {"type": "verbatim", "timestamp_granularities": ["word"]},
                    }
                },
            }
            response = provider._request(payload, settings.GEMINI_API_KEY).json()
            annotations = [
                a
                for step in response.get("steps", [])
                if step.get("type") == "model_output"
                for part in step.get("content", [])
                if part.get("type") == "text"
                for a in part.get("annotations", [])
            ]
            words = match_words(text, annotations, MP3(file_path).info.length)
        except Exception as exc:
            logger.warning(
                "Gemini word alignment unavailable (%s); using estimated line highlighting.",
                str(exc) if isinstance(exc, AlignmentValidationError) else type(exc).__name__,
            )
        data = {"signature": signature, "words": words, "retry_after": time.time() + 3600 if not words else 0}
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
            json.dump(data, handle)
            temporary = handle.name
        os.replace(temporary, cache)
        return words

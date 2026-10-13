"""Build and validate the single concatenated office audio track.

Each office + settings combination is spoken as one mp3 assembled by ffmpeg
from many cached clips (see ``GenericDailyOfficeSerializer.get_single_track``).
The file name is a hash of the concat list, so once a file exists at that path
it is served to everyone, cached by Cloudflare and browsers, and never rebuilt.

That makes a partial file very costly. ffmpeg used to write straight to the
final path, so a request arriving mid-encode, or a worker killed mid-encode
(timeout, deploy restart), left a truncated track that played part of the
office and then stopped. The helpers here:

* build into a unique temporary file and ``os.replace`` it into place only after
  ffmpeg succeeds and the result decodes, so the final path only ever holds a
  complete track;
* serialise builds of one track with an exclusive ``fcntl`` lock, so concurrent
  first requests wait for a single encode instead of racing or serving it half
  written;
* reject an existing track whose duration is missing (an unfinalised header,
  which is what an interrupted encode leaves) or far from the expected length,
  so tracks truncated before this fix are rebuilt on the next request.

Each completed build records its duration in the track's lock file. A track
that matches its own build record is accepted even if it is outside the
tolerance, so an unexpected length is rebuilt once rather than on every request.
"""

import fcntl
import logging
import os
import re
import subprocess
import uuid

from mutagen.mp3 import MP3

from office.audio_builds import ensure_generation_allowed

logger = logging.getLogger(__name__)

# How far a combined track may differ from the sum of its clip lengths and
# still count as complete. The concat re-encode drifts by a few frames per clip
# (which ``rescale_segments`` corrects); measured on real offices that is about
# 0.03 s over 15 minutes, so 2% leaves a wide margin while still catching a
# track that is missing its closing minutes. The floor keeps very short tracks
# from failing on frame rounding alone.
DURATION_TOLERANCE = 0.02
MIN_DURATION_TOLERANCE_SECONDS = 1.0

# Combined tracks are named ``<uuid5 of the concat list>.mp3``. The build's
# scratch files sit beside the track and start with its name, so a cleanup can
# map them back to it: ``<track>.lock`` (lock and build record), and
# ``<track>.<token>.part`` / ``<track>.<token>.txt`` while encoding.
# ``<track>.txt`` is the concat list name used before builds were atomic.
LOCK_SUFFIX = ".lock"
_TRACK = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.mp3"
TRACK_NAME_RE = re.compile(rf"^{_TRACK}$")
TRACK_LOCK_RE = re.compile(rf"^{_TRACK}\.lock$")
TEMP_AUDIO_RE = re.compile(rf"^{_TRACK}\.[0-9a-f]{{32}}\.part$")
CONCAT_LIST_RE = re.compile(rf"^{_TRACK}(?:\.[0-9a-f]{{32}})?\.txt$")


def mp3_duration(path):
    """Decoded length in seconds, or 0.0 when the file is missing or unreadable.

    An encode interrupted before ffmpeg finalises the mp3 header reports 0.0,
    which is how a truncated combined track is recognised.
    """
    try:
        return float(MP3(path).info.length or 0.0)
    except Exception:
        return 0.0


def duration_matches(duration, expected_duration):
    """True when ``duration`` is positive and close enough to ``expected_duration``."""
    if not duration or duration <= 0:
        return False
    if not expected_duration or expected_duration <= 0:
        return True
    tolerance = max(expected_duration * DURATION_TOLERANCE, MIN_DURATION_TOLERANCE_SECONDS)
    return abs(duration - expected_duration) <= tolerance


def recorded_duration(file_path):
    """Duration written by the last completed build of ``file_path``, or None."""
    try:
        with open(f"{file_path}{LOCK_SUFFIX}") as record:
            return float(record.read().strip() or "nan")
    except (OSError, ValueError):
        return None


def valid_track_duration(file_path, expected_duration):
    """Duration of a complete track at ``file_path``, or 0.0 if it is missing or truncated."""
    if not os.path.isfile(file_path):
        return 0.0
    duration = mp3_duration(file_path)
    if duration_matches(duration, expected_duration):
        return duration
    recorded = recorded_duration(file_path)
    if duration > 0 and recorded is not None and abs(recorded - duration) < 0.01:
        return duration
    return 0.0


def ensure_combined_track(concat_paths, file_path, expected_duration, sample_rate):
    """Return the duration of a complete combined track at ``file_path``.

    Reuses a valid existing file, otherwise (re)builds it. Returns 0.0 when no
    complete track could be produced; the caller should then hide the player.
    """
    # The final path is only ever replaced atomically, so a valid file can be
    # used without waiting on the lock.
    duration = valid_track_duration(file_path, expected_duration)
    if duration:
        return duration
    # Web requests never encode; they defer the build (office/audio_builds.py).
    ensure_generation_allowed()

    with open(f"{file_path}{LOCK_SUFFIX}", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Another request may have finished the build while this one waited.
        duration = valid_track_duration(file_path, expected_duration)
        if duration:
            return duration
        if os.path.exists(file_path):
            logger.warning(
                "Rebuilding truncated combined audio track %s (%.2fs, expected %.2fs)",
                file_path,
                mp3_duration(file_path),
                expected_duration,
            )
            _remove(file_path)
        duration = build_combined_track(concat_paths, file_path, expected_duration, sample_rate)
        lock.truncate(0)
        if duration:
            lock.write(f"{duration:.3f}\n")
        lock.flush()
        return duration


def build_combined_track(concat_paths, file_path, expected_duration, sample_rate):
    """Encode ``concat_paths`` into ``file_path`` atomically; return its duration or 0.0.

    Callers must hold the track's lock (see ``ensure_combined_track``).
    """
    token = uuid.uuid4().hex
    concat_list = f"{file_path}.{token}.txt"
    temp_path = f"{file_path}.{token}.part"
    try:
        with open(concat_list, "w") as f:
            for concat_path in concat_paths:
                f.write(f"file '{concat_path}'\n")

        # Re-encode (rather than `-c copy`) to a single constant-bitrate mp3 with
        # a proper header. The per-clip sources vary in bitrate (gpt-4o-mini-tts
        # ~128k vs the silence clips), and a stream-copied VBR mp3 with no Xing
        # header is not reliably seekable in browsers (seeks snap to the start).
        # A uniform CBR encode restores accurate time-based seeking. The format
        # is explicit because the temporary name has no .mp3 extension.
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list,
            "-c:a",
            "libmp3lame",
            "-b:a",
            "160k",
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-f",
            "mp3",
            temp_path,
        ]
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(
                "ffmpeg failed building %s with return code %s: %s",
                file_path,
                result.returncode,
                (result.stderr or "")[-2000:],
            )
            return 0.0

        duration = mp3_duration(temp_path)
        if duration <= 0:
            logger.error("ffmpeg produced an unreadable combined audio track for %s", file_path)
            return 0.0
        if not duration_matches(duration, expected_duration):
            # ffmpeg finished, so the file is complete; the expectation is what
            # is off. Keep it (the timeline is rescaled to it) but make it visible.
            logger.warning(
                "Combined audio track %s is %.2fs, expected %.2fs",
                file_path,
                duration,
                expected_duration,
            )
        os.replace(temp_path, file_path)
        return duration
    finally:
        _remove(temp_path)
        _remove(concat_list)


def _remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

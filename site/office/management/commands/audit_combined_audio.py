import fcntl
import os
import re
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from mutagen.mp3 import MP3, BitrateMode

from office.api.views.tts import get_tts_provider, provider_names
from office.combined_track import (
    CONCAT_LIST_RE,
    LOCK_SUFFIX,
    TEMP_AUDIO_RE,
    TRACK_LOCK_RE,
    TRACK_NAME_RE,
    duration_matches,
    mp3_duration,
)
from office.models import AudioClip


class Command(BaseCommand):
    help = (
        "Report combined office audio tracks that are truncated or unreadable, plus leftover "
        "build files (temporary mp3s, concat lists, orphaned locks). Dry run unless --delete is given. "
        "A deleted track is rebuilt the next time its office is requested."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the problem tracks and stale build files. Without this, only report them.",
        )
        parser.add_argument(
            "--min-age-minutes",
            type=int,
            default=60,
            help="Leave build files younger than this alone; a build may still be using them (default: 60).",
        )

    def _scan_dirs(self, media_root):
        """MEDIA_ROOT plus each TTS provider media subfolder (e.g. gemini/, elevenlabs/)."""
        dirs = [media_root]
        for name in provider_names():
            path = os.path.join(media_root, get_tts_provider(name).media_subdir)
            if path not in dirs and os.path.isdir(path):
                dirs.append(path)
        return dirs

    def handle(self, *args, **options):
        delete = options["delete"]
        cutoff = time.time() - options["min_age_minutes"] * 60
        media_root = settings.MEDIA_ROOT
        if not os.path.isdir(media_root):
            self.stdout.write(self.style.ERROR(f"Media root does not exist: {media_root}"))
            return

        self.stdout.write(
            self.style.ERROR("DELETE mode: problem files will be removed.")
            if delete
            else self.style.WARNING("Dry run: nothing will be deleted. Pass --delete to remove problem files.")
        )
        # Combined tracks and individual clips share the <uuid>.mp3 naming;
        # clips are the ones tracked in AudioClip.
        clip_names = set(AudioClip.objects.values_list("filename", flat=True))

        tracks = bad_tracks = stale_files = removed = 0
        for directory in self._scan_dirs(media_root):
            for name in sorted(os.listdir(directory)):
                path = os.path.join(directory, name)
                relative = os.path.relpath(path, media_root)
                if not os.path.isfile(path):
                    continue

                if self._is_build_file(path, name) and os.path.getmtime(path) < cutoff:
                    stale_files += 1
                    self.stdout.write(f"Stale build file: {relative}")
                    if delete and self._remove_build_file(path, name):
                        removed += 1
                    continue

                if not TRACK_NAME_RE.match(name) or relative in clip_names:
                    continue
                tracks += 1
                problem = self._track_problem(path)
                if not problem:
                    continue
                bad_tracks += 1
                self.stdout.write(self.style.WARNING(f"Bad combined track: {relative} ({problem})"))
                if delete and self._remove_track(path):
                    removed += 1

        self.stdout.write("")
        self.stdout.write(f"Combined tracks checked: {tracks}")
        self.stdout.write(f"Truncated or unreadable tracks: {bad_tracks}")
        self.stdout.write(f"Stale build files: {stale_files}")
        if delete:
            self.stdout.write(self.style.SUCCESS(f"Removed: {removed}"))
        elif bad_tracks or stale_files:
            self.stdout.write(self.style.WARNING("Dry run. Re-run with --delete to remove these files."))

    @staticmethod
    def _is_build_file(path, name):
        if TEMP_AUDIO_RE.search(name) or CONCAT_LIST_RE.search(name):
            return True
        # A lock whose track is gone has nothing left to protect.
        return bool(TRACK_LOCK_RE.match(name)) and not os.path.exists(path[: -len(LOCK_SUFFIX)])

    def _track_problem(self, path):
        """Why ``path`` is not a complete track, or None when it looks complete."""
        duration = mp3_duration(path)
        if duration <= 0:
            return "no readable duration; the encode was interrupted"

        # A list left behind by an interrupted build (before the atomic build
        # path) gives the length the track should have had.
        concat_list = f"{path}.txt"
        if os.path.isfile(concat_list):
            expected = self._concat_list_duration(concat_list)
            if expected and not duration_matches(duration, expected):
                return f"{duration:.1f}s of an expected {expected:.1f}s"

        # Combined tracks are constant bitrate, so the bytes on disk should
        # account for the whole length the header claims.
        try:
            info = MP3(path).info
        except Exception:
            return "unreadable"
        if info.bitrate and info.bitrate_mode == BitrateMode.CBR:
            on_disk = os.path.getsize(path) * 8 / info.bitrate
            if not duration_matches(on_disk, duration) and on_disk < duration:
                return f"header says {duration:.1f}s but only {on_disk:.1f}s of audio is on disk"
        return None

    @staticmethod
    def _concat_list_duration(concat_list):
        try:
            with open(concat_list) as f:
                paths = re.findall(r"^file '(.*)'$", f.read(), flags=re.MULTILINE)
        except OSError:
            return 0.0
        if not paths or not all(os.path.isfile(clip) for clip in paths):
            return 0.0
        return sum(mp3_duration(clip) for clip in paths)

    def _remove_track(self, path):
        """Delete a bad track (and its build record) unless a build of it is running right now."""
        lock_path = f"{path}{LOCK_SUFFIX}"
        with open(lock_path, "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.stdout.write(f"  Skipped (being rebuilt now): {path}")
                return False
            # Re-check under the lock: a request may have just replaced it.
            if not self._track_problem(path):
                return False
            for leftover in (path, f"{path}.txt", lock_path):
                if os.path.isfile(leftover):
                    os.remove(leftover)
        self.stdout.write(self.style.SUCCESS(f"  Deleted: {path}"))
        return True

    def _remove_build_file(self, path, name):
        if name.endswith(LOCK_SUFFIX):
            with open(path, "a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return False
                os.remove(path)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                return False
        self.stdout.write(self.style.SUCCESS(f"  Deleted: {path}"))
        return True

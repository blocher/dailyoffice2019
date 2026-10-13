import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from io import StringIO
from pathlib import Path
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from office import combined_track
from office.audio_builds import AudioNotReady, deferred_generation
from office.models import AudioClip


def fake_mp3(durations):
    """Patch target for MP3: look up a duration by path; unknown paths are unreadable."""

    def build(path):
        if path not in durations:
            raise ValueError("can't sync to MPEG frame")
        result = MagicMock()
        result.info.length = durations[path]
        return result

    return build


class DurationMatchesTests(SimpleTestCase):
    def test_zero_or_missing_duration_is_never_complete(self):
        for duration in (0, 0.0, None, -1):
            with self.subTest(duration=duration):
                self.assertFalse(combined_track.duration_matches(duration, 900))

    def test_re_encode_drift_is_accepted(self):
        # Measured drift on real offices is a few hundredths of a second.
        self.assertTrue(combined_track.duration_matches(907.584, 907.56))
        self.assertTrue(combined_track.duration_matches(900 * 0.985, 900))
        self.assertTrue(combined_track.duration_matches(900 * 1.015, 900))

    def test_missing_minutes_are_rejected(self):
        self.assertFalse(combined_track.duration_matches(2451, 2618))
        self.assertFalse(combined_track.duration_matches(900 * 0.97, 900))
        self.assertFalse(combined_track.duration_matches(900 * 1.03, 900))

    def test_short_tracks_allow_a_second_of_rounding(self):
        self.assertTrue(combined_track.duration_matches(4.0, 4.35))
        self.assertFalse(combined_track.duration_matches(3.0, 4.35))

    def test_unknown_expectation_only_requires_a_duration(self):
        self.assertTrue(combined_track.duration_matches(12.0, 0))


class EnsureCombinedTrackTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.final = str(self.root / "track.mp3")
        self.durations = {}
        patcher = patch.object(combined_track, "MP3", side_effect=fake_mp3(self.durations))
        patcher.start()
        self.addCleanup(patcher.stop)

    def ensure(self, run, expected=100.0):
        with patch.object(combined_track.subprocess, "run", side_effect=run) as mock_run:
            duration = combined_track.ensure_combined_track(["/a.mp3", "/b.mp3"], self.final, expected, 44100)
        return duration, mock_run

    def leftovers(self):
        return sorted(p.name for p in self.root.iterdir() if p.name not in {"track.mp3", "track.mp3.lock"})

    def ffmpeg_writing(self, length, returncode=0, content=b"audio"):
        def run(command, **_kwargs):
            output = command[-1]
            # Output goes to a temporary name, never straight to the final path.
            self.assertNotEqual(output, self.final)
            self.assertTrue(output.startswith(self.final + "."))
            with open(output, "wb") as f:
                f.write(content)
            concat_list = command[command.index("-i") + 1]
            with open(concat_list) as f:
                self.assertEqual(f.read(), "file '/a.mp3'\nfile '/b.mp3'\n")
            if length is not None:
                self.durations[output] = length
            return MagicMock(returncode=returncode, stderr="boom" if returncode else "")

        return run

    def test_builds_atomically_and_cleans_up(self):
        duration, run = self.ensure(self.ffmpeg_writing(99.9))
        self.assertEqual(duration, 99.9)
        run.assert_called_once()
        self.assertEqual(Path(self.final).read_bytes(), b"audio")
        self.assertEqual(self.leftovers(), [])
        self.assertEqual(combined_track.recorded_duration(self.final), 99.9)

    def test_failed_encode_leaves_nothing_at_the_final_path(self):
        duration, _run = self.ensure(self.ffmpeg_writing(50.0, returncode=1, content=b"half"))
        self.assertEqual(duration, 0.0)
        self.assertFalse(os.path.exists(self.final))
        self.assertEqual(self.leftovers(), [])

    def test_unreadable_output_is_not_published(self):
        duration, _run = self.ensure(self.ffmpeg_writing(None))
        self.assertEqual(duration, 0.0)
        self.assertFalse(os.path.exists(self.final))
        self.assertEqual(self.leftovers(), [])

    def test_exception_during_encode_cleans_up_temporary_files(self):
        def run(command, **_kwargs):
            Path(command[-1]).write_bytes(b"partial")
            raise KeyboardInterrupt  # e.g. the worker being stopped mid-encode

        with self.assertRaises(KeyboardInterrupt):
            self.ensure(run)
        self.assertFalse(os.path.exists(self.final))
        self.assertEqual(self.leftovers(), [])

    def test_complete_existing_track_is_reused_without_encoding(self):
        Path(self.final).write_bytes(b"done")
        self.durations[self.final] = 100.4
        duration, run = self.ensure(self.ffmpeg_writing(1.0))
        self.assertEqual(duration, 100.4)
        run.assert_not_called()

    def test_truncated_existing_track_is_rebuilt(self):
        for truncated_length in (0.0, 61.0):
            with self.subTest(truncated_length=truncated_length):
                Path(self.final).write_bytes(b"truncated")
                self.durations[self.final] = truncated_length
                duration, run = self.ensure(self.ffmpeg_writing(100.1))
                run.assert_called_once()
                self.assertEqual(duration, 100.1)
                self.assertEqual(Path(self.final).read_bytes(), b"audio")

    def test_truncated_track_is_removed_even_if_the_rebuild_fails(self):
        Path(self.final).write_bytes(b"truncated")
        self.durations[self.final] = 0.0
        duration, _run = self.ensure(self.ffmpeg_writing(None, returncode=1))
        self.assertEqual(duration, 0.0)
        self.assertFalse(os.path.exists(self.final))

    def test_web_request_defers_a_missing_track_but_serves_a_complete_one(self):
        with deferred_generation():
            with self.assertRaises(AudioNotReady):
                self.ensure(self.ffmpeg_writing(100.0))
            self.assertFalse(os.path.exists(self.final))
            Path(self.final).write_bytes(b"done")
            self.durations[self.final] = 100.2
            duration, run = self.ensure(self.ffmpeg_writing(1.0))
        self.assertEqual(duration, 100.2)
        run.assert_not_called()

    def test_complete_build_with_unexpected_length_is_not_rebuilt_every_request(self):
        # ffmpeg succeeded, so the expectation (not the file) is off: serve it,
        # and remember it so later requests do not re-encode the office again.
        duration, run = self.ensure(self.ffmpeg_writing(80.0))
        self.assertEqual(duration, 80.0)
        self.durations[self.final] = 80.0
        duration, run = self.ensure(self.ffmpeg_writing(80.0))
        self.assertEqual(duration, 80.0)
        run.assert_not_called()

    def test_concurrent_requests_share_one_build(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def slow_run(command, **_kwargs):
            calls.append(command)
            Path(command[-1]).write_bytes(b"part")
            started.set()
            release.wait(5)
            Path(command[-1]).write_bytes(b"audio")
            # The fake MP3 is keyed by path: describe the file before and after os.replace.
            self.durations[command[-1]] = 100.0
            self.durations[self.final] = 100.0
            return MagicMock(returncode=0, stderr="")

        results = []

        def request():
            results.append(combined_track.ensure_combined_track(["/a.mp3"], self.final, 100.0, 44100))

        with patch.object(combined_track.subprocess, "run", side_effect=slow_run):
            first = threading.Thread(target=request)
            first.start()
            self.assertTrue(started.wait(5))
            second = threading.Thread(target=request)
            second.start()
            # While the first encode runs, nothing is published at the final path.
            time.sleep(0.2)
            self.assertFalse(os.path.exists(self.final))
            self.assertEqual(results, [])
            release.set()
            first.join(5)
            second.join(5)

        self.assertEqual(len(calls), 1)
        self.assertEqual(results, [100.0, 100.0])


@skipUnless(shutil.which("ffmpeg"), "ffmpeg is required")
class RealFfmpegCombinedTrackTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def tone(self, name, seconds):
        path = str(self.root / name)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={seconds}:sample_rate=24000",
                "-ac",
                "1",
                "-b:a",
                "64k",
                path,
            ],
            check=True,
        )
        return path

    def test_builds_a_track_matching_its_clips(self):
        clips = [self.tone("one.mp3", 3), self.tone("two.mp3", 4)]
        expected = sum(combined_track.mp3_duration(c) for c in clips)
        final = str(self.root / "office.mp3")
        duration = combined_track.ensure_combined_track(clips, final, expected, 24000)
        self.assertAlmostEqual(duration, expected, delta=0.2)
        self.assertAlmostEqual(combined_track.mp3_duration(final), duration, places=3)
        self.assertEqual(
            sorted(p.name for p in self.root.iterdir()),
            sorted(["one.mp3", "two.mp3", "office.mp3", "office.mp3.lock"]),
        )

    def test_killed_encode_never_reaches_the_final_path(self):
        clips = [self.tone(f"clip{i}.mp3", 30) for i in range(6)]
        final = str(self.root / "office.mp3")

        def killed_run(command, **kwargs):
            # Throttle the encode to real time and kill it partway, as a worker
            # restart would, leaving a partial file at ffmpeg's output path.
            process = subprocess.Popen(
                [command[0], "-re", *command[1:-1], "-flush_packets", "1", command[-1]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.time() + 10
            while time.time() < deadline and not (os.path.exists(command[-1]) and os.path.getsize(command[-1]) > 4096):
                time.sleep(0.05)
            process.send_signal(signal.SIGKILL)
            process.wait()
            self.partial_size = os.path.getsize(command[-1])
            # What an interrupted encode leaves: audio bytes but no finalised length.
            self.partial_duration = combined_track.mp3_duration(command[-1])
            return MagicMock(returncode=process.returncode, stderr="killed")

        with patch.object(combined_track.subprocess, "run", side_effect=killed_run):
            duration = combined_track.ensure_combined_track(clips, final, 180.0, 24000)
        self.assertGreater(self.partial_size, 4096)
        self.assertEqual(self.partial_duration, 0.0)
        self.assertEqual(duration, 0.0)
        self.assertFalse(os.path.exists(final))
        # Only the (empty) lock remains: no temporary audio or concat list.
        leftovers = [p.name for p in self.root.iterdir() if p.name.startswith("office.mp3.")]
        self.assertEqual(leftovers, ["office.mp3.lock"])
        self.assertEqual((self.root / "office.mp3.lock").read_text(), "")


class AuditCombinedAudioCommandTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        settings_override = override_settings(MEDIA_ROOT=str(self.root))
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        (self.root / "gemini").mkdir()
        self.durations = {}
        patcher = patch.object(combined_track, "MP3", side_effect=fake_mp3(self.durations))
        patcher.start()
        self.addCleanup(patcher.stop)
        # The command's own CBR size check reads MP3 directly; keep it out of these tests.
        cbr = patch("office.management.commands.audit_combined_audio.MP3", side_effect=fake_mp3(self.durations))
        cbr.start()
        self.addCleanup(cbr.stop)

    def file(self, relative, duration=None, age_minutes=0, content=b"mp3"):
        path = self.root / relative
        path.write_bytes(content)
        if duration is not None:
            self.durations[str(path)] = duration
        if age_minutes:
            past = time.time() - age_minutes * 60
            os.utime(path, (past, past))
        return path

    def run_command(self, *args):
        out = StringIO()
        call_command("audit_combined_audio", *args, stdout=out)
        return out.getvalue()

    @staticmethod
    def track(label):
        """A combined-track style name: a uuid whose last group encodes the label."""
        return f"00000000-0000-5000-8000-{label.encode().hex()[:12]:0>12}.mp3"

    def make_files(self):
        self.names = names = {
            label: self.track(label)
            for label in ("good", "trunc", "unread", "clip", "short", "source", "stale", "fresh", "gone")
        }
        files = {
            "good": self.file(f"gemini/{names['good']}", 900.0),
            "truncated": self.file(f"gemini/{names['trunc']}", 0.0),
            "unreadable": self.file(f"gemini/{names['unread']}"),
            "clip": self.file(f"gemini/{names['clip']}", 0.0),
            "silence": self.file("gemini/silence_500ms_24000.mp3", 0.0),
            # A legacy concat list beside a track whose header was finalised.
            "short": self.file(f"gemini/{names['short']}", 60.0),
            "source": self.file(f"gemini/{names['source']}", 120.0),
            "stale_part": self.file(f"gemini/{names['stale']}.{'a' * 32}.part", age_minutes=120),
            "fresh_part": self.file(f"gemini/{names['fresh']}.{'b' * 32}.part"),
            "orphan_lock": self.file(f"gemini/{names['gone']}.lock", content=b"", age_minutes=120),
            # Other features keep their own media and locks here; never touched.
            "dialogue": self.file("gemini/dialogue_abc.mp3", 0.0),
            "dialogue_lock": self.file("gemini/dialogue_abc.mp3.lock", content=b"", age_minutes=120),
        }
        files["short_list"] = self.file(
            f"gemini/{names['short']}.txt", content=f"file '{files['source']}'\n".encode(), age_minutes=120
        )
        AudioClip.objects.create(key="clip", filename=f"gemini/{names['clip']}", provider="gemini")
        return files

    def test_dry_run_reports_without_deleting(self):
        files = self.make_files()
        names = self.names
        output = self.run_command()
        self.assertIn(f"Bad combined track: gemini/{names['trunc']} (no readable duration", output)
        self.assertIn(f"Bad combined track: gemini/{names['unread']}", output)
        self.assertIn(f"Bad combined track: gemini/{names['short']} (60.0s of an expected 120.0s)", output)
        self.assertIn(f"Stale build file: gemini/{names['stale']}.{'a' * 32}.part", output)
        self.assertIn(f"Stale build file: gemini/{names['gone']}.lock", output)
        self.assertIn(f"Stale build file: gemini/{names['short']}.txt", output)
        for label in ("good", "clip", "source", "fresh"):
            self.assertNotIn(names[label], output)
        self.assertNotIn("silence_", output)
        self.assertNotIn("dialogue", output)
        self.assertIn("Truncated or unreadable tracks: 3", output)
        self.assertIn("Dry run", output)
        for path in files.values():
            self.assertTrue(path.exists(), path)

    def test_delete_removes_only_problem_files(self):
        files = self.make_files()
        self.run_command("--delete")
        for name in ("truncated", "unreadable", "short", "short_list", "stale_part", "orphan_lock"):
            self.assertFalse(files[name].exists(), name)
        for name in ("good", "clip", "silence", "source", "fresh_part", "dialogue", "dialogue_lock"):
            self.assertTrue(files[name].exists(), name)
        self.assertFalse((self.root / "gemini" / f"{self.names['trunc']}.lock").exists())


class AudioTrackCacheHeaderTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "track.mp3").write_bytes(b"0123456789")
        settings_override = override_settings(MEDIA_ROOT=str(self.root))
        settings_override.enable()
        self.addCleanup(settings_override.disable)

    def get(self, length):
        audio = MagicMock()
        audio.info.length = length
        with (
            patch("churchcal.api.views.MP3", return_value=audio),
            patch("analytics.utils.record_audio_loaded"),
        ):
            response = self.client.get(reverse("audio_track", kwargs={"track": "track.mp3"}))
        self.addCleanup(response.close)
        return response

    def test_truncated_track_is_not_cached(self):
        response = self.get(0.0)
        self.assertEqual(response["X-Audio-Duration"], "0")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_complete_track_keeps_default_caching(self):
        response = self.get(905.2)
        self.assertEqual(response["X-Audio-Duration"], "905")
        self.assertNotIn("no-store", response.get("Cache-Control", ""))

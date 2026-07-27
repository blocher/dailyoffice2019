import os
import tempfile
import time
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from office.management.commands.cleanup_full_audio_files import Command as CleanupFullAudioCommand
from office.models import Scripture


class NormalizeBibleTranslationTests(TestCase):
    def test_undefined_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("undefined"), "esv")

    def test_null_and_none_strings_default_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("null"), "esv")
        self.assertEqual(Scripture.normalize_bible_translation("none"), "esv")

    def test_empty_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation(""), "esv")
        self.assertEqual(Scripture.normalize_bible_translation(None), "esv")

    def test_valid_translation_is_normalized(self):
        self.assertEqual(Scripture.normalize_bible_translation("NRSVCE"), "nrsvce")

    def test_unknown_translation_defaults_to_esv(self):
        self.assertEqual(Scripture.normalize_bible_translation("msg"), "esv")


class CleanupFullAudioFilesTests(TestCase):
    def test_scan_dirs_includes_provider_subfolders(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "openai_v2"))
            os.makedirs(os.path.join(tmp, "fish"))
            dirs = CleanupFullAudioCommand()._scan_dirs(tmp)
            self.assertEqual(
                dirs,
                [tmp, os.path.join(tmp, "fish"), os.path.join(tmp, "openai_v2")],
            )

    @override_settings(MEDIA_ROOT="")
    def test_deletes_ffmpeg_full_tracks_in_openai_v2(self):
        with tempfile.TemporaryDirectory() as tmp:
            v2 = os.path.join(tmp, "openai_v2")
            os.makedirs(v2)
            full_path = os.path.join(v2, "full-track.mp3")
            clip_path = os.path.join(v2, "clip.mp3")
            for path in (full_path, clip_path):
                with open(path, "wb") as f:
                    f.write(b"fake-mp3")
                # Older than --days 7
                old = time.time() - (8 * 86400)
                os.utime(path, (old, old))

            def fake_mp3(path):
                audio = MagicMock()
                if path.endswith("full-track.mp3"):
                    tag = MagicMock()
                    tag.text = ["Lavf61.7.100"]
                    audio.tags.getall.return_value = [tag]
                else:
                    audio.tags = None
                return audio

            with (
                override_settings(MEDIA_ROOT=tmp),
                patch(
                    "office.management.commands.cleanup_full_audio_files.MP3",
                    side_effect=fake_mp3,
                ),
            ):
                out = StringIO()
                call_command("cleanup_full_audio_files", "--execute", "--days", "7", stdout=out)

            self.assertFalse(os.path.exists(full_path))
            self.assertTrue(os.path.exists(clip_path))
            self.assertIn("openai_v2/full-track.mp3", out.getvalue())

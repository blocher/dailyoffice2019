import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from office.api.views import index


class CacheOnlyAudioTests(SimpleTestCase):
    def provider(self):
        return Mock(name="provider", media_subdir="gemini", voice_for_text=Mock(return_value="reader"))

    def test_missing_cache_does_not_require_directory_write_access(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"),
            patch.object(index, "TTS_PROVIDER", self.provider()),
            patch.object(index.os, "makedirs", side_effect=PermissionError("read-only media root")) as mkdir,
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech") as synthesize,
            patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip") as record,
            patch.object(index.bugsnag, "notify") as notify,
        ):
            url, path = index.GenericDailyOfficeSerializer.get_or_create_clip(
                "In the beginning.", "reader", no_generate=True, voice="reader"
            )
            self.assertTrue(path.startswith("/uploads/gemini/"))
            self.assertTrue(url.endswith(path))
            self.assertFalse(Path(directory, "gemini").exists())
            mkdir.assert_not_called()
            synthesize.assert_not_called()
            record.assert_not_called()
            notify.assert_not_called()

    def test_existing_cache_remains_available_without_mkdir(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"),
            patch.object(index, "TTS_PROVIDER", self.provider()),
            patch.object(index.os.path, "isfile", return_value=True),
            patch.object(index.os.path, "getsize", return_value=20),
            patch.object(index.os, "makedirs", side_effect=PermissionError("read-only media root")) as mkdir,
            patch.object(index.GenericDailyOfficeSerializer, "get_clip_word_timing", return_value=[]),
            patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip"),
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech") as synthesize,
        ):
            url, path = index.GenericDailyOfficeSerializer.get_or_create_clip(
                "In the beginning.", "reader", no_generate=True, voice="reader"
            )
            self.assertIsNotNone(url)
            self.assertTrue(path.startswith("/uploads/gemini/"))
            mkdir.assert_not_called()
            synthesize.assert_not_called()

    def test_generation_still_creates_provider_directory(self):
        def synthesize(voice, text, file_path):
            self.assertTrue(Path(file_path).parent.is_dir())
            Path(file_path).write_bytes(b"test audio")
            return []

        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"),
            patch.object(index, "TTS_PROVIDER", self.provider()),
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech", side_effect=synthesize) as synthesis,
            patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip"),
        ):
            url, path = index.GenericDailyOfficeSerializer.get_or_create_clip(
                "In the beginning.", "reader", voice="reader"
            )
            self.assertIsNotNone(url)
            self.assertTrue(Path(directory, path.removeprefix("/uploads/")).is_file())
            synthesis.assert_called_once()

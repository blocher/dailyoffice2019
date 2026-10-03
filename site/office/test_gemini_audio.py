"""Gemini adapter tests mock HTTP; no live synthesis or credentials are used."""

import base64
import io
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from office.api.views import index
from office.api.views.tts import GeminiTTSProvider, ElevenLabsTTSProvider, get_tts_provider, provider_names
from office.models import AudioClip
from rest_framework.test import APIRequestFactory


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\0\0" * 2400)
    return buffer.getvalue()


@override_settings(GEMINI_API_KEY="test-placeholder", GEMINI_TTS_MAX_RETRIES=0)
class GeminiProviderTests(SimpleTestCase):
    def setUp(self):
        self.provider = GeminiTTSProvider()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = os.path.join(self.temp.name, "clip.mp3")

    def response(self, data=None, status=200):
        return Mock(
            status_code=status,
            headers={"x-request-id": "request-1"},
            json=Mock(
                return_value=data
                or {
                    "steps": [
                        {
                            "type": "model_output",
                            "content": [
                                {
                                    "type": "audio",
                                    "mime_type": "audio/wav",
                                    "data": base64.b64encode(wav_bytes()).decode(),
                                }
                            ],
                        }
                    ],
                    "usage": {"total_tokens": 123},
                }
            ),
        )

    @override_settings(GEMINI_TTS_STYLE="calm and measured")
    @patch("office.api.views.tts.subprocess.run")
    @patch("office.api.views.tts.requests.post")
    def test_verbatim_transcript_metadata_and_atomic_mp3(self, post, run):
        post.return_value = self.response()

        def convert(command, **kwargs):
            with open(command[command.index("-i") + 1], "rb") as source:
                self.assertEqual(source.read(4), b"RIFF")
            with open(command[-1], "wb") as output:
                output.write(b"test-mp3")
            return SimpleNamespace(returncode=0)

        run.side_effect = convert
        result = self.provider.synthesize("Kore", "The Lord be with you.", self.output)
        payload = post.call_args.kwargs["json"]
        part = payload["input"][0]["content"][0]
        self.assertEqual(part["text"], "The Lord be with you.")
        self.assertEqual(part["annotations"], [{"type": "speech_metadata", "style": "calm and measured"}])
        self.assertEqual(payload["generation_config"]["speech_config"], [{"voice": "Kore"}])
        self.assertEqual(result, [])
        self.assertEqual(os.listdir(self.temp.name), ["clip.mp3"])

    @override_settings(GEMINI_API_KEY="")
    @patch("office.api.views.tts.requests.post")
    def test_missing_key_fails_before_request(self, post):
        with self.assertRaisesMessage(RuntimeError, "GEMINI_API_KEY"):
            self.provider.synthesize("Kore", "Amen.", self.output)
        post.assert_not_called()

    @patch("office.api.views.tts.requests.post")
    def test_empty_invalid_and_raw_pcm_audio_fail_without_file(self, post):
        for content in [
            [],
            [{"type": "audio", "data": "not base64!"}],
            [{"type": "audio", "data": base64.b64encode(b"\0" * 100).decode()}],
        ]:
            with self.subTest(content=content):
                post.return_value = self.response({"steps": [{"type": "model_output", "content": content}]})
                with self.assertRaises(RuntimeError):
                    self.provider.synthesize("Kore", "Amen.", self.output)
                self.assertFalse(os.path.exists(self.output))

    @patch("office.api.views.tts.subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 120))
    @patch("office.api.views.tts.requests.post")
    def test_conversion_failure_leaves_no_partial_files(self, post, run):
        post.return_value = self.response()
        with self.assertRaisesMessage(RuntimeError, "conversion"):
            self.provider.synthesize("Kore", "Amen.", self.output)
        self.assertEqual(os.listdir(self.temp.name), [])

    @override_settings(GEMINI_TTS_MAX_RETRIES=2)
    @patch("office.api.views.tts.time.sleep")
    @patch("office.api.views.tts.requests.post")
    def test_transient_retry_but_not_auth_errors(self, post, sleep):
        post.side_effect = [self.response(status=429), self.response(status=503), self.response()]
        self.provider._request({}, "placeholder")
        self.assertEqual(post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        post.reset_mock(side_effect=True)
        post.return_value = self.response(status=401)
        with self.assertRaisesMessage(RuntimeError, "HTTP 401"):
            self.provider._request({}, "placeholder")
        self.assertEqual(post.call_count, 1)

    @override_settings(TTS_PROVIDER="gemini")
    def test_environment_selection_and_explicit_override(self):
        self.assertIsInstance(get_tts_provider(), GeminiTTSProvider)
        self.assertIsInstance(get_tts_provider("elevenlabs"), ElevenLabsTTSProvider)
        self.assertIn("gemini", provider_names())

    @override_settings(TTS_PROVIDER="typo")
    def test_invalid_provider_fails_clearly(self):
        with self.assertRaisesMessage(ValueError, "Unknown TTS_PROVIDER"):
            get_tts_provider()

    @override_settings(GEMINI_TTS_VOICE_LEADER="voice_custom", GEMINI_TTS_VOICES_READER=[])
    def test_voice_roles_and_blank_defaults(self):
        self.assertEqual(self.provider.voice_for_line_type("leader_dialogue"), "voice_custom")
        self.assertEqual(self.provider.voice_for_line_type("reader"), "Algieba")
        self.assertIsNone(self.provider.voice_for_line_type("rubric"))

    @override_settings(GEMINI_TTS_VOICES_READER=" Kore, ,Charon, Sulafat ")
    def test_reader_pool_uses_stable_selection_for_reader_and_html(self):
        self.assertEqual(self.provider.voices["reader"], ("Kore", "Charon", "Sulafat"))
        selected = {self.provider.voice_for_text("reader", f"Passage {i}") for i in range(50)}
        self.assertEqual(selected, {"Kore", "Charon", "Sulafat"})
        for role in ("reader", "html"):
            self.assertEqual(
                self.provider.voice_for_text(role, "In the beginning"),
                self.provider.voice_for_text("reader", "In the beginning"),
            )

    @override_settings(GEMINI_TTS_VOICES_READER=[" ", ""], GEMINI_TTS_VOICE_READER="Puck")
    def test_empty_pool_defaults_to_algieba_ignoring_legacy_setting(self):
        self.assertEqual(self.provider.voice_for_text("reader", "Amen."), "Algieba")

    @skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for the real transcoding smoke test")
    @patch("office.api.views.tts.requests.post")
    def test_real_ffmpeg_produces_readable_mp3(self, post):
        from mutagen.mp3 import MP3

        post.return_value = self.response()
        self.provider.synthesize("Kore", "Amen.", self.output)
        audio = MP3(self.output)
        self.assertEqual(audio.info.sample_rate, 44100)
        self.assertEqual(audio.info.channels, 1)
        self.assertGreater(audio.info.length, 0)
        self.assertEqual(os.listdir(self.temp.name), ["clip.mp3"])


@override_settings(GEMINI_TTS_VOICE_LEADER="Kore", GEMINI_TTS_STYLE="", GEMINI_TTS_MODEL="gemini-3.8-flash-tts")
class GeminiClipTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.provider = GeminiTTSProvider()
        self.enterContext(override_settings(MEDIA_ROOT=self.temp.name, MEDIA_URL="/uploads/"))
        self.enterContext(patch.object(index, "TTS_PROVIDER", self.provider))

    def test_cache_tracks_model_voice_style_and_records_provider(self):
        def synthesize(voice, text, file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as handle:
                handle.write(b"fake-audio")
            return []

        get_clip = index.GenericDailyOfficeSerializer.get_or_create_clip
        with patch.object(self.provider, "synthesize", side_effect=synthesize) as generate:
            first = get_clip("Let us pray.", "leader")
            self.assertEqual(first, get_clip("Let us pray.", "leader"))
            self.assertEqual(generate.call_count, 1)
            self.assertIn("/gemini/", first[1])
            for options in [
                {"GEMINI_TTS_MODEL": "gemini-3.8-flash-lite-tts"},
                {"GEMINI_TTS_STYLE": "reverent"},
                {"GEMINI_TTS_VOICE_LEADER": "Charon"},
            ]:
                with self.subTest(options=options), override_settings(**options):
                    self.assertNotEqual(first, get_clip("Let us pray.", "leader"))
            self.assertEqual(generate.call_count, 4)
        self.assertEqual(AudioClip.objects.filter(provider="gemini").count(), 4)

    def test_failure_does_not_publish_clip(self):
        with patch.object(self.provider, "synthesize", side_effect=RuntimeError("unavailable")):
            self.assertEqual(index.GenericDailyOfficeSerializer.get_or_create_clip("Amen.", "leader"), (None, None))
        self.assertFalse(AudioClip.objects.exists())
        self.assertFalse(any(Path(self.temp.name).rglob("*.mp3")))

    @override_settings(GEMINI_TTS_VOICES_READER=["Charon", "Kore"])
    def test_reader_reuse_survives_pool_changes_in_both_endpoints(self):
        text = "The Word of the Lord."
        filename = "gemini/existing.mp3"
        path = Path(self.temp.name) / filename
        path.parent.mkdir()
        path.write_bytes(b"existing-audio")
        AudioClip.objects.create(
            key="existing",
            filename=filename,
            text=text,
            line_type="reader",
            provider="gemini",
            voice="old-reader",
            model="gemini-3.8-flash-tts",
            kind="reader",
        )
        get_clip = index.GenericDailyOfficeSerializer.get_or_create_clip
        with patch.object(self.provider, "synthesize") as synthesize:
            first = get_clip(text, "reader")
            self.assertEqual(first[1], "/uploads/" + filename)
            for pool in (["Kore", "Charon"], ["Sulafat"], []):
                with self.subTest(pool=pool), override_settings(GEMINI_TTS_VOICES_READER=pool):
                    self.assertEqual(get_clip(text, "reader"), first)
                    self.assertEqual(get_clip(text, "html"), first)
                    request = APIRequestFactory().post(
                        "/audio/", {"content": text, "line_type": "reader"}, format="json"
                    )
                    response = index.AudioViewSet().retrieve(request)
                    self.assertTrue(response.data["path"].endswith("/uploads/" + filename))
            synthesize.assert_not_called()
        self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader(text, "leader"))
        self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader("Different text", "reader"))
        path.unlink()
        self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader(text, "reader"))
        path.write_bytes(b"")
        self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader(text, "reader"))

    def test_reader_reuse_is_provider_scoped(self):
        path = Path(self.temp.name) / "elevenlabs" / "existing.mp3"
        path.parent.mkdir()
        path.write_bytes(b"other-provider")
        AudioClip.objects.create(
            key="other",
            filename="elevenlabs/existing.mp3",
            text="Amen.",
            line_type="reader",
            provider="elevenlabs",
            voice="other",
            model="eleven_v3",
            kind="reader",
        )
        self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader("Amen.", "reader"))

"""Gemini adapter tests mock HTTP; no live synthesis or credentials are used."""

import base64
import io
import os
import shutil
import subprocess
import tempfile
import wave
from decimal import Decimal
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from office.audio.providers import AudioProviderError, GeminiAudioProvider, ProviderResult, get_audio_provider
from office.audio.services import AudioItem, VoiceResolver, line_reference_cache_key
from office.models import AudioGeneratedFile, AudioGenerationConfig, AudioGenerationEvent
from office.tests import AudioGenerationTestCase


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
        self.provider = GeminiAudioProvider(SimpleNamespace())
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
    @patch("office.audio.providers.subprocess.run")
    @patch("office.audio.providers.requests.post")
    def test_verbatim_transcript_metadata_and_atomic_mp3(self, post, run):
        post.return_value = self.response()

        def convert(command, **kwargs):
            with open(command[command.index("-i") + 1], "rb") as source:
                self.assertEqual(source.read(4), b"RIFF")
            with open(command[-1], "wb") as output:
                output.write(b"test-mp3")
            return SimpleNamespace(returncode=0)

        run.side_effect = convert
        result = self.provider.generate_spoken_file("The Lord be with you.", "Kore", self.output)
        payload = post.call_args.kwargs["json"]
        part = payload["input"][0]["content"][0]
        self.assertEqual(part["text"], "The Lord be with you.")
        self.assertEqual(part["annotations"], [{"type": "speech_metadata", "style": "calm and measured"}])
        self.assertEqual(payload["generation_config"]["speech_config"], [{"voice": "Kore"}])
        self.assertEqual(result.request_id, "request-1")
        self.assertEqual(result.metadata["usage"], {"total_tokens": 123})
        self.assertEqual(os.listdir(self.temp.name), ["clip.mp3"])

    @override_settings(GEMINI_API_KEY="")
    @patch("office.audio.providers.requests.post")
    def test_missing_key_fails_before_request(self, post):
        with self.assertRaisesMessage(AudioProviderError, "GEMINI_API_KEY"):
            self.provider.generate_spoken_file("Amen.", "Kore", self.output)
        post.assert_not_called()

    @patch("office.audio.providers.requests.post")
    def test_empty_invalid_and_raw_pcm_audio_fail_without_file(self, post):
        for content in [
            [],
            [{"type": "audio", "data": "not base64!"}],
            [{"type": "audio", "data": base64.b64encode(b"\0" * 100).decode()}],
        ]:
            with self.subTest(content=content):
                post.return_value = self.response({"steps": [{"type": "model_output", "content": content}]})
                with self.assertRaises(AudioProviderError):
                    self.provider.generate_spoken_file("Amen.", "Kore", self.output)
                self.assertFalse(os.path.exists(self.output))

    @patch("office.audio.providers.subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 120))
    @patch("office.audio.providers.requests.post")
    def test_conversion_failure_leaves_no_partial_files(self, post, run):
        post.return_value = self.response()
        with self.assertRaisesMessage(AudioProviderError, "conversion"):
            self.provider.generate_spoken_file("Amen.", "Kore", self.output)
        self.assertEqual(os.listdir(self.temp.name), [])

    @override_settings(GEMINI_TTS_MAX_RETRIES=2)
    @patch("office.audio.providers.time.sleep")
    @patch("office.audio.providers.requests.post")
    def test_transient_retry_but_not_auth_errors(self, post, sleep):
        post.side_effect = [self.response(status=429), self.response(status=503), self.response()]
        self.provider._request({}, "placeholder")
        self.assertEqual(post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        post.reset_mock(side_effect=True)
        post.return_value = self.response(status=401)
        with self.assertRaisesMessage(AudioProviderError, "HTTP 401"):
            self.provider._request({}, "placeholder")
        self.assertEqual(post.call_count, 1)

    @override_settings(AUDIO_PROVIDER="gemini")
    def test_environment_selection_does_not_mutate_admin_choice(self):
        config = AudioGenerationConfig(provider_mode="elevenlabs_v3")
        provider, mode = get_audio_provider(config)
        self.assertIsInstance(provider, GeminiAudioProvider)
        self.assertEqual(mode, "gemini")
        self.assertEqual(config.provider_mode, "elevenlabs_v3")

    @override_settings(AUDIO_PROVIDER="elevenlabs")
    def test_elevenlabs_alias_keeps_existing_provider(self):
        provider, mode = get_audio_provider(AudioGenerationConfig())
        self.assertEqual(provider.provider_name, "elevenlabs")
        self.assertEqual(mode, "elevenlabs_v3")

    @override_settings(AUDIO_PROVIDER="typo")
    def test_invalid_provider_fails_clearly(self):
        with self.assertRaisesMessage(AudioProviderError, "Unknown audio provider"):
            get_audio_provider(AudioGenerationConfig())

    @override_settings(GEMINI_TTS_VOICE_LEADER="voice_custom")
    def test_environment_voice_applies_to_dialogue_role(self):
        resolver = VoiceResolver(self.provider, "gemini")
        self.assertEqual(resolver.for_role("leader_dialogue"), "voice_custom")

    def test_default_voices_and_database_voice_are_gemini_specific(self):
        resolver = VoiceResolver(self.provider, "gemini")
        resolver._voices = []
        self.assertEqual(resolver.provider_name, "gemini")
        self.assertEqual(resolver.for_role("reader"), "Charon")
        resolver._voices = [SimpleNamespace(role="reader", voice_id="voice_reader")]
        self.assertEqual(resolver.for_role("reader"), "voice_reader")

    @skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for the real transcoding smoke test")
    @patch("office.audio.providers.requests.post")
    def test_real_ffmpeg_produces_readable_mp3(self, post):
        from mutagen.mp3 import MP3

        post.return_value = self.response()
        self.provider.generate_spoken_file("Amen.", "Kore", self.output)
        audio = MP3(self.output)
        self.assertEqual(audio.info.sample_rate, 44100)
        self.assertEqual(audio.info.channels, 1)
        self.assertGreater(audio.info.length, 0)
        self.assertEqual(os.listdir(self.temp.name), ["clip.mp3"])


@override_settings(AUDIO_PROVIDER="gemini", GEMINI_TTS_VOICE_LEADER="Kore", GEMINI_TTS_STYLE="")
class GeminiBuilderTests(AudioGenerationTestCase):
    """Real cache/event/usage models; synthesis alone is mocked."""

    @patch("office.audio.services.audio_duration", return_value=Decimal("1.5"))
    @patch("office.audio.providers.GeminiAudioProvider.generate_spoken_file")
    def test_cache_tracks_model_voice_and_style(self, generate, duration):
        def synthesize(text, voice_id, output_path):
            self.write_fake_audio(output_path)
            return ProviderResult(characters=len(text))

        generate.side_effect = synthesize
        item = AudioItem("Opening", "leader-1", "leader", "leader", "Let us pray.")
        first = self.builder()._generate_spoken_items([item])[0]
        second = self.builder()._generate_spoken_items([item])[0]
        self.assertEqual(first.generated_file.pk, second.generated_file.pk)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(first.generated_file.provider, "gemini")
        self.assertEqual(first.generated_file.provider_mode, "gemini")
        self.assertEqual(first.generated_file.cost_source, "unpriced")
        self.assertEqual(first.line_segments[0]["id"], "leader-1")
        for options in [
            {"GEMINI_TTS_MODEL": "gemini-3.8-flash-lite-tts"},
            {"GEMINI_TTS_STYLE": "reverent"},
            {"GEMINI_TTS_VOICE_LEADER": "Charon"},
        ]:
            with self.subTest(options=options), override_settings(**options):
                changed = self.builder()._generate_spoken_items([item])[0]
                self.assertNotEqual(first.generated_file.pk, changed.generated_file.pk)
        self.assertEqual(generate.call_count, 4)
        self.assertEqual(AudioGeneratedFile.objects.filter(provider="gemini", status="ready").count(), 4)

    @patch(
        "office.audio.providers.GeminiAudioProvider.generate_spoken_file",
        side_effect=AudioProviderError("unavailable"),
    )
    def test_generation_failure_is_recorded_and_never_ready(self, generate):
        with self.assertRaisesMessage(AudioProviderError, "unavailable"):
            self.builder()._generate_spoken_items([AudioItem("Opening", "line-1", "leader", "leader", "Amen.")])
        generated = AudioGeneratedFile.objects.get(provider="gemini")
        self.assertEqual(generated.status, "failed")
        self.assertTrue(AudioGenerationEvent.objects.filter(generated_file=generated, action="error").exists())
        self.assertFalse(generated.file_name)

    def test_sound_effects_are_not_sent_to_gemini(self):
        items = self.builder()._items_for_module(
            {
                "name": "Test",
                "lines": [
                    {"id": "sound-1", "line_type": "sound", "content": "bell"},
                    {"id": "speech-1", "line_type": "leader", "content": "Amen."},
                ],
            }
        )
        self.assertEqual([item.line_id for item in items], ["speech-1"])

    @override_settings(AUDIO_PROVIDER="elevenlabs")
    def test_legacy_reference_uses_environment_provider_mode(self):
        implicit = line_reference_cache_key("leader", "Amen.")
        explicit = line_reference_cache_key("leader", "Amen.", provider_mode="elevenlabs_v3")
        self.assertEqual(implicit, explicit)

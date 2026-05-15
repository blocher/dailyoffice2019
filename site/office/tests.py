import datetime
import os
import shutil
import tempfile
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from office.audio.providers import ProviderResult, get_audio_provider
from office.audio.services import AudioItem, FFMPEGAudioAssembler, OfficeAudioBuilder, VoiceResolver
from office.models import AudioGeneratedFile, AudioGenerationConfig, AudioGenerationEvent, AudioVoice


class AudioGenerationTestCase(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root, MEDIA_URL="/uploads/")
        self.override.enable()
        Site.objects.update_or_create(id=settings.SITE_ID, defaults={"domain": "example.com", "name": "Example"})
        self.config = AudioGenerationConfig.get_solo()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def dummy_office(self):
        return SimpleNamespace(
            settings={"bible_translation": "esv"},
            date=SimpleNamespace(date=datetime.date(2026, 5, 3)),
            request=SimpleNamespace(get_full_path=lambda: "/api/v1/office/morning_prayer/2026-05-03"),
        )

    def builder(self):
        return OfficeAudioBuilder(self.dummy_office())

    def write_fake_audio(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as fake_audio:
            fake_audio.write(b"fake mp3")


class AudioProviderSelectionTests(AudioGenerationTestCase):
    def test_studio_mode_falls_back_when_toggle_is_off(self):
        self.config.provider_mode = AudioGenerationConfig.ProviderMode.ELEVENLABS_STUDIO
        self.config.elevenlabs_studio_enabled = False
        self.config.save()

        provider, provider_mode = get_audio_provider(self.config)

        self.assertEqual(provider.provider_name, "elevenlabs")
        self.assertEqual(provider_mode, AudioGenerationConfig.ProviderMode.ELEVENLABS_V3)
        self.assertTrue(AudioGenerationEvent.objects.filter(action=AudioGenerationEvent.Action.FALLBACK).exists())


class AudioVoiceTests(AudioGenerationTestCase):
    def test_reader_voice_selection_is_deterministic(self):
        AudioVoice.objects.create(provider="elevenlabs", role="reader", name="Reader A", voice_id="voice-a", order=1)
        AudioVoice.objects.create(provider="elevenlabs", role="reader", name="Reader B", voice_id="voice-b", order=2)
        self.config.provider_mode = AudioGenerationConfig.ProviderMode.ELEVENLABS_V3
        self.config.save()
        provider, provider_mode = get_audio_provider(self.config)
        resolver = VoiceResolver(provider, provider_mode)

        first = resolver.for_role("reader", "reading-one")
        second = resolver.for_role("reader", "reading-one")

        self.assertEqual(first, second)
        self.assertIn(first, {"voice-a", "voice-b"})


class AudioBuilderTests(AudioGenerationTestCase):
    def enable_elevenlabs(self):
        self.config.provider_mode = AudioGenerationConfig.ProviderMode.ELEVENLABS_V3
        self.config.save()
        AudioVoice.objects.create(provider="elevenlabs", role="leader", name="Leader", voice_id="leader-voice")
        AudioVoice.objects.create(provider="elevenlabs", role="reader", name="Reader", voice_id="reader-voice")

    @patch("office.audio.services.audio_duration", return_value=Decimal("1.500"))
    @patch("office.audio.providers.ElevenLabsV3AudioProvider.generate_dialogue_file")
    def test_elevenlabs_spoken_generation_uses_v3_and_cache(self, generate_dialogue_file, audio_duration):
        self.enable_elevenlabs()

        def fake_generate(inputs, output_path):
            self.write_fake_audio(output_path)
            return ProviderResult(
                characters=sum(len(item["text"]) for item in inputs),
                cost_units=Decimal("12"),
                request_id="request-1",
                voice_segments=[
                    {
                        "dialogue_input_index": 0,
                        "start_time_seconds": 0,
                        "end_time_seconds": 1.5,
                    }
                ],
            )

        generate_dialogue_file.side_effect = fake_generate
        item = AudioItem("Opening", "line-1", "leader", "leader", "The Lord be with you.")

        first = self.builder()._generate_elevenlabs_dialogue_chunk([item])
        second = self.builder()._generate_elevenlabs_dialogue_chunk([item])

        self.assertEqual(first.generated_file.uuid, second.generated_file.uuid)
        self.assertEqual(first.generated_file.model_id, "eleven_v3")
        self.assertEqual(first.line_segments[0]["id"], "line-1")
        self.assertEqual(generate_dialogue_file.call_count, 1)

    @patch("office.audio.services.audio_duration", return_value=Decimal("1.000"))
    @patch("office.audio.providers.ElevenLabsV3AudioProvider.generate_dialogue_file")
    def test_disabled_file_is_not_reused(self, generate_dialogue_file, audio_duration):
        self.enable_elevenlabs()

        def fake_generate(inputs, output_path):
            self.write_fake_audio(output_path)
            return ProviderResult(characters=10, cost_units=Decimal("10"))

        generate_dialogue_file.side_effect = fake_generate
        item = AudioItem("Opening", "line-1", "leader", "leader", "Amen.")

        first = self.builder()._generate_elevenlabs_dialogue_chunk([item])
        first.generated_file.mark_disabled()
        second = self.builder()._generate_elevenlabs_dialogue_chunk([item])

        self.assertNotEqual(first.generated_file.uuid, second.generated_file.uuid)
        self.assertEqual(generate_dialogue_file.call_count, 2)

    @patch("office.audio.services.audio_duration", return_value=Decimal("2.000"))
    @patch("office.audio.providers.ElevenLabsV3AudioProvider.generate_sound_file")
    def test_sound_lines_use_sound_generation_cache_with_configured_model(self, generate_sound_file, audio_duration):
        self.enable_elevenlabs()

        def fake_generate(prompt, output_path, duration_seconds=None):
            self.write_fake_audio(output_path)
            return ProviderResult(characters=len(prompt), cost_units=Decimal("8"), request_id="sound-1")

        generate_sound_file.side_effect = fake_generate
        item = AudioItem("Opening", "sound-1", "sound", "sound", "A small chapel bell rings.", kind="sound")

        first = self.builder()._generate_sound(item)
        second = self.builder()._generate_sound(item)

        self.assertEqual(first.generated_file.uuid, second.generated_file.uuid)
        self.assertEqual(first.generated_file.model_id, "eleven_v3")
        self.assertEqual(generate_sound_file.call_count, 1)

    @patch.object(FFMPEGAudioAssembler, "generate_silence")
    @patch("office.audio.services.audio_duration", return_value=Decimal("3.000"))
    def test_silence_lines_generate_local_cached_audio(self, audio_duration, generate_silence):
        def fake_silence(output_path, seconds):
            self.write_fake_audio(output_path)

        generate_silence.side_effect = fake_silence
        item = AudioItem("Opening", "silence-1", "silence", "silence", "3", kind="silence", seconds=Decimal("3"))

        first = self.builder()._generate_silence(item)
        second = self.builder()._generate_silence(item)

        self.assertEqual(first.generated_file.uuid, second.generated_file.uuid)
        self.assertEqual(first.generated_file.generation_type, AudioGeneratedFile.GenerationType.SILENCE)
        self.assertEqual(generate_silence.call_count, 1)

    def test_openai_skips_sound_and_non_audio_roles(self):
        self.config.provider_mode = AudioGenerationConfig.ProviderMode.OPENAI
        self.config.save()
        module = {
            "name": "Opening",
            "lines": [
                {"id": "heading-1", "line_type": "heading", "content": "Opening"},
                {"id": "sound-1", "line_type": "sound", "content": "A bell rings."},
                {"id": "rubric-1", "line_type": "rubric", "content": "The People stand."},
                {"id": "leader-1", "line_type": "leader", "content": "Let us pray."},
            ],
        }

        items = self.builder()._items_for_module(module)

        self.assertEqual([item.line_id for item in items], ["leader-1"])

    def test_spoken_chunking_keeps_v3_requests_under_maximum(self):
        self.config.spoken_chunk_target_characters = 40
        self.config.spoken_chunk_max_characters = 50
        self.config.save()
        item = AudioItem("Reading", "reader-1", "reader", "reader", "word " * 40)

        chunks = self.builder()._spoken_chunks([item])

        self.assertTrue(all(sum(len(item.text) for item in chunk) <= 50 for chunk in chunks))

    @patch.object(FFMPEGAudioAssembler, "assemble")
    @patch("office.audio.services.audio_duration", return_value=Decimal("1.000"))
    @patch("office.audio.providers.OpenAIAudioProvider.generate_spoken_file")
    def test_audio_response_keeps_single_track_shape(self, generate_spoken_file, audio_duration, assemble):
        def fake_spoken(text, voice_id, output_path):
            self.write_fake_audio(output_path)
            return ProviderResult(characters=len(text))

        def fake_assemble(pieces, output_path, padding_ms=None):
            self.write_fake_audio(output_path)

        generate_spoken_file.side_effect = fake_spoken
        assemble.side_effect = fake_assemble
        module = {
            "name": "Opening",
            "lines": [
                {"id": "heading-1", "line_type": "heading", "content": "Opening"},
                {"id": "leader-1", "line_type": "leader", "content": "Let us pray."},
            ],
        }

        response = OfficeAudioBuilder(self.dummy_office(), modules=[module]).build()

        self.assertIn("single_track", response)
        self.assertEqual(len(response["single_track"]), 4)
        self.assertEqual(response["single_track"][2][0]["name"], "Opening")
        self.assertEqual(response["single_track"][3][0]["id"], "leader-1")

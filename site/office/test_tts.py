import base64
import os
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider
from office.models import AudioClip


class ElevenLabsTTSProviderTests(SimpleTestCase):
    @override_settings(
        ELEVENLABS_TTS_VOICE_LEADER="leader-id",
        ELEVENLABS_TTS_VOICE_CONGREGATION="people-id",
        ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"),
    )
    def test_roles_share_configured_voices_and_reader_is_selected_from_list(self):
        provider = ElevenLabsTTSProvider()

        self.assertEqual(provider.voice_for_line_type("leader"), "leader-id")
        self.assertEqual(provider.voice_for_line_type("leader_dialogue"), "leader-id")
        self.assertEqual(provider.voice_for_line_type("congregation"), "people-id")
        self.assertEqual(provider.voice_for_line_type("congregation_dialogue"), "people-id")
        with patch("office.api.views.tts.random.choice", return_value="reader-two") as choice:
            self.assertEqual(provider.voice_for_line_type("reader"), "reader-two")
            choice.assert_called_once_with(("reader-one", "reader-two"))
        self.assertEqual(
            provider.voice_for_text("reader", "In the beginning"),
            provider.voice_for_text("reader", "In the beginning"),
        )
        self.assertIn(
            provider.voice_for_text("reader", "In the beginning"),
            ("reader-one", "reader-two"),
        )

    @override_settings(
        ELEVENLABS_API_KEY="test-key",
        ELEVENLABS_TTS_MODEL="eleven_v3",
        ELEVENLABS_TTS_SPEED=0.9,
        ELEVENLABS_TTS_MAX_RETRIES=0,
    )
    @patch("office.api.views.tts.requests.post")
    def test_synthesize_writes_audio_and_returns_word_alignment(self, post):
        response = MagicMock()
        response.json.return_value = {
            "audio_base64": base64.b64encode(b"mp3-data").decode(),
            "alignment": {
                "characters": list("Peace be."),
                "character_start_times_seconds": [index / 10 for index in range(9)],
                "character_end_times_seconds": [(index + 1) / 10 for index in range(9)],
            },
        }
        post.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "clip.mp3")
            words = ElevenLabsTTSProvider().synthesize("voice-id", "Peace be.", path)

            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"mp3-data")

        self.assertEqual(
            words,
            [
                {
                    "word": "Peace",
                    "start_time": 0.0,
                    "end_time": 0.5,
                    "char_start": 0,
                    "char_end": 5,
                },
                {
                    "word": "be",
                    "start_time": 0.6,
                    "end_time": 0.8,
                    "char_start": 6,
                    "char_end": 8,
                },
            ],
        )
        post.assert_called_once()
        request = post.call_args
        self.assertEqual(request.kwargs["json"]["model_id"], "eleven_v3")
        self.assertEqual(request.kwargs["json"]["voice_settings"]["speed"], 0.9)
        self.assertEqual(request.kwargs["params"]["output_format"], "mp3_44100_128")


class ElevenLabsClipReuseTests(TestCase):
    def test_reader_exact_text_reuses_any_existing_elevenlabs_voice(self):
        with tempfile.TemporaryDirectory() as directory:
            provider_dir = os.path.join(directory, "elevenlabs")
            os.makedirs(provider_dir)
            filename = "elevenlabs/existing.mp3"
            file_path = os.path.join(directory, filename)
            with open(file_path, "wb") as handle:
                handle.write(b"existing-audio")
            AudioClip.objects.create(
                key="existing",
                filename=filename,
                text="The Word of the Lord.",
                line_type="reader",
                provider="elevenlabs",
                voice="old-reader",
                model="eleven_multilingual_v2",
                kind="reader",
                word_timing=[{"word": "The", "start_time": 0.0, "end_time": 0.2}],
            )

            provider = ElevenLabsTTSProvider()
            with (
                override_settings(
                    MEDIA_ROOT=directory,
                    MEDIA_URL="/uploads/",
                    SITE_ADDRESS="https://example.test",
                    ELEVENLABS_TTS_VOICES_READER=("new-reader",),
                ),
                patch.object(index, "TTS_PROVIDER", provider),
                patch.object(provider, "synthesize") as synthesize,
            ):
                url, path = index.GenericDailyOfficeSerializer.get_or_create_clip(
                    "The Word of the Lord.",
                    "reader",
                    kind="reader",
                )

            self.assertEqual(url, "https://example.test/uploads/elevenlabs/existing.mp3")
            self.assertEqual(path, "/uploads/elevenlabs/existing.mp3")
            synthesize.assert_not_called()

    def test_word_timing_round_trips_through_sidecar_without_database_row(self):
        timing = [{"word": "Peace", "start_time": 0.0, "end_time": 0.4}]
        with tempfile.TemporaryDirectory() as directory:
            provider_dir = os.path.join(directory, "elevenlabs")
            os.makedirs(provider_dir)
            file_path = os.path.join(provider_dir, "clip.mp3")
            with override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"):
                index.GenericDailyOfficeSerializer.save_word_timing(file_path, timing)
                loaded = index.GenericDailyOfficeSerializer.get_clip_word_timing("/uploads/elevenlabs/clip.mp3")

        self.assertEqual(loaded, timing)


class CombinedTrackTimingTests(TestCase):
    def test_word_timing_preserves_module_pause_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "elevenlabs"))
            paths = {
                "first": os.path.join(directory, "first.mp3"),
                "second": os.path.join(directory, "second.mp3"),
                "group_gap": os.path.join(directory, "group-gap.mp3"),
                "module_gap": os.path.join(directory, "module-gap.mp3"),
                "amen_gap": os.path.join(directory, "amen-gap.mp3"),
            }
            for path in paths.values():
                with open(path, "wb") as handle:
                    handle.write(b"audio")

            durations = {
                paths["first"]: 1.0,
                paths["second"]: 2.0,
                paths["group_gap"]: 0.5,
                paths["module_gap"]: 1.35,
                paths["amen_gap"]: 0.03,
            }

            def fake_mp3(path):
                result = MagicMock()
                result.info.length = durations.get(path, 4.35)
                return result

            def fake_silence(seconds):
                return {
                    0.5: paths["group_gap"],
                    1.35: paths["module_gap"],
                    0.03: paths["amen_gap"],
                }[seconds]

            def fake_ffmpeg(command, **_kwargs):
                with open(command[-1], "wb") as handle:
                    handle.write(b"combined")
                return MagicMock(returncode=0, stderr="")

            tracks = [
                {
                    "path": "/first.mp3",
                    "module": "Opening",
                    "line_id": "line-one",
                    "word_timing": [
                        {
                            "id": "line-one",
                            "speaker": "leader",
                            "word": "Grace",
                            "start_time": 0.1,
                            "end_time": 0.4,
                        }
                    ],
                },
                {
                    "path": "/second.mp3",
                    "module": "Psalm",
                    "line_id": "line-two",
                    "word_timing": [
                        {
                            "id": "line-two",
                            "speaker": "reader",
                            "word": "Peace",
                            "start_time": 0.2,
                            "end_time": 0.6,
                        }
                    ],
                },
            ]

            with (
                override_settings(
                    BASE_DIR=directory,
                    MEDIA_ROOT=directory,
                    MEDIA_URL="/",
                    SITE_ADDRESS="https://example.test",
                ),
                patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
                patch.object(index, "MP3", side_effect=fake_mp3),
                patch.object(
                    index.GenericDailyOfficeSerializer,
                    "get_silence_clip",
                    side_effect=fake_silence,
                ),
                patch.object(index.subprocess, "run", side_effect=fake_ffmpeg),
                patch.object(index, "generate_uuid_from_string", return_value="full"),
            ):
                result = index.GenericDailyOfficeSerializer.get_single_track(tracks)

        self.assertEqual(result[2][1]["start_time"], 2.35)
        self.assertEqual(result[4][0]["start_time"], 0.1)
        self.assertEqual(result[4][0]["speaker"], "leader")
        self.assertAlmostEqual(result[4][1]["start_time"], 2.55)
        self.assertAlmostEqual(result[4][1]["end_time"], 2.95)


class RebuildAudioClipCommandTests(TestCase):
    def test_clear_provider_uses_versioned_openai_media_subdir(self):
        with tempfile.TemporaryDirectory() as directory:
            provider_dir = os.path.join(directory, "openai_v2")
            os.makedirs(provider_dir)
            audio_path = os.path.join(provider_dir, "clip.mp3")
            sidecar_path = f"{audio_path}.json"
            for path in (audio_path, sidecar_path):
                with open(path, "wb") as handle:
                    handle.write(b"data")
            AudioClip.objects.create(
                key="openai-clip",
                filename="openai_v2/clip.mp3",
                provider="openai",
            )

            with override_settings(MEDIA_ROOT=directory):
                call_command(
                    "rebuild_audio_clip",
                    "--clear-provider",
                    "openai",
                    "--execute",
                    stdout=StringIO(),
                )

            self.assertFalse(os.path.exists(audio_path))
            self.assertFalse(os.path.exists(sidecar_path))
            self.assertFalse(AudioClip.objects.filter(key="openai-clip").exists())

    def test_prune_orphans_scans_versioned_openai_media_subdir(self):
        with tempfile.TemporaryDirectory() as directory:
            provider_dir = os.path.join(directory, "openai_v2")
            os.makedirs(provider_dir)
            orphan_path = os.path.join(provider_dir, "orphan.mp3")
            with open(orphan_path, "wb") as handle:
                handle.write(b"orphan")

            with override_settings(MEDIA_ROOT=directory):
                call_command(
                    "rebuild_audio_clip",
                    "--prune-orphans",
                    "--execute",
                    stdout=StringIO(),
                )

            self.assertFalse(os.path.exists(orphan_path))

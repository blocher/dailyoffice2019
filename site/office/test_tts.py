import base64
import os
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider, GeminiTTSProvider
from office.models import AudioClip, PronunciationOverride


class ReadingVoiceTests(SimpleTestCase):
    @override_settings(
        ELEVENLABS_TTS_MODEL="eleven_v4",
        ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"),
        ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
        GEMINI_TTS_VOICES_READER=("Kore", "Charon"),
    )
    def test_complete_reading_keeps_one_voice_through_audio_assembly(self):
        from types import SimpleNamespace
        from office.elevenlabs_dialogue import DialogueSession

        for provider in (ElevenLabsTTSProvider(), GeminiTTSProvider()):
            with self.subTest(provider=provider.name), tempfile.TemporaryDirectory() as directory:
                module = SimpleNamespace(
                    office=SimpleNamespace(
                        office_readings=SimpleNamespace(reading="Genesis 1:1-2", reading_testament="OT"),
                        readings={"Genesis 1:1-2": SimpleNamespace(esv="<p>In the beginning.</p><p>The earth.</p>")},
                    ),
                    language="english",
                    remove_headings_if_needed=lambda text: text,
                    get_safe_name=lambda: "firstreading",
                    audio=lambda *args: None,
                    closing=index.ReadingModule.closing,
                    closing_response=index.ReadingModule.closing_response,
                )
                serializer = index.GenericDailyOfficeSerializer()
                voices = []

                def clip(content, line_type, **kwargs):
                    if line_type == "reader" and not kwargs.get("no_generate"):
                        voices.append(kwargs.get("voice"))
                    return "/uploads/11111111-1111-1111-1111-111111111111.mp3", "/uploads/reader.mp3"

                def dialogue_clip(session, lines):
                    voices.extend(line.get("audio_voice") for line in lines if line["line_type"] == "reader")
                    return "/uploads/dialogue.mp3", []

                with (
                    override_settings(MEDIA_ROOT=directory),
                    patch.object(index, "TTS_PROVIDER", provider),
                    patch.object(serializer, "normalize_tts_text", side_effect=lambda text: text),
                    patch.object(
                        index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda text: text
                    ),
                    patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", side_effect=clip),
                    patch.object(index.GenericDailyOfficeSerializer, "get_clip_word_timing", return_value=[]),
                    patch.object(DialogueSession, "clip", dialogue_clip),
                    patch.object(index, "frame_tracks", side_effect=lambda office, tracks, *args: tracks),
                    patch.object(serializer, "get_single_track", return_value=[]),
                ):
                    lines = index.ReadingModule.get_reading(module, "reading")
                    for position, line in enumerate(lines):
                        line["id"] = f"firstreading_{position}"
                    with patch.object(
                        serializer, "get_modules", return_value=[{"name": "First Reading", "lines": lines}]
                    ):
                        serializer.get_audio(SimpleNamespace(settings={}))
                self.assertEqual(len(voices), 4)
                self.assertNotIn(None, voices)
                self.assertEqual(len(set(voices)), 1)

    def test_explicit_reading_voice_bypasses_other_cached_readers(self):
        with (
            patch.object(index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda text: text),
            patch.object(index.GenericDailyOfficeSerializer, "find_reusable_reader") as reusable,
            patch.object(index.os.path, "isfile", return_value=False),
            patch.object(index.TTS_PROVIDER, "voice_for_text") as choose_voice,
        ):
            _, path = index.GenericDailyOfficeSerializer._get_or_create_clip(
                "The Word of the Lord.", "reader", voice="assigned-reader", no_generate=True
            )
            key = index.GenericDailyOfficeSerializer.tts_clip_key("assigned-reader", "The Word of the Lord.")
        self.assertIn(str(key), path)
        reusable.assert_not_called()
        choose_voice.assert_not_called()


@override_settings(ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="", ELEVENLABS_PRONUNCIATION_DICTIONARY_VERSION_ID="")
class ElevenLabsTTSProviderTests(SimpleTestCase):
    @override_settings(ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"))
    def test_reading_paragraphs_share_one_explicit_voice(self):
        provider = ElevenLabsTTSProvider()
        with (
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=(None, None)) as clip,
        ):
            index.GenericDailyOfficeSerializer.handle_html(
                "<p>First paragraph.</p><p>Second paragraph.</p>", voice="reader-two"
            )
        self.assertEqual(clip.call_count, 2)
        self.assertTrue(all(call.kwargs["voice"] == "reader-two" for call in clip.call_args_list))

    @override_settings(ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"))
    def test_complete_reading_assigns_intro_body_and_closing_one_reader(self):
        from types import SimpleNamespace

        provider = ElevenLabsTTSProvider()
        module = SimpleNamespace(
            office=SimpleNamespace(
                office_readings=SimpleNamespace(reading="Genesis 1:1-2", reading_testament="OT"),
                readings={
                    "Genesis 1:1-2": SimpleNamespace(esv="<p>In the beginning.</p><p>The earth was without form.</p>")
                },
            ),
            language="english",
            remove_headings_if_needed=lambda text: text,
            get_safe_name=lambda: "firstreading",
            audio=lambda *args: None,
            closing=index.ReadingModule.closing,
            closing_response=index.ReadingModule.closing_response,
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda text: text),
            patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=(None, None)) as clip,
        ):
            lines = index.ReadingModule.get_reading(module, "reading")
            assigned = {line["audio_voice"] for line in lines if line["line_type"] in {"reader", "html"}}
            self.assertEqual(len(assigned), 1)
            voice = assigned.pop()
            self.assertTrue(all(call.kwargs["voice"] == voice for call in clip.call_args_list))
            reader_lines = [line for line in lines if line["line_type"] == "reader"]
            self.assertEqual(len(reader_lines), 2)
            self.assertEqual(reader_lines[-1]["content"], "The Word of the Lord.")
            self.assertNotIn("audio_voice", next(line for line in lines if line["line_type"] == "congregation"))

    @override_settings(ELEVENLABS_TTS_VOICES_READER=("reader-one", "reader-two"))
    def test_reading_assignment_varies_by_passage_and_survives_pool_changes(self):
        provider = ElevenLabsTTSProvider()
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda text: text),
        ):
            voices = [index.GenericDailyOfficeSerializer.reading_voice(f"Passage {i}") for i in range(20)]
            self.assertEqual(set(voices), {"reader-one", "reader-two"})
            with override_settings(ELEVENLABS_TTS_VOICES_READER=("different",)):
                self.assertEqual(index.GenericDailyOfficeSerializer.reading_voice("Passage 0"), voices[0])

    def test_reader_reuse_rejects_previous_pacing_or_model(self):
        provider = ElevenLabsTTSProvider()
        stale = MagicMock(key="old-signature", voice="reader", file_path="clip.mp3")
        with (
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(AudioClip.objects, "filter") as clips,
            patch.object(index.os.path, "isfile", return_value=True),
            patch.object(index.os.path, "getsize", return_value=100),
        ):
            clips.return_value.order_by.return_value = [stale]
            self.assertIsNone(index.GenericDailyOfficeSerializer.find_reusable_reader("Amen", "reader"))
            stale.key = index.GenericDailyOfficeSerializer.tts_clip_key("reader", "Amen")
            self.assertIs(index.GenericDailyOfficeSerializer.find_reusable_reader("Amen", "reader"), stale)

    def test_elevenlabs_persists_direct_timings_without_google_alignment(self):
        provider = ElevenLabsTTSProvider()
        timing = [{"word": "Amen", "start_time": 0.1, "end_time": 0.8}]
        with (
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(provider, "synthesize", return_value=timing),
            patch.object(index.GenericDailyOfficeSerializer, "save_word_timing") as save,
            patch("office.gemini_alignment.align_clip") as google_align,
        ):
            result = index.GenericDailyOfficeSerializer.synthesize_speech("voice", "Amen", "clip.mp3")
        self.assertEqual(result, timing)
        save.assert_called_once_with("clip.mp3", timing)
        google_align.assert_not_called()

    @override_settings(
        ELEVENLABS_TTS_MODEL="eleven_v4",
        ELEVENLABS_TTS_INSTRUCTIONS="calm, reverent, measured delivery",
        ELEVENLABS_TTS_AMEN_IPA="ɑːˈmɛn",
    )
    def test_v4_steering_ipa_and_original_word_offsets(self):
        provider = ElevenLabsTTSProvider()
        original = "Amen, amen! Amend this. AMEN."
        submitted, positions = provider.prepare_text(original)
        self.assertTrue(submitted.startswith("[calm]\n"))
        self.assertEqual(submitted.count("/ɑːˈmɛn/"), 3)
        self.assertIn("Amend this", submitted)
        alignment = {
            "characters": list(submitted),
            "character_start_times_seconds": [i / 10 for i in range(len(submitted))],
            "character_end_times_seconds": [(i + 1) / 10 for i in range(len(submitted))],
        }
        words = provider.original_word_alignment(alignment, original, submitted, positions)
        self.assertEqual([w["word"] for w in words], ["Amen", "amen", "Amend", "this", "AMEN"])
        for word in words:
            self.assertEqual(original[word["char_start"] : word["char_end"]], word["word"])
        self.assertEqual(words[0]["start_time"], submitted.index("/ɑːˈmɛn/") / 10)
        self.assertAlmostEqual(words[0]["end_time"] - words[0]["start_time"], len("/ɑːˈmɛn/") / 10)
        signature = provider.cache_signature()
        with override_settings(ELEVENLABS_TTS_AMEN_IPA="different"):
            self.assertNotEqual(signature, provider.cache_signature())
        alignment["characters"][0] = "?"
        self.assertEqual(provider.original_word_alignment(alignment, original, submitted, positions), [])

    @override_settings(ELEVENLABS_TTS_MODEL="eleven_multilingual_v2")
    def test_legacy_model_keeps_text_unchanged(self):
        provider = ElevenLabsTTSProvider()
        self.assertEqual(provider.prepare_text("Amen."), ("Amen.", list(range(5))))
        self.assertEqual(provider.effective_instructions, "")

    @override_settings(ELEVENLABS_TTS_MODEL="eleven_v4", ELEVENLABS_API_KEY="test-key", ELEVENLABS_TTS_MAX_RETRIES=0)
    @patch("office.api.views.tts.requests.post")
    def test_v4_synthesis_sends_prepared_text_and_preserves_alignment(self, post):
        provider = ElevenLabsTTSProvider()
        submitted, _ = provider.prepare_text("Amen.")
        post.return_value.json.return_value = {
            "audio_base64": base64.b64encode(b"audio").decode(),
            "alignment": {
                "characters": list(submitted),
                "character_start_times_seconds": [0.0] * len(submitted),
                "character_end_times_seconds": [1.0] * len(submitted),
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            words = provider.synthesize("voice", "Amen.", os.path.join(directory, "test.mp3"))
        self.assertEqual(post.call_args.kwargs["json"]["text"], submitted)
        self.assertEqual([w["word"] for w in words], ["Amen"])

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
        self.assertNotIn("pronunciation_dictionary_locators", request.kwargs["json"])

    def test_flash_v2_5_is_a_documented_model_option(self):
        self.assertIn("eleven_flash_v2_5", ElevenLabsTTSProvider.MODELS)
        self.assertIn("eleven_flash_v2", ElevenLabsTTSProvider.MODELS)

    @override_settings(
        ELEVENLABS_API_KEY="test-key",
        ELEVENLABS_TTS_MODEL="eleven_flash_v2_5",
        ELEVENLABS_TTS_MAX_RETRIES=0,
        ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="dict-1",
        ELEVENLABS_PRONUNCIATION_DICTIONARY_VERSION_ID="ver-1",
    )
    @patch("office.api.views.tts.requests.post")
    def test_synthesize_sends_flash_model_and_pronunciation_dictionary(self, post):
        response = MagicMock()
        response.json.return_value = {
            "audio_base64": base64.b64encode(b"mp3-data").decode(),
            "alignment": {
                "characters": ["A"],
                "character_start_times_seconds": [0.0],
                "character_end_times_seconds": [0.1],
            },
        }
        post.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "clip.mp3")
            ElevenLabsTTSProvider().synthesize("voice-id", "Amen", path)

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model_id"], "eleven_flash_v2_5")
        self.assertEqual(
            payload["pronunciation_dictionary_locators"],
            [{"pronunciation_dictionary_id": "dict-1", "version_id": "ver-1"}],
        )
        self.assertEqual(
            ElevenLabsTTSProvider().cache_signature(),
            "eleven_flash_v2_5 1.0 dict-1:ver-1",
        )


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
                key=index.generate_uuid_from_string(
                    f"old-reader {ElevenLabsTTSProvider().cache_signature()} The Word of the Lord."
                ),
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


class PronunciationOverrideProviderTests(TestCase):
    def test_openai_only_amen_rule_leaves_elevenlabs_text_alone(self):
        PronunciationOverride.objects.create(
            match="Amen",
            replacement="Ah-men",
            providers="openai",
            enabled=True,
            order=20,
        )

        self.assertEqual(PronunciationOverride.apply("Amen.", provider="openai"), "Ah-men.")
        self.assertEqual(PronunciationOverride.apply("Amen.", provider="elevenlabs"), "Amen.")
        self.assertEqual(PronunciationOverride.apply("Amen."), "Amen.")


class CombinedTrackTimingTests(SimpleTestCase):
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
        self.assertEqual(result[4][0]["provider"], "elevenlabs")
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

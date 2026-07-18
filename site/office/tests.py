import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from office.audio.eligibility import check_audio_eligibility
from office.audio.pipeline import (
    PIPELINE_GEMINI,
    PIPELINE_LEGACY,
    PIPELINE_V2,
    get_audio_pipeline,
    set_audio_pipeline,
)
from office.audio.v2 import ROLE_VOICES, _gap_ms, assemble_full_track, build_v2_audio, voice_for_line_type
from office.models import Scripture


class UpdateAudioFilesCommandTests(TestCase):
    def test_date_list_can_exclude_yesterday(self):
        from office.management.commands.update_audio_files import Command

        now = datetime(2026, 7, 18, 12, tzinfo=timezone.utc)

        dates = Command._date_list(now, days=2, include_yesterday=False)

        self.assertEqual([date.date().isoformat() for date in dates], ["2026-07-18", "2026-07-19"])

    def test_date_list_includes_yesterday_by_default(self):
        from office.management.commands.update_audio_files import Command

        now = datetime(2026, 7, 18, 12, tzinfo=timezone.utc)

        dates = Command._date_list(now, days=2, include_yesterday=True)

        self.assertEqual(
            [date.date().isoformat() for date in dates],
            ["2026-07-17", "2026-07-18", "2026-07-19"],
        )

    def test_days_must_be_positive(self):
        from office.management.commands.update_audio_files import Command

        with self.assertRaises(CommandError):
            Command().handle(days=0, pipeline="gemini", no_yesterday=True)

    def test_batch_submit_persists_pending_jobs(self):
        from office.audio.gemini import BatchChunk
        from office.management.commands.update_audio_files import Command
        from office.models import AudioBatchJob

        chunks = [BatchChunk(cache_key="k1", prompt="p", file_path="/tmp/k1.mp3", spoken_chars=10)]
        records = [
            {
                "job_name": "batches/1",
                "model_name": "gemini-3.1-flash-tts-preview",
                "chunks": [{"cache_key": "k1", "file_path": "/tmp/k1.mp3", "spoken_chars": 10}],
            }
        ]
        command = Command()
        # kronos.register duplicates the command class, so patch the instance directly.
        command._collect_batch_chunks = MagicMock(return_value=chunks)
        with patch("office.audio.gemini_batch.submit_chunks", return_value=records):
            command._batch_submit(days=1, include_yesterday=False)

        job = AudioBatchJob.objects.get(job_name="batches/1")
        self.assertEqual(job.status, AudioBatchJob.STATUS_PENDING)
        self.assertEqual(job.chunks[0]["cache_key"], "k1")

    def test_batch_fetch_marks_completed_jobs(self):
        from office.management.commands.update_audio_files import Command
        from office.models import AudioBatchJob

        AudioBatchJob.objects.create(
            job_name="batches/2",
            chunks=[{"cache_key": "k", "file_path": "/tmp/k.mp3", "spoken_chars": 10}],
            status=AudioBatchJob.STATUS_PENDING,
        )
        result = {"state": "JOB_STATE_SUCCEEDED", "terminal": True, "succeeded": True, "written": 1, "failed": 0}
        command = Command()
        with patch("office.audio.gemini_batch.fetch_job", return_value=result):
            command._batch_fetch()

        job = AudioBatchJob.objects.get(job_name="batches/2")
        self.assertEqual(job.status, AudioBatchJob.STATUS_SUCCEEDED)
        self.assertEqual(job.written, 1)
        self.assertIsNotNone(job.completed_at)

    def test_batch_fetch_leaves_running_jobs_pending(self):
        from office.management.commands.update_audio_files import Command
        from office.models import AudioBatchJob

        AudioBatchJob.objects.create(
            job_name="batches/3",
            chunks=[{"cache_key": "k", "file_path": "/tmp/k.mp3", "spoken_chars": 10}],
            status=AudioBatchJob.STATUS_PENDING,
        )
        result = {"state": "JOB_STATE_RUNNING", "terminal": False, "succeeded": False, "written": 0, "failed": 0}
        command = Command()
        with patch("office.audio.gemini_batch.fetch_job", return_value=result):
            command._batch_fetch()

        job = AudioBatchJob.objects.get(job_name="batches/3")
        self.assertEqual(job.status, AudioBatchJob.STATUS_PENDING)
        self.assertEqual(job.last_state, "JOB_STATE_RUNNING")


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


class AudioEligibilityTests(TestCase):
    def test_english_esv_is_eligible(self):
        result = check_audio_eligibility(
            {
                "display_language": "english",
                "language_style": "contemporary",
                "psalm_translation": "contemporary",
                "bible_translation": "esv",
            }
        )
        self.assertTrue(result.available)

    def test_traditional_kjv_is_eligible(self):
        result = check_audio_eligibility(
            {
                "display_language": "english",
                "language_style": "traditional",
                "psalm_translation": "traditional",
                "bible_translation": "kjv",
            }
        )
        self.assertTrue(result.available)

    def test_chinese_display_blocked(self):
        result = check_audio_eligibility(
            {
                "display_language": "chinese-traditional",
                "language_style": "contemporary",
                "psalm_translation": "contemporary",
                "bible_translation": "esv",
            }
        )
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "display_language")
        self.assertIn("still in progress", result.message)

    def test_non_esv_kjv_blocked(self):
        result = check_audio_eligibility(
            {
                "display_language": "english",
                "language_style": "contemporary",
                "psalm_translation": "contemporary",
                "bible_translation": "nrsvce",
            }
        )
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "bible_translation")


class AudioPipelineSwitchTests(TestCase):
    def tearDown(self):
        set_audio_pipeline(None)

    @override_settings(OFFICE_AUDIO_PIPELINE="legacy")
    def test_settings_pipeline_legacy(self):
        self.assertEqual(get_audio_pipeline(), PIPELINE_LEGACY)

    @override_settings(OFFICE_AUDIO_PIPELINE="v2")
    def test_override_takes_precedence(self):
        set_audio_pipeline(PIPELINE_LEGACY)
        self.assertEqual(get_audio_pipeline(), PIPELINE_LEGACY)
        set_audio_pipeline(None)
        self.assertEqual(get_audio_pipeline(), PIPELINE_V2)

    @override_settings(OFFICE_AUDIO_PIPELINE="gemini")
    def test_settings_pipeline_gemini(self):
        self.assertEqual(get_audio_pipeline(), PIPELINE_GEMINI)

    def test_build_gemini_batches_dialogue_into_multispeaker_chunks(self):
        from office.audio.gemini import AUDIO_GEMINI_SUBDIR, build_gemini_audio

        fake_clip = MagicMock(
            line_id="a",
            module_name="",
            role="leader",
            end_role="congregation",
            kind="spoken",
            url="https://example.com/a.mp3",
            media_path="/uploads/audio_gemini/clips/a.mp3",
            duration=1.0,
            line_segments=[{"id": "a", "chars": 10}, {"id": "b", "chars": 5}],
        )
        with (
            patch("office.audio.gemini.generate_gemini_dialogue_clip", return_value=fake_clip) as synth,
            patch("office.audio.v2.assemble_full_track") as assemble,
        ):
            assemble.return_value = (
                "https://example.com/api/v1/audio_track/audio_gemini/full/x.mp3",
                "/uploads/audio_gemini/full/x.mp3",
                [{"name": "M", "start_time": 0}],
                [{"id": "a", "start_time": 0, "duration": 1.0}],
            )
            result = build_gemini_audio(
                [
                    {
                        "name": "M",
                        "lines": [
                            {"id": "a", "line_type": "leader", "content": "O Lord, open our lips."},
                            {"id": "b", "line_type": "congregation", "content": "And our mouth shall proclaim."},
                        ],
                    }
                ]
            )
            self.assertTrue(result["available"])
            # Leader + congregation dialogue is one multi-speaker request.
            self.assertEqual(synth.call_count, 1)
            items = synth.call_args[0][0]
            self.assertEqual([item["role"] for item in items], ["leader", "congregation"])
            self.assertTrue(any("/audio_gemini/" in (c.media_path or "") for c in assemble.call_args[0][0]))
            self.assertEqual(AUDIO_GEMINI_SUBDIR, "audio_gemini")
            from office.audio.v2 import get_audio_subdir

            self.assertEqual(get_audio_subdir(), "audio_v2")  # reset after context

    def test_build_gemini_includes_dialogue_line_types(self):
        from office.audio.gemini import build_gemini_audio

        fake_clip = MagicMock(
            line_id="a",
            module_name="",
            role="leader",
            end_role="congregation",
            kind="spoken",
            url="https://example.com/a.mp3",
            media_path="/uploads/audio_gemini/clips/a.mp3",
            duration=1.0,
            line_segments=[{"id": "a", "chars": 10}, {"id": "b", "chars": 5}],
        )
        with (
            patch("office.audio.gemini.generate_gemini_dialogue_clip", return_value=fake_clip) as synth,
            patch("office.audio.v2.assemble_full_track") as assemble,
        ):
            assemble.return_value = (
                "https://example.com/api/v1/audio_track/audio_gemini/full/x.mp3",
                "/uploads/audio_gemini/full/x.mp3",
                [{"name": "M", "start_time": 0}],
                [{"id": "a", "start_time": 0, "duration": 1.0}],
            )
            result = build_gemini_audio(
                [
                    {
                        "name": "M",
                        "lines": [
                            {"id": "a", "line_type": "leader_dialogue", "content": "O Lord, open our lips."},
                            {
                                "id": "b",
                                "line_type": "congregation_dialogue",
                                "content": "And our mouth shall proclaim.",
                            },
                        ],
                    }
                ]
            )
            self.assertTrue(result["available"])
            # Dialogue variants collapse to leader/congregation and stay in one chunk.
            self.assertEqual(synth.call_count, 1)
            items = synth.call_args[0][0]
            self.assertEqual([item["role"] for item in items], ["leader", "congregation"])

    def test_role_for_line_type_collapses_dialogue_variants(self):
        from office.audio.v2 import role_for_line_type

        self.assertEqual(role_for_line_type("leader_dialogue"), "leader")
        self.assertEqual(role_for_line_type("congregation_dialogue"), "congregation")
        self.assertEqual(role_for_line_type("leader"), "leader")
        self.assertEqual(role_for_line_type("congregation"), "congregation")
        self.assertEqual(role_for_line_type("html"), "reader")
        self.assertEqual(role_for_line_type("reader"), "reader")

    def test_gemini_cache_key_is_text_only(self):
        from office.audio.gemini import _dialogue_turns, _segment_cache_key, _segment_transcript

        items = [
            {"line_id": "a", "text": "O Lord, open our lips.", "role": "leader"},
            {"line_id": "a2", "text": "Continue without an extra pause.", "role": "leader"},
            {"line_id": "b", "text": "And our mouth shall proclaim.", "role": "congregation"},
        ]
        transcript = _segment_transcript(items)
        self.assertIn("Leader: O Lord, open our lips. Continue without an extra pause.", transcript)
        self.assertIn("Congregation: And our mouth shall proclaim.", transcript)
        self.assertEqual(len(_dialogue_turns(items)), 2)
        # Key depends only on the segment text, not voices or model.
        self.assertEqual(_segment_cache_key(transcript), _segment_cache_key(transcript))
        self.assertNotEqual(_segment_cache_key(transcript), _segment_cache_key(transcript + " changed"))

    def test_gemini_randomizes_reader_voice_only_on_cache_miss(self):
        from office.audio.gemini import READER_VOICES, generate_gemini_dialogue_clip

        items = [{"line_id": "reading", "text": "A unique test reading.", "role": "reader"}]

        def write_fake_audio(prompt, roles, voices, file_path, spoken_chars):
            with open(file_path, "wb") as audio_file:
                audio_file.write(b"fake mp3")

        with (
            tempfile.TemporaryDirectory() as media_root,
            override_settings(
                MEDIA_ROOT=media_root,
                MEDIA_URL="/uploads/",
                SITE_ADDRESS="https://127.0.0.1:8000",
            ),
            patch("office.audio.gemini.random.choice", return_value="Leda") as choose,
            patch("office.audio.gemini._synthesize_to_mp3", side_effect=write_fake_audio) as synthesize,
            patch("office.audio.gemini.audio_duration", return_value=1.0),
        ):
            generate_gemini_dialogue_clip(items)
            generate_gemini_dialogue_clip(items)

        choose.assert_called_once_with(READER_VOICES)
        synthesize.assert_called_once()
        self.assertEqual(synthesize.call_args.args[2], {"reader": "Leda"})

    def test_gemini_keeps_leader_and_congregation_voices_fixed(self):
        from office.audio.gemini import ROLE_VOICES as GEMINI_ROLE_VOICES
        from office.audio.gemini import _voices_for_generation

        with patch("office.audio.gemini.random.choice") as choose:
            voices = _voices_for_generation(["leader", "congregation"])

        choose.assert_not_called()
        self.assertEqual(
            voices,
            {
                "leader": GEMINI_ROLE_VOICES["leader"],
                "congregation": GEMINI_ROLE_VOICES["congregation"],
            },
        )

    def test_gemini_rejects_implausible_clip_durations(self):
        from office.audio.gemini import PCM_SAMPLE_RATE, _check_duration_plausible

        def pcm_for_seconds(seconds):
            return b"\x00" * int(seconds * 2 * PCM_SAMPLE_RATE)

        # ~120 chars spoken in ~10s is a normal reading pace: accepted.
        _check_duration_plausible(pcm_for_seconds(10), 120)
        # 145s of audio for a 120-char intro means the model recited beyond
        # the provided text (the bug that mixed translations): rejected.
        with self.assertRaises(RuntimeError):
            _check_duration_plausible(pcm_for_seconds(145), 120)
        # 1s of audio for 1400 chars means the clip was truncated: rejected.
        with self.assertRaises(RuntimeError):
            _check_duration_plausible(pcm_for_seconds(1), 1400)

    def test_gemini_extract_pcm_reports_finish_reason_when_no_audio(self):
        from office.audio.gemini import _extract_pcm

        # Capped runaway: candidate present but content/parts are None.
        response = MagicMock()
        response.candidates = [MagicMock(content=None, finish_reason="MAX_TOKENS")]
        with self.assertRaises(RuntimeError) as ctx:
            _extract_pcm(response)
        self.assertIn("MAX_TOKENS", str(ctx.exception))

        # No candidates at all.
        response.candidates = []
        with self.assertRaises(RuntimeError):
            _extract_pcm(response)

        # Normal audio response passes through.
        part = MagicMock()
        part.inline_data.data = b"pcm-bytes"
        response.candidates = [MagicMock(content=MagicMock(parts=[part]))]
        self.assertEqual(_extract_pcm(response), b"pcm-bytes")

    def test_gemini_output_token_cap_scales_with_text_length(self):
        from office.audio.gemini import AUDIO_TOKENS_PER_SECOND, _max_output_tokens

        # Cap tracks the plausible-duration ceiling (6s base + 1s per 6 chars).
        self.assertEqual(_max_output_tokens(0), 6 * AUDIO_TOKENS_PER_SECOND)
        self.assertEqual(_max_output_tokens(600), int((6 + 100) * AUDIO_TOKENS_PER_SECOND))
        # A normal reading (~15 chars/sec) stays well under the cap.
        self.assertGreater(_max_output_tokens(600), (600 / 15) * 35)

    def test_gemini_temperature_defaults_and_reads_setting(self):
        from office.audio.gemini import gemini_temperature

        with override_settings(GEMINI_TTS_TEMPERATURE="0.7"):
            self.assertEqual(gemini_temperature(), 0.7)
        with override_settings(GEMINI_TTS_TEMPERATURE="0.9"):
            self.assertEqual(gemini_temperature(), 0.9)
        # Blank/invalid values fall back to the safe default rather than raising.
        with override_settings(GEMINI_TTS_TEMPERATURE=""):
            self.assertEqual(gemini_temperature(), 0.7)
        with override_settings(GEMINI_TTS_TEMPERATURE="not-a-number"):
            self.assertEqual(gemini_temperature(), 0.7)

    def test_gemini_prompt_requires_one_spoken_congregation_voice(self):
        from office.audio.gemini import _build_prompt

        items = [
            {"line_id": "a", "text": "The Lord be with you.", "role": "leader"},
            {"line_id": "b", "text": "And with your spirit.", "role": "congregation"},
        ]
        prompt = _build_prompt(items, ["leader", "congregation"])
        # Documented "TTS the following..." shape; sectioned prompts trigger 400s.
        self.assertTrue(prompt.startswith("TTS the following Daily Office dialogue between Leader and Congregation."))
        self.assertIn("one single solo respondent, not a crowd", prompt)
        self.assertIn("Never sing, chant, harmonize, layer voices", prompt)
        self.assertIn("Leader: The Lord be with you.", prompt)
        self.assertIn("Congregation: And with your spirit.", prompt)
        # Explicit transcript boundaries keep the model from reciting past the text.
        self.assertIn("BEGIN_TRANSCRIPT", prompt)
        self.assertIn("END_TRANSCRIPT", prompt)
        self.assertIn("stop immediately after the last word", prompt)
        # The spoken transcript sits inside the final BEGIN/END marker block
        # (the marker words also appear once in the boundary instructions above).
        transcript_body = prompt.rsplit("BEGIN_TRANSCRIPT", 1)[1].rsplit("END_TRANSCRIPT", 1)[0]
        self.assertIn("Leader: The Lord be with you.", transcript_body)
        self.assertIn("Congregation: And with your spirit.", transcript_body)

    def test_gemini_reader_voice_is_consistent_across_an_office(self):
        from office.audio.gemini import READER_VOICES, _office_reader_voice

        modules = [
            {"name": "Psalm", "lines": [{"id": "p1", "content": "Bless the Lord, O my soul."}]},
            {"name": "Lesson", "lines": [{"id": "l1", "content": "In the beginning was the Word."}]},
        ]
        voice = _office_reader_voice(modules)
        # Deterministic: same office always resolves to the same reader voice.
        self.assertIn(voice, READER_VOICES)
        self.assertEqual(voice, _office_reader_voice(modules))
        # Different content can resolve to a different voice from the pool.
        other = _office_reader_voice([{"name": "Other", "lines": [{"id": "x", "content": "Different text."}]}])
        self.assertIn(other, READER_VOICES)

    def test_gemini_voices_use_context_reader_voice_without_randomizing(self):
        from office.audio.gemini import _reader_voice, _voices_for_generation

        token = _reader_voice.set("Orus")
        try:
            with patch("office.audio.gemini.random.choice") as choose:
                voices = _voices_for_generation(["reader"])
            choose.assert_not_called()
            self.assertEqual(voices["reader"], "Orus")
        finally:
            _reader_voice.reset(token)

    def test_gemini_extract_pcm_rejects_truncated_max_tokens_audio(self):
        from office.audio.gemini import _extract_pcm

        # Partial audio returned alongside finish_reason=MAX_TOKENS is a truncated
        # or runaway clip and must be rejected, not cached.
        part = MagicMock()
        part.inline_data.data = b"partial-pcm"
        response = MagicMock()
        response.candidates = [MagicMock(content=MagicMock(parts=[part]), finish_reason="MAX_TOKENS")]
        with self.assertRaises(RuntimeError) as ctx:
            _extract_pcm(response)
        self.assertIn("MAX_TOKENS", str(ctx.exception))

    def test_gemini_collect_mode_records_misses_without_synthesizing(self):
        from office.audio.gemini import collecting_batch_chunks, generate_gemini_dialogue_clip

        items = [{"line_id": "r", "text": "A unique batch reading.", "role": "reader"}]
        with (
            tempfile.TemporaryDirectory() as media_root,
            override_settings(MEDIA_ROOT=media_root, MEDIA_URL="/uploads/", SITE_ADDRESS="https://127.0.0.1:8000"),
            patch("office.audio.gemini._synthesize_to_mp3") as synthesize,
        ):
            with collecting_batch_chunks() as collector:
                first = generate_gemini_dialogue_clip(items)
                second = generate_gemini_dialogue_clip(items)  # identical text: deduped
            chunks = collector.chunks()

        # Collection never synthesizes and never returns a clip (so no assembly).
        synthesize.assert_not_called()
        self.assertIsNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(chunks), 1)
        self.assertIn("BEGIN_TRANSCRIPT", chunks[0].prompt)
        self.assertTrue(chunks[0].file_path.endswith(".mp3"))
        self.assertEqual(chunks[0].roles, ["reader"])

    def test_gemini_run_batch_synthesis_writes_successful_clips(self):
        from office.audio import gemini_batch
        from office.audio.gemini import BatchChunk, PCM_SAMPLE_RATE

        chunk = BatchChunk(
            cache_key="k1",
            prompt="prompt",
            file_path="/tmp/dailyoffice-batch-test.mp3",
            spoken_chars=20,
            roles=["reader"],
            voices={"reader": "Leda"},
        )
        plausible_pcm = b"\x00" * (2 * 2 * PCM_SAMPLE_RATE)  # ~2s of audio
        part = MagicMock()
        part.inline_data.data = plausible_pcm
        response = MagicMock()
        response.candidates = [MagicMock(content=MagicMock(parts=[part]), finish_reason="STOP")]
        inline_item = MagicMock(response=response, error=None)
        job = MagicMock(name="jobs/test")
        job.state.name = "JOB_STATE_SUCCEEDED"
        job.dest.inlined_responses = [inline_item]
        job.dest.file_name = None
        client = MagicMock()
        client.batches.create.return_value = job

        with (
            patch("office.audio.gemini_batch._genai_client", return_value=client),
            patch("office.audio.gemini_batch.build_generate_content_config", return_value={}),
            patch("office.audio.gemini_batch.encode_pcm_to_mp3") as encode,
        ):
            summary = gemini_batch.run_batch_synthesis([chunk])

        self.assertEqual(summary, {"requested": 1, "written": 1, "failed": 0})
        encode.assert_called_once()
        self.assertEqual(encode.call_args.args[1], "/tmp/dailyoffice-batch-test.mp3")

    def test_gemini_run_batch_synthesis_counts_bad_responses_as_failures(self):
        from office.audio import gemini_batch
        from office.audio.gemini import BatchChunk

        chunk = BatchChunk(
            cache_key="k2", prompt="p", file_path="/tmp/x.mp3", spoken_chars=20, roles=["reader"], voices={}
        )
        inline_item = MagicMock(response=None, error="quota exceeded")
        job = MagicMock()
        job.state.name = "JOB_STATE_SUCCEEDED"
        job.dest.inlined_responses = [inline_item]
        job.dest.file_name = None
        client = MagicMock()
        client.batches.create.return_value = job

        with (
            patch("office.audio.gemini_batch._genai_client", return_value=client),
            patch("office.audio.gemini_batch.build_generate_content_config", return_value={}),
            patch("office.audio.gemini_batch.encode_pcm_to_mp3") as encode,
        ):
            summary = gemini_batch.run_batch_synthesis([chunk])

        self.assertEqual(summary, {"requested": 1, "written": 0, "failed": 1})
        encode.assert_not_called()

    def test_gemini_submit_chunks_returns_persistable_records(self):
        from office.audio import gemini_batch
        from office.audio.gemini import BatchChunk

        chunk = BatchChunk(
            cache_key="k1", prompt="p", file_path="/tmp/k1.mp3", spoken_chars=10, roles=["reader"], voices={}
        )
        job = MagicMock()
        job.name = "batches/xyz"
        client = MagicMock()
        client.batches.create.return_value = job

        with (
            patch("office.audio.gemini_batch._genai_client", return_value=client),
            patch("office.audio.gemini_batch.build_generate_content_config", return_value={}),
        ):
            records = gemini_batch.submit_chunks([chunk])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["job_name"], "batches/xyz")
        self.assertEqual(records[0]["chunks"], [{"cache_key": "k1", "file_path": "/tmp/k1.mp3", "spoken_chars": 10}])

    def test_gemini_fetch_job_reports_pending_without_writing(self):
        from office.audio import gemini_batch

        running = MagicMock()
        running.state.name = "JOB_STATE_RUNNING"
        client = MagicMock()
        client.batches.get.return_value = running

        with (
            patch("office.audio.gemini_batch._genai_client", return_value=client),
            patch("office.audio.gemini_batch.encode_pcm_to_mp3") as encode,
        ):
            result = gemini_batch.fetch_job(
                "batches/p", [{"cache_key": "k", "file_path": "/tmp/k.mp3", "spoken_chars": 10}]
            )

        self.assertFalse(result["terminal"])
        self.assertFalse(result["succeeded"])
        encode.assert_not_called()

    def test_gemini_fetch_job_writes_when_succeeded(self):
        from office.audio import gemini_batch
        from office.audio.gemini import PCM_SAMPLE_RATE

        plausible_pcm = b"\x00" * (2 * 2 * PCM_SAMPLE_RATE)
        part = MagicMock()
        part.inline_data.data = plausible_pcm
        response = MagicMock()
        response.candidates = [MagicMock(content=MagicMock(parts=[part]), finish_reason="STOP")]
        item = MagicMock(response=response, error=None)
        job = MagicMock()
        job.state.name = "JOB_STATE_SUCCEEDED"
        job.dest.inlined_responses = [item]
        job.dest.file_name = None
        client = MagicMock()
        client.batches.get.return_value = job

        with (
            patch("office.audio.gemini_batch._genai_client", return_value=client),
            patch("office.audio.gemini_batch.encode_pcm_to_mp3") as encode,
        ):
            result = gemini_batch.fetch_job(
                "batches/d", [{"cache_key": "k", "file_path": "/tmp/k.mp3", "spoken_chars": 20}]
            )

        self.assertTrue(result["terminal"])
        self.assertTrue(result["succeeded"])
        self.assertEqual(result["written"], 1)
        encode.assert_called_once()


class AudioV2HelpersTests(TestCase):
    def test_voice_mapping(self):
        self.assertEqual(voice_for_line_type("leader_dialogue"), ROLE_VOICES["leader"])
        self.assertEqual(voice_for_line_type("congregation"), ROLE_VOICES["congregation"])
        self.assertEqual(voice_for_line_type("reader"), ROLE_VOICES["reader"])
        self.assertEqual(voice_for_line_type("html"), ROLE_VOICES["reader"])

    def test_gap_policy(self):
        self.assertEqual(_gap_ms("leader", "congregation", False), 280)
        self.assertEqual(_gap_ms("leader", "leader", False), 0)
        self.assertEqual(_gap_ms("leader", "reader", True), 600)

    def test_chunk_char_limit_is_provider_scoped(self):
        from office.audio.v2 import MAX_SPOKEN_CHUNK_CHARS, _max_chunk_chars, audio_provider

        # Default outside any provider context.
        self.assertEqual(_max_chunk_chars(), MAX_SPOKEN_CHUNK_CHARS)
        with audio_provider(subdir="audio_gemini", chunk_char_limit=700):
            self.assertEqual(_max_chunk_chars(), 700)
        # Restored after the provider context exits.
        self.assertEqual(_max_chunk_chars(), MAX_SPOKEN_CHUNK_CHARS)

    def test_build_v2_batches_same_role_lines(self):
        modules = [
            {
                "name": "M",
                "lines": [
                    {"id": "a", "line_type": "leader", "content": "O Lord, open our lips."},
                    {"id": "b", "line_type": "leader", "content": "And our mouth shall proclaim your praise."},
                    {"id": "c", "line_type": "congregation", "content": "Amen."},
                ],
            }
        ]

        def side_effect(role, items):
            # Copy items — builder clears the buffer after the call.
            captured = list(items)
            return MagicMock(
                line_id=captured[0]["line_id"],
                module_name="M",
                role=role,
                kind="spoken",
                url="https://example.com/x.mp3",
                media_path="/uploads/audio_v2/clips/x.mp3",
                duration=1.0,
                line_segments=[{"id": i["line_id"], "chars": len(i["text"])} for i in captured],
            )

        with (
            patch("office.audio.v2.generate_spoken_chunk", side_effect=side_effect) as chunk_mock,
            patch(
                "office.audio.v2.assemble_full_track",
                return_value=(
                    "https://example.com/api/v1/audio_track/audio_v2/full/x.mp3",
                    "/uploads/audio_v2/full/x.mp3",
                    [{"name": "M", "start_time": 0}],
                    [{"id": "a", "start_time": 0, "duration": 1.0}],
                ),
            ),
        ):
            result = build_v2_audio(modules)
            self.assertTrue(result["available"])
            self.assertEqual(chunk_mock.call_count, 2)
            # Chunks run in a thread pool, so index by role rather than call order.
            calls_by_role = {call.args[0]: call.args[1] for call in chunk_mock.call_args_list}
            self.assertEqual(set(calls_by_role), {"leader", "congregation"})
            self.assertEqual(len(calls_by_role["leader"]), 2)
            self.assertEqual(len(calls_by_role["congregation"]), 1)
            # Even with parallel synthesis, tracks stay in document order.
            self.assertEqual([t["line_id"] for t in result["tracks"]], ["a", "b", "c"])

    def test_clip_generation_lock_serializes_same_key(self):
        import threading
        import time

        from office.audio.v2 import clip_generation_lock

        events = []

        def worker(name):
            with clip_generation_lock("same-key"):
                events.append(f"{name}-start")
                time.sleep(0.02)
                events.append(f"{name}-end")

        threads = [threading.Thread(target=worker, args=(str(i),)) for i in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Each start must be immediately followed by the same worker's end —
        # no interleaving means the per-key lock serialized generation.
        self.assertEqual(len(events), 6)
        for i in range(0, 6, 2):
            self.assertEqual(events[i].split("-")[0], events[i + 1].split("-")[0])

    def test_assemble_uses_audio_v2_directory(self):
        media_root = tempfile.mkdtemp()
        with override_settings(
            MEDIA_ROOT=media_root,
            MEDIA_URL="/uploads/",
            SITE_ADDRESS="https://127.0.0.1:8000",
        ):
            clip = MagicMock(
                file_path="/tmp/a.mp3",
                module_name="Opening",
                role="leader",
                kind="spoken",
                line_id="line-1",
                duration=1.5,
                text="O Lord, open our lips.",
                line_segments=[],
            )

            def fake_run(command):
                import os

                output = command[-1]
                os.makedirs(os.path.dirname(output), exist_ok=True)
                with open(output, "wb") as handle:
                    handle.write(b"ID3fake")

            with (
                patch("office.audio.v2._run_ffmpeg", side_effect=fake_run),
                patch(
                    "office.audio.v2._normalize_to_wav",
                    side_effect=lambda i, o, k: open(o, "wb").write(b"x"),
                ),
                patch("office.audio.v2.os.path.isfile", return_value=False),
            ):
                url, media_path, modules, lines = assemble_full_track([clip])

            self.assertTrue(url.startswith("https://127.0.0.1:8000/api/v1/audio_track/audio_v2/full/"))
            self.assertTrue(media_path.startswith("/uploads/audio_v2/full/"))
            self.assertEqual(modules[0]["name"], "Opening")
            self.assertEqual(lines[0]["id"], "line-1")
            self.assertIn("duration", lines[0])

    def test_assemble_timeline_uses_normalized_clip_duration(self):
        media_root = tempfile.mkdtemp()
        with override_settings(
            MEDIA_ROOT=media_root,
            MEDIA_URL="/uploads/",
            SITE_ADDRESS="https://127.0.0.1:8000",
        ):
            clips = [
                MagicMock(
                    file_path="/tmp/a.mp3",
                    module_name="Opening",
                    role="leader",
                    end_role="leader",
                    kind="spoken",
                    line_id="line-1",
                    duration=8.0,
                    text="First.",
                    line_segments=[{"id": "line-1", "chars": 6}],
                ),
                MagicMock(
                    file_path="/tmp/b.mp3",
                    module_name="Reading",
                    role="reader",
                    end_role="reader",
                    kind="spoken",
                    line_id="line-2",
                    duration=9.0,
                    text="Second.",
                    line_segments=[{"id": "line-2", "chars": 7}],
                ),
            ]

            def fake_run(command):
                output = command[-1]
                os.makedirs(os.path.dirname(output), exist_ok=True)
                with open(output, "wb") as handle:
                    handle.write(b"ID3fake")

            with (
                patch("office.audio.v2._run_ffmpeg", side_effect=fake_run),
                patch(
                    "office.audio.v2._normalize_to_wav",
                    side_effect=lambda i, o, k: open(o, "wb").write(b"x"),
                ),
                patch("office.audio.v2.audio_duration", return_value=2.0),
            ):
                _, _, modules, _ = assemble_full_track(clips)

            # The second module starts after the normalized 2s clip plus 600ms
            # module gap, not after the original 8s source duration.
            self.assertAlmostEqual(modules[1]["start_time"], 2.6)

    def test_build_v2_includes_silence_rubrics(self):
        with (
            patch("office.audio.v2.generate_spoken_chunk") as spoken,
            patch("office.audio.v2.assemble_full_track") as assemble,
            patch("office.audio.v2.generate_silence_clip") as silence,
        ):
            spoken.return_value = MagicMock(
                line_id="a",
                module_name="M",
                role="leader",
                kind="spoken",
                url="https://example.com/a.mp3",
                media_path="/uploads/audio_v2/clips/a.mp3",
                duration=1.0,
                line_segments=[{"id": "a", "chars": 10}],
            )
            silence.return_value = MagicMock(
                line_id="silence",
                module_name="M",
                role="silence",
                kind="silence",
                url="https://example.com/s.mp3",
                media_path="/uploads/audio_v2/silence/s.mp3",
                duration=4.0,
            )
            assemble.return_value = (
                "https://example.com/api/v1/audio_track/audio_v2/full/x.mp3",
                "/uploads/audio_v2/full/x.mp3",
                [{"name": "M", "start_time": 0}],
                [{"id": "a", "start_time": 0, "duration": 1.0}],
            )
            modules = [
                {
                    "name": "M",
                    "lines": [
                        {"id": "a", "line_type": "leader", "content": "O Lord, open our lips."},
                        {"id": "b", "line_type": "rubric", "content": "A period of silence may follow."},
                    ],
                }
            ]
            result = build_v2_audio(modules)
            self.assertTrue(result["available"])
            self.assertTrue(result["single_track"])
            self.assertEqual(spoken.call_count, 1)
            silence.assert_called_once()

    def test_build_v2_fails_when_tts_fails_instead_of_silence_only(self):
        with (
            patch("office.audio.v2.generate_spoken_chunk", side_effect=RuntimeError("bad api key")),
            patch("office.audio.v2.assemble_full_track") as assemble,
            patch("office.audio.v2.generate_silence_clip") as silence,
        ):
            silence.return_value = MagicMock(
                line_id="silence",
                module_name="M",
                role="silence",
                kind="silence",
                duration=4.0,
            )
            modules = [
                {
                    "name": "M",
                    "lines": [
                        {"id": "a", "line_type": "leader", "content": "O Lord, open our lips."},
                        {"id": "b", "line_type": "rubric", "content": "A period of silence may follow."},
                    ],
                }
            ]
            result = build_v2_audio(modules)
            self.assertFalse(result["available"])
            self.assertEqual(result["unavailable_reason"], "generation_failed")
            self.assertEqual(result["single_track"], [])
            assemble.assert_not_called()


class AudioTrackRangeTests(TestCase):
    def test_range_request_returns_partial_content(self):
        from django.test import RequestFactory

        from churchcal.api.views import AudioTrackView

        media_root = tempfile.mkdtemp()
        full_dir = os.path.join(media_root, "audio_gemini", "full")
        os.makedirs(full_dir)
        track_name = "audio_gemini/full/seek-test.mp3"
        file_path = os.path.join(media_root, track_name)
        payload = b"0123456789ABCDEFGHIJ"  # 20 bytes
        with open(file_path, "wb") as handle:
            handle.write(payload)

        with override_settings(MEDIA_ROOT=media_root):
            request = RequestFactory().get(
                f"/api/v1/audio_track/{track_name}",
                HTTP_RANGE="bytes=4-8",
            )
            response = AudioTrackView.as_view()(request, track=track_name)
            body = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Range"], "bytes 4-8/20")
        self.assertEqual(response["Content-Length"], "5")
        self.assertEqual(body, b"45678")

    def test_full_request_advertises_accept_ranges(self):
        from django.test import RequestFactory

        from churchcal.api.views import AudioTrackView

        media_root = tempfile.mkdtemp()
        track_name = "audio_gemini/full/full-test.mp3"
        file_path = os.path.join(media_root, track_name)
        os.makedirs(os.path.dirname(file_path))
        with open(file_path, "wb") as handle:
            handle.write(b"hello-audio")

        with override_settings(MEDIA_ROOT=media_root):
            request = RequestFactory().get(f"/api/v1/audio_track/{track_name}")
            response = AudioTrackView.as_view()(request, track=track_name)
            body = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Length"], "11")
        self.assertEqual(body, b"hello-audio")

"""The batch bootstrap is tested without Google requests or production media."""

import base64
import io
import json
import shutil
import tempfile
import wave
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from office import audio_batch as batch
from office.api.views import index
from office.api.views.tts import GeminiTTSProvider
from office.models import AudioClip


def audio_result():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\0\0" * 2400)
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(stream.getvalue()).decode()}}
                    ]
                },
            }
        ]
    }


class BatchSetup:
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / "manifest.json"
        self.active = GeminiTTSProvider()
        self.enterContext(
            override_settings(
                MEDIA_ROOT=self.directory, GEMINI_TTS_MODEL="gemini-3.8-flash-tts", GEMINI_TTS_VOICE_LEADER="Kore"
            )
        )
        self.enterContext(patch.object(index, "TTS_PROVIDER", self.active))
        self.key = str(batch.SERIALIZER.tts_clip_key("Kore", "Amen."))
        self.clip = {"voice": "Kore", "text": "Amen.", "kind": "line", "line_type": "leader"}
        self.manifest = {
            "version": 1,
            "signature": self.active.cache_signature(),
            "model": self.active.model,
            "style": self.active.effective_instructions,
            "start_date": "2026-10-03",
            "days": 7,
            "clips": {self.key: self.clip},
            "chunks": [{"keys": [self.key], "state": "prepared"}],
        }


class BatchPlanningTests(BatchSetup, SimpleTestCase):
    def test_seven_days_all_offices_styles_and_baseline(self):
        items = list(batch.office_requests(date(2026, 10, 3), 7))
        self.assertEqual(len(items), 7 * 8 * 2 * 12)
        self.assertEqual({url[-10:] for url, _ in items}, {f"2026-10-{day:02}" for day in range(3, 10)})
        self.assertEqual({params["language_style"] for _, params in items}, {"traditional", "contemporary"})
        self.assertEqual(items[0][1]["psalter"], "60")
        self.assertEqual(items[1][1]["psalter"], "30")

    @patch.object(batch.SERIALIZER, "find_reusable_reader", return_value=None)
    def test_prepare_collects_deduplicates_skips_cache_and_resets_context(self, reuse):
        target = batch.clip_path(self.key)
        target.parent.mkdir()
        target.write_bytes(b"existing-audio")

        def view(request):
            self.assertTrue(request._audio_prewarm)
            for _ in range(2):
                batch.SERIALIZER.get_or_create_clip("Optional text.", "leader", no_generate=True)
                batch.SERIALIZER.get_or_create_clip("Amen.", "leader")
                batch.SERIALIZER.get_or_create_clip("Hear us.", "leader")
            return SimpleNamespace(status_code=200)

        with (
            patch.object(batch, "office_requests", return_value=[("/office", {})]),
            patch.object(batch, "resolve", return_value=SimpleNamespace(func=view, args=(), kwargs={})),
            patch.object(self.active, "synthesize") as synthesis,
            patch("office.gemini_alignment.align_clip") as align,
        ):
            manifest = batch.prepare(date(2026, 10, 3))
        self.assertEqual([clip["text"] for clip in manifest["clips"].values()], ["Hear us."])
        synthesis.assert_not_called()
        align.assert_not_called()
        self.assertIsNone(index.AUDIO_CLIP_COLLECTOR.get())

    def test_prepare_resets_context_on_error(self):
        with patch.object(batch, "office_requests", side_effect=ValueError("broken")):
            with self.assertRaisesMessage(ValueError, "broken"):
                batch.prepare(date(2026, 10, 3))
        self.assertIsNone(index.AUDIO_CLIP_COLLECTOR.get())

    def test_serializer_collects_groups_readings_and_announcement_without_assembly(self):
        obj = SimpleNamespace(settings={})
        serializer = batch.SERIALIZER()
        modules = [
            {
                "name": "Prayers",
                "lines": [
                    {"id": "line_1", "line_type": "leader", "content": "Lord,"},
                    {"id": "line_2", "line_type": "leader", "content": "hear us."},
                    {"id": "line_3", "line_type": "congregation", "content": "Amen."},
                    {"id": "line_4", "line_type": "html", "content": "<p>In the beginning.</p>"},
                ],
            }
        ]
        collector = Mock(
            return_value=("https://example.com/uploads/gemini/12345678.mp3", "/uploads/gemini/12345678.mp3")
        )
        token = index.AUDIO_CLIP_COLLECTOR.set(collector)
        try:
            with (
                patch.object(serializer, "get_modules", return_value=modules),
                patch.object(serializer, "get_single_track") as assembly,
                patch("office.audio_ceremony.announcement", return_value="Morning Prayer today."),
                patch.object(index, "frame_tracks") as frame,
            ):
                result = serializer.get_audio(obj)
        finally:
            index.AUDIO_CLIP_COLLECTOR.reset(token)
        self.assertIn(("Lord, hear us.", "leader", "group"), [call.args for call in collector.call_args_list])
        self.assertIn(("In the beginning.", "reader", "reader"), [call.args for call in collector.call_args_list])
        self.assertIn(("Morning Prayer today.", "speaker", "line"), [call.args for call in collector.call_args_list])
        self.assertIsNone(result["single_track"])
        assembly.assert_not_called()
        frame.assert_not_called()

    def test_wrong_provider_rejected(self):
        with patch.object(index, "TTS_PROVIDER", Mock()):
            with self.assertRaisesMessage(ValueError, "requires"):
                batch.prepare(date(2026, 10, 3))


class BatchLifecycleTests(BatchSetup, SimpleTestCase):
    def test_submit_schema_and_resume_without_duplicate_paid_job(self):
        client = Mock()
        client.create.return_value = {"name": "batches/job-1"}
        batch.submit(self.path, self.manifest, client)
        batch.submit(self.path, batch.load_manifest(self.path), client)
        client.create.assert_called_once()
        model, payload = client.create.call_args.args
        request = payload["batch"]["inputConfig"]["requests"]["requests"][0]
        self.assertEqual(model, self.active.model)
        self.assertEqual(request["metadata"], {"key": self.key})
        self.assertEqual(request["request"]["contents"][0]["parts"][0]["text"], "Amen.")
        self.assertEqual(
            request["request"]["contents"][0]["parts"][0]["speechMetadata"]["style"],
            self.active.effective_instructions,
        )
        self.assertEqual(request["request"]["generationConfig"]["responseFormat"]["audio"]["mimeType"], "AUDIO_WAV")

    def test_uncertain_submit_is_not_automatically_retried(self):
        client = Mock()
        client.create.side_effect = requests.Timeout()
        with self.assertRaises(requests.Timeout):
            batch.submit(self.path, self.manifest, client)
        saved = batch.load_manifest(self.path)
        self.assertEqual(saved["chunks"][0]["state"], "submitting")
        with self.assertRaisesMessage(ValueError, "uncertain submission"):
            batch.submit(self.path, saved, client)
        client.create.assert_called_once()
        client.get.return_value = {"metadata": {"displayName": "dailyoffice-2026-10-03-manifest-0"}}
        batch.attach(self.path, saved, client, 0, "batches/recovered")
        self.assertEqual(batch.load_manifest(self.path)["chunks"][0]["job"], "batches/recovered")

    def test_quota_rejection_can_resume_without_losing_accepted_jobs(self):
        self.manifest["chunks"].insert(0, {"keys": [], "job": "batches/accepted", "state": "submitted"})
        client = Mock()
        client.create.side_effect = batch.BatchHTTPError(429)
        with self.assertRaisesMessage(batch.BatchHTTPError, "429"):
            batch.submit(self.path, self.manifest, client)
        saved = batch.load_manifest(self.path)
        self.assertEqual(saved["chunks"][1]["state"], "prepared")
        client.create.side_effect = None
        client.create.return_value = {"name": "batches/new"}
        batch.submit(self.path, saved, client)
        self.assertEqual(saved["chunks"][0]["job"], "batches/accepted")
        self.assertEqual(saved["chunks"][1]["job"], "batches/new")

    @override_settings(GEMINI_API_KEY="")
    def test_missing_credentials_leave_manifest_prepared(self):
        batch.save_manifest(self.path, self.manifest)
        with self.assertRaisesMessage(ValueError, "GEMINI_API_KEY"):
            batch.submit(self.path, self.manifest, batch.BatchClient())
        self.assertEqual(batch.load_manifest(self.path)["chunks"][0]["state"], "prepared")

    def test_manifest_refuses_configuration_drift_and_path_tampering(self):
        batch.save_manifest(self.path, self.manifest)
        with override_settings(GEMINI_TTS_STYLE="different"):
            with self.assertRaisesMessage(ValueError, "configuration changed"):
                batch.load_manifest(self.path)
        self.manifest["clips"] = {"../../outside": self.clip}
        batch.save_manifest(self.path, self.manifest)
        with self.assertRaisesMessage(ValueError, "clip key"):
            batch.load_manifest(self.path)

    def test_lock_excludes_second_process(self):
        with batch.manifest_lock(self.path):
            with self.assertRaisesMessage(ValueError, "Another process"):
                with batch.manifest_lock(self.path):
                    pass

    def operation(self, results):
        self.manifest["chunks"][0].update(job="batches/job-1", state="submitted")
        client = Mock()
        client.get.return_value = {"done": True, "metadata": {"state": "JOB_STATE_SUCCEEDED"}}
        client.results.return_value = results
        return client

    @patch.object(batch, "import_clip")
    def test_import_matches_keys_and_resumes(self, importer):
        client = self.operation([{"metadata": {"key": self.key}, "response": audio_result()}])
        self.assertEqual(batch.refresh(self.path, self.manifest, client, True), 0)
        self.assertEqual(batch.refresh(self.path, batch.load_manifest(self.path), client, True), 0)
        importer.assert_called_once()
        client.get.assert_called_once()

    @patch.object(batch, "import_clip")
    def test_partial_errors_and_missing_results_remain_retryable(self, importer):
        other_key = str(batch.SERIALIZER.tts_clip_key("Kore", "Lord."))
        self.manifest["clips"][other_key] = self.clip | {"text": "Lord."}
        self.manifest["chunks"][0]["keys"].append(other_key)
        client = self.operation([{"metadata": {"key": self.key}, "response": audio_result()}])
        self.assertEqual(batch.refresh(self.path, self.manifest, client, True), 1)
        saved = batch.load_manifest(self.path)
        self.assertFalse(saved["chunks"][0]["imported"])
        self.assertEqual(saved["chunks"][0]["failures"], {other_key: "Missing batch response."})
        importer.assert_called_once()
        client.results.return_value = [{"metadata": {"key": self.key}, "error": {"code": 8}}]
        self.assertEqual(batch.refresh(self.path, saved, client, True), 2)

    @patch.object(batch, "import_clip")
    def test_running_job_never_imports(self, importer):
        client = self.operation([])
        client.get.return_value = {"metadata": {"state": "JOB_STATE_RUNNING"}}
        self.assertEqual(batch.refresh(self.path, self.manifest, client, True), 0)
        importer.assert_not_called()
        client.results.assert_not_called()

    def test_unknown_result_is_rejected(self):
        client = self.operation([{"key": "unknown", "response": audio_result()}])
        with self.assertRaisesMessage(ValueError, "unknown"):
            batch.refresh(self.path, self.manifest, client, True)

    def test_prepare_command_defaults_and_refuses_overwrite(self):
        with patch.object(batch, "prepare", return_value=self.manifest) as prepare:
            call_command("batch_audio_files", "prepare", manifest=str(self.path), stdout=io.StringIO())
            self.assertEqual(prepare.call_args.args[1:3], (7, 50))
            with self.assertRaisesMessage(CommandError, "already exists"):
                call_command("batch_audio_files", "prepare", manifest=str(self.path), stdout=io.StringIO())

    def test_rest_results_inline_and_streamed_jsonl(self):
        item = {"metadata": {"key": self.key}, "response": audio_result()}
        client = batch.BatchClient()
        self.assertEqual(
            list(client.results({"response": {"inlinedResponses": {"inlinedResponses": [item]}}})), [item]
        )
        response = Mock()
        response.iter_lines.return_value = [json.dumps(item).encode(), b""]
        with patch.object(client, "request") as request:
            request.return_value.__enter__.return_value = response
            self.assertEqual(list(client.results({"response": {"responsesFile": "files/results"}})), [item])
            self.assertTrue(request.call_args.kwargs["stream"])
        with self.assertRaisesMessage(ValueError, "no supported"):
            list(client.results({"response": {"responsesFile": "https://elsewhere.example"}}))

    @override_settings(GEMINI_API_KEY="test-key")
    @patch.object(batch.requests, "request")
    def test_rest_auth_timeout_and_no_redirects(self, request):
        request.return_value.status_code = 429
        with self.assertRaisesMessage(ValueError, "HTTP 429"):
            batch.BatchClient().request("POST", batch.API)
        request.assert_called_once()
        self.assertEqual(request.call_args.kwargs["headers"], {"x-goog-api-key": "test-key"})
        self.assertFalse(request.call_args.kwargs["allow_redirects"])


@skipUnless(shutil.which("ffmpeg"), "ffmpeg is required")
class BatchImportTests(BatchSetup, TestCase):
    def test_real_conversion_database_tracking_and_repeat_import(self):
        batch.import_clip(self.key, self.clip, audio_result())
        clip = AudioClip.objects.get(key=self.key)
        self.assertEqual(clip.filename, f"gemini/{self.key}.mp3")
        self.assertEqual(clip.provider, "gemini")
        self.assertGreater(clip.duration, 0)
        original = batch.clip_path(self.key).read_bytes()
        with patch.object(self.active, "write_wav") as convert:
            batch.import_clip(self.key, self.clip, audio_result())
        convert.assert_not_called()
        self.assertEqual(batch.clip_path(self.key).read_bytes(), original)
        self.assertEqual(AudioClip.objects.filter(key=self.key).count(), 1)

    def test_invalid_or_truncated_audio_does_not_publish(self):
        result = audio_result()
        result["candidates"][0]["finishReason"] = "MAX_TOKENS"
        with self.assertRaisesMessage(ValueError, "incomplete"):
            batch.import_clip(self.key, self.clip, result)
        result["candidates"][0]["finishReason"] = "STOP"
        result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"] = "!!!"
        with self.assertRaisesMessage(ValueError, "base64"):
            batch.import_clip(self.key, self.clip, result)
        self.assertFalse(batch.clip_path(self.key).exists())
        self.assertFalse(AudioClip.objects.filter(key=self.key).exists())

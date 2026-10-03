import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from office.voice_auditions import AuditionStore, SAMPLE_TEXT
from office.api.views.tts import GeminiTTSProvider
from office.voice_style import GEMINI_PRAYER_STYLE


@override_settings(GEMINI_API_KEY="test-only", GEMINI_TTS_MODEL="gemini-3.8-flash-tts")
class VoiceAuditionTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.catalog = [
            {"id": "one", "display_name": "One", "language_code": "en-US", "region_code": "US", "gender": "male"},
            {"id": "two", "display_name": "Two", "language_code": "en-US", "accent": "East Coast", "gender": "female"},
            {"id": "british", "language_code": "en-GB", "region_code": "GB"},
            {"id": "unknown"},
            {"id": "french", "language_code": "fr-FR"},
        ]

    def store(self):
        (self.directory / "catalog.json").write_text(json.dumps(self.catalog))
        return AuditionStore(self.directory)

    @patch("office.voice_auditions.requests.get")
    def test_full_catalog_pagination_and_strict_american_english_filter(self, get):
        get.side_effect = [
            Mock(ok=True, json=Mock(return_value={"voices": self.catalog[:2], "next_page_token": "next"})),
            Mock(ok=True, json=Mock(return_value={"voices": self.catalog[2:]})),
        ]
        store = AuditionStore(self.directory)
        self.assertEqual(store.total, 5)
        self.assertEqual(set(store.voices), {"one", "two"})
        self.assertEqual(get.call_args.kwargs["params"]["page_token"], "next")
        self.assertNotIn("test-only", json.dumps(store.snapshot()))
        self.assertFalse(store.snapshot()["popularity_available"])
        get.reset_mock()
        AuditionStore(self.directory)
        get.assert_not_called()

    @patch("office.voice_auditions.requests.get")
    def test_repeated_page_tokens_fail_without_saving_partial_catalog(self, get):
        get.return_value = Mock(ok=True, json=Mock(return_value={"voices": self.catalog, "next_page_token": "same"}))
        with self.assertRaisesMessage(ValueError, "repeated"):
            AuditionStore(self.directory)
        self.assertFalse((self.directory / "catalog.json").exists())

    def test_audio_is_cached_by_voice_model_style_and_sample(self):
        store = self.store()

        def generate(voice, text, path):
            self.assertEqual(text, SAMPLE_TEXT)
            self.assertTrue(text.startswith("Amen. O Lord,"))
            Path(path).write_bytes(b"audio")

        with patch.object(store.provider, "synthesize", side_effect=generate) as generate_mock:
            first = store.synthesize("one")
            self.assertEqual(store.synthesize("one"), first)
            generate_mock.assert_called_once()
            with override_settings(GEMINI_TTS_MODEL="gemini-3.8-flash-lite-tts"):
                self.assertNotEqual(store.synthesize("one"), first)
            self.assertNotEqual(store.synthesize("two"), first)
        self.assertEqual(store.snapshot()["cached"], ["one", "two"])

    @override_settings(GEMINI_TTS_STYLE="")
    def test_shared_prayer_direction_and_style_cache_invalidation(self):
        store = self.store()
        self.assertEqual(store.provider.effective_instructions, GEMINI_PRAYER_STYLE)
        self.assertEqual(GeminiTTSProvider().effective_instructions, GEMINI_PRAYER_STYLE)
        original_key = store.sample_key("one")
        with patch("office.voice_auditions.STYLE", "different delivery"):
            self.assertNotEqual(store.sample_key("one"), original_key)

    def test_bulk_skips_cached_and_retries_failures(self):
        store = self.store()
        store.audio_path(store.sample_key("one")).write_bytes(b"cached")
        with patch.object(store.provider, "synthesize", side_effect=RuntimeError("private error")) as generate:
            store.start_batch()
            store.batch_thread.join(timeout=2)
            self.assertFalse(store.batch_thread.is_alive())
            self.assertEqual(generate.call_count, 1)
        self.assertEqual(store.snapshot()["batch"]["failed"], ["two"])
        self.assertNotIn("private error", json.dumps(store.snapshot()))
        with patch.object(store.provider, "synthesize", side_effect=lambda v, t, p: Path(p).write_bytes(b"audio")):
            store.start_batch()
            store.batch_thread.join(timeout=2)
        self.assertEqual(store.snapshot()["batch"]["failed"], [])
        self.assertEqual(set(store.snapshot()["cached"]), {"one", "two"})

    def test_bulk_stop_duplicate_start_and_resume_after_restart(self):
        import threading

        store = self.store()
        entered, release = threading.Event(), threading.Event()

        def generate(voice, text, path):
            entered.set()
            release.wait(timeout=3)
            Path(path).write_bytes(b"audio")

        with patch.object(store.provider, "synthesize", side_effect=generate) as synth:
            try:
                store.start_batch()
                self.assertTrue(entered.wait(timeout=2))
                thread = store.batch_thread
                store.start_batch()
                self.assertIs(store.batch_thread, thread)
                self.assertEqual(store.stop_batch()["batch"]["status"], "stopping")
            finally:
                release.set()
                store.batch_thread.join(timeout=2)
            self.assertEqual(synth.call_count, 1)
        self.assertEqual(store.snapshot()["batch"]["status"], "paused")
        restored = AuditionStore(self.directory)
        with patch.object(
            restored.provider, "synthesize", side_effect=lambda v, t, p: Path(p).write_bytes(b"audio")
        ) as synth:
            restored.start_batch()
            restored.batch_thread.join(timeout=2)
            self.assertEqual(synth.call_count, 1)
        self.assertEqual(len(restored.snapshot()["cached"]), 2)

    def test_results_survive_restart_and_validate_input(self):
        store = self.store()
        store.save_result({"voice": "one", "status": "shortlist", "rating": 5, "notes": "Clear and warm"})
        restored = AuditionStore(self.directory)
        self.assertEqual(restored.results["one"]["notes"], "Clear and warm")
        for changes in ({"rating": 7}, {"status": "oops"}, {"voice": "british"}, {"notes": "x" * 2001}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                store.save_result({"voice": "one", "status": "shortlist", "rating": 5, **changes})

    def test_unknown_voices_and_path_traversal_are_rejected(self):
        store = self.store()
        with self.assertRaises(ValueError):
            store.synthesize("british")
        with self.assertRaises(ValueError):
            store.audio_path("../website/.env")


class VoiceAuditionHTTPTests(SimpleTestCase):
    def setUp(self):
        import threading
        from http.server import ThreadingHTTPServer
        from office.management.commands.voice_auditions import make_handler

        self.store = Mock()
        self.store.snapshot.return_value = {"voices": []}
        self.store.save_result.return_value = {"saved": True}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.store, "session-token"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, headers=None, data=None):
        import http.client

        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        self.addCleanup(connection.close)
        connection.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers or {})
        response = connection.getresponse()
        return response.status, response.read()

    def test_foreign_host_and_cross_origin_posts_are_rejected(self):
        status, _ = self.request("GET", "/api/state", {"Host": "attacker.example"})
        self.assertEqual(status, 403)
        status, _ = self.request("POST", "/api/result", {"Origin": "https://attacker.example"}, {"voice": "one"})
        self.assertEqual(status, 403)
        self.store.save_result.assert_not_called()

    def test_same_origin_session_can_save_results(self):
        status, body = self.request(
            "POST",
            "/api/result",
            {"Origin": f"http://127.0.0.1:{self.server.server_port}", "X-Audition-Token": "session-token"},
            {"voice": "one"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"saved": True})
        self.store.save_result.assert_called_once_with({"voice": "one"})

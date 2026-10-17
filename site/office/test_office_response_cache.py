"""Short-lived office response cache and out-of-request audio builds."""

import datetime
import json
import os
import tempfile
import threading
from io import StringIO
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from office import audio_builds, response_cache
from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider
from office.elevenlabs_dialogue import DialogueSession

LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "office-tests"}}
TODAY = datetime.date(2026, 10, 13)
PATH = "/api/v1/office/evening_prayer/2026-10-13"


class OfficeViewTestMixin:
    def setUp(self):
        cache.clear()
        self.enterContext(patch.object(index.timezone, "localdate", return_value=TODAY))
        self.enterContext(patch.object(index, "EveningPrayer"))

    def get(self, params=None, accept=None, **attributes):
        headers = {"HTTP_ACCEPT": accept} if accept else {}
        request = APIRequestFactory().get(PATH, params or {}, **headers)
        for name, value in attributes.items():
            setattr(request, name, value)
        match = resolve(PATH)
        response = match.func(request, *match.args, **match.kwargs)
        if hasattr(response, "render"):
            response.render()
        return response


@override_settings(CACHES=LOCMEM, OFFICE_API_CACHE_SECONDS=60, REST_FRAMEWORK={"UNAUTHENTICATED_USER": None})
class OfficeResponseCacheTests(OfficeViewTestMixin, SimpleTestCase):
    def test_repeat_request_is_served_from_cache_without_rebuilding(self):
        with patch.object(index, "OfficeSerializer") as serializer:
            serializer.return_value.data = {"modules": ["first"]}
            first = self.get({"psalter": "60"})
            serializer.return_value.data = {"modules": ["changed"]}
            second = self.get({"psalter": "60"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second["X-Office-Cache"], "hit")
        self.assertEqual(second.content, first.content)
        self.assertEqual(second["Content-Type"], "application/json")
        self.assertNotIn("Cache-Control", second)
        serializer.assert_called_once()

    def test_key_is_the_full_query_string_and_clear_invalidates(self):
        with patch.object(index, "OfficeSerializer") as serializer:
            serializer.return_value.data = {"modules": []}
            self.get({"psalter": "60"})
            self.get({"psalter": "30"})
            self.assertEqual(serializer.call_count, 2)
            response_cache.clear()
            self.assertFalse(self.get({"psalter": "60"}).has_header("X-Office-Cache"))
            self.assertEqual(serializer.call_count, 3)

    def test_browsable_api_and_errors_are_not_cached(self):
        with patch.object(index, "OfficeSerializer") as serializer:
            serializer.return_value.data = {"modules": []}
            self.get(accept="text/html")
            self.get(accept="text/html")
            self.assertEqual(serializer.call_count, 2)
            serializer.side_effect = index.ReadingAudioUnavailable()
            self.assertEqual(self.get().status_code, 503)
            serializer.side_effect = None
            self.assertEqual(self.get().status_code, 200)

    @override_settings(OFFICE_API_CACHE_SECONDS=0)
    def test_zero_seconds_disables_the_cache(self):
        with patch.object(index, "OfficeSerializer") as serializer:
            serializer.return_value.data = {"modules": []}
            self.get()
            self.get()
        self.assertEqual(serializer.call_count, 2)

    def test_cache_outage_serves_uncached(self):
        with (
            patch.object(index, "OfficeSerializer") as serializer,
            patch.object(response_cache.cache, "get", side_effect=OSError("memcached down")),
            patch.object(response_cache.cache, "add", side_effect=OSError("memcached down")),
        ):
            serializer.return_value.data = {"modules": []}
            with self.assertLogs("office.response_cache", "WARNING"):
                self.assertEqual(self.get().status_code, 200)

    def test_clear_command(self):
        before = response_cache.key_for(APIRequestFactory().get(PATH), "json")
        call_command("clear_office_cache", stdout=StringIO())
        self.assertNotEqual(response_cache.key_for(APIRequestFactory().get(PATH), "json"), before)


@override_settings(CACHES=LOCMEM, OFFICE_API_CACHE_SECONDS=60)
class AdminSaveClearsCacheTests(TestCase):
    def test_admin_log_entry_clears_after_commit(self):
        request = APIRequestFactory().get(PATH)
        before = response_cache.key_for(request, "json")
        user = get_user_model().objects.create(username="editor")
        with self.captureOnCommitCallbacks(execute=True):
            LogEntry.objects.create(user=user, action_flag=ADDITION, object_repr="Collect")
        self.assertNotEqual(response_cache.key_for(request, "json"), before)


@override_settings(
    CACHES=LOCMEM,
    OFFICE_API_CACHE_SECONDS=60,
    AUDIO_BUILD_RETRY_AFTER=7,
    REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
)
class DeferredAudioViewTests(OfficeViewTestMixin, SimpleTestCase):
    audio = {"include_audio_links": "true", "psalter": "60"}

    def test_missing_audio_queues_one_build_and_answers_202(self):
        data = PropertyMock(side_effect=audio_builds.AudioNotReady())
        with (
            patch.object(index.OfficeAudioSerializer, "data", data),
            patch.object(audio_builds, "schedule") as schedule,
        ):
            response = self.get(self.audio)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response["Retry-After"], "7")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response.data["audio"]["status"], "preparing")
        self.assertEqual(response.data["audio"]["single_track"], [])
        identity, build = schedule.call_args.args
        self.assertEqual(identity, f"{PATH}?include_audio_links=true&psalter=60")
        with patch.object(index, "build_office_audio") as background:
            build()
        background.assert_called_once_with(PATH, "include_audio_links=true&psalter=60")

    def test_serializer_runs_with_generation_deferred(self):
        seen = []

        def data(serializer):
            seen.append(audio_builds.generation_deferred())
            return {"audio": {"single_track": ["ready.mp3"]}}

        with patch.object(index.OfficeAudioSerializer, "data", property(data)):
            self.assertEqual(self.get(self.audio).status_code, 200)
            # Trusted in-process callers still generate inline and skip the cache.
            self.assertEqual(self.get(self.audio, _audio_prewarm=True).status_code, 200)
            self.assertEqual(self.get(self.audio, _audio_build=True).status_code, 200)
        self.assertEqual(seen, [True, False, False])
        self.assertFalse(audio_builds.generation_deferred())

    def test_in_flight_build_answers_202_without_rebuilding_the_office(self):
        with (
            patch.object(audio_builds, "is_building", return_value=True),
            patch.object(index.OfficeAudioSerializer, "data", new_callable=PropertyMock) as data,
        ):
            response = self.get(self.audio)
        self.assertEqual(response.status_code, 202)
        data.assert_not_called()
        index.EveningPrayer.assert_not_called()

    def test_failed_build_answers_503_until_it_expires(self):
        with patch.object(audio_builds, "has_failed", return_value=True):
            response = self.get(self.audio)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["detail"].code, "audio_build_failed")

    def test_finished_build_is_served_to_the_polling_client_from_cache(self):
        with patch.object(index.OfficeAudioSerializer, "data", new_callable=PropertyMock) as data:
            data.return_value = {"audio": {"single_track": ["ready.mp3"]}}
            index.build_office_audio(PATH, "include_audio_links=true&psalter=60")
            data.side_effect = AssertionError("must not rebuild")
            response = self.get(self.audio)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Office-Cache"], "hit")

    def test_answer_without_a_track_is_not_cached(self):
        with patch.object(index.OfficeAudioSerializer, "data", new_callable=PropertyMock) as data:
            data.return_value = {"audio": {"single_track": []}}
            self.assertEqual(self.get(self.audio).status_code, 200)
            data.return_value = {"audio": {"single_track": ["ready.mp3"]}}
            response = self.get(self.audio)
            self.assertEqual(json.loads(response.content)["audio"]["single_track"], ["ready.mp3"])
            self.assertFalse(response.has_header("X-Office-Cache"))
            self.assertEqual(self.get(self.audio)["X-Office-Cache"], "hit")
        self.assertEqual(data.call_count, 2)


@override_settings(
    CACHES=LOCMEM,
    AUDIO_BUILD_WORKERS=1,
    AUDIO_BUILD_MAX_PENDING=2,
    AUDIO_BUILD_LOCK_SECONDS=60,
    AUDIO_BUILD_FAILURE_SECONDS=60,
)
class AudioBuildSchedulerTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(audio_builds._pending.clear)

    def run_now(self):
        """Run submitted builds synchronously in this thread."""
        return patch.object(audio_builds, "_get_executor", return_value=SimpleNamespace(submit=lambda fn, *a: fn(*a)))

    def test_same_identity_is_built_once_at_a_time(self):
        release = threading.Event()
        calls = []

        def build():
            calls.append(threading.current_thread().name)
            release.wait(5)
            return True

        self.assertTrue(audio_builds.schedule("office-a", build))
        self.assertTrue(audio_builds.is_building("office-a"))
        self.assertFalse(audio_builds.schedule("office-a", build))
        release.set()
        audio_builds._get_executor().submit(lambda: None).result(5)
        for _ in range(50):
            if not audio_builds.is_building("office-a"):
                break
            threading.Event().wait(0.05)
        self.assertFalse(audio_builds.is_building("office-a"))
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("office-audio-build"))
        self.assertFalse(audio_builds.has_failed("office-a"))

    def test_other_process_holding_the_lock_blocks_a_duplicate(self):
        cache.add(audio_builds._key("lock", "office-b"), 1)
        self.assertFalse(audio_builds.schedule("office-b", lambda: True))

    def test_failure_is_remembered_and_lock_released(self):
        with self.run_now(), patch.object(audio_builds, "release_db_connections") as release:
            audio_builds.schedule("office-c", lambda: False)
            with self.assertLogs("office.audio_builds", "ERROR"):
                audio_builds.schedule("office-d", lambda: 1 / 0)
        self.assertTrue(audio_builds.has_failed("office-c"))
        self.assertTrue(audio_builds.has_failed("office-d"))
        self.assertFalse(audio_builds.is_building("office-c"))
        self.assertEqual(release.call_count, 2)

    def test_queue_is_bounded(self):
        audio_builds._pending.update({"x", "y"})
        self.assertFalse(audio_builds.schedule("office-e", lambda: True))
        self.assertFalse(audio_builds.is_building("office-e"))

    def test_generation_points_raise_only_when_deferred(self):
        audio_builds.ensure_generation_allowed()
        with audio_builds.deferred_generation():
            with self.assertRaises(audio_builds.AudioNotReady):
                audio_builds.ensure_generation_allowed()
        audio_builds.ensure_generation_allowed()


@override_settings(SITE_ADDRESS="https://example.test")
class DeferredGenerationPointTests(SimpleTestCase):
    def setUp(self):
        self.media = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=self.media))

    def test_missing_clip_is_not_synthesized_or_reported(self):
        serializer = index.GenericDailyOfficeSerializer
        with (
            patch.object(index.TTS_PROVIDER, "synthesize") as synthesize,
            patch.object(serializer, "find_reusable_reader", return_value=None),
            patch.object(index.bugsnag, "notify") as notify,
            audio_builds.deferred_generation(),
        ):
            with self.assertRaises(audio_builds.AudioNotReady):
                serializer.get_or_create_clip("The Lord be with you.", "leader")
            with self.assertRaises(audio_builds.AudioNotReady):
                serializer.synthesize_speech("voice", "text", os.path.join(self.media, "x.mp3"))
            with (
                patch.object(serializer, "get_or_create_clip", side_effect=audio_builds.AudioNotReady()),
                patch.object(serializer, "reading_voice", return_value="reader"),
            ):
                with self.assertRaises(audio_builds.AudioNotReady):
                    serializer.handle_html("<p>In the beginning.</p>", voice="reader")
            with patch.object(index.subprocess, "run") as ffmpeg:
                with self.assertRaises(audio_builds.AudioNotReady):
                    serializer.get_silence_clip(0.5)
            ffmpeg.assert_not_called()
        synthesize.assert_not_called()
        notify.assert_not_called()

    def test_existing_clip_is_served_while_deferred(self):
        serializer = index.GenericDailyOfficeSerializer
        voice = index.TTS_PROVIDER.voice_for_text("leader", "Amen.")
        key = serializer.tts_clip_key(voice, serializer.normalize_tts_text("Amen."))
        filename = index.provider_media_name(f"{key}.mp3")
        with open(os.path.join(self.media, filename), "wb") as handle:
            handle.write(b"mp3")
        with (
            patch.object(index.TTS_PROVIDER, "synthesize") as synthesize,
            patch.object(serializer, "find_reusable_reader", return_value=None),
            patch.object(serializer, "record_audio_clip"),
            patch.object(serializer, "get_clip_word_timing", return_value=[]),
            audio_builds.deferred_generation(),
        ):
            url, path = serializer.get_or_create_clip("Amen.", "leader")
        self.assertEqual(path, "/uploads/" + filename)
        synthesize.assert_not_called()

    def test_clip_lock_skips_synthesis_when_another_build_finished_it(self):
        serializer = index.GenericDailyOfficeSerializer

        def finished_elsewhere(voice, text, file_path):
            raise AssertionError("must not synthesize twice")

        voice = index.TTS_PROVIDER.voice_for_text("leader", "Amen.")
        key = serializer.tts_clip_key(voice, serializer.normalize_tts_text("Amen."))
        file_path = os.path.join(self.media, index.provider_media_name(f"{key}.mp3"))
        real_isfile = os.path.isfile
        checks = []

        def isfile(path):
            # Missing on the first (unlocked) check, present once the lock is held.
            if path == file_path:
                checks.append(path)
                if len(checks) == 1:
                    return False
                with open(file_path, "wb") as handle:
                    handle.write(b"mp3")
            return real_isfile(path)

        with (
            patch.object(index.os.path, "isfile", side_effect=isfile),
            patch.object(serializer, "synthesize_speech", side_effect=finished_elsewhere),
            patch.object(serializer, "find_reusable_reader", return_value=None),
            patch.object(serializer, "record_audio_clip"),
            patch.object(serializer, "get_clip_word_timing", return_value=[]),
        ):
            url, path = serializer.get_or_create_clip("Amen.", "leader", raise_on_error=True)
        self.assertTrue(path.endswith(f"{key}.mp3"))

    @override_settings(
        ELEVENLABS_TTS_MODEL="eleven_v4",
        ELEVENLABS_API_KEY="test",
        ELEVENLABS_TTS_VOICE_LEADER="leader",
        ELEVENLABS_TTS_VOICE_CONGREGATION="people",
        ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
    )
    def test_uncached_dialogue_is_deferred_without_calling_the_api(self):
        lines = [
            {"id": "one", "line_type": "leader", "content": "Hello"},
            {"id": "two", "line_type": "congregation", "content": "Amen"},
        ]
        with (
            patch("office.elevenlabs_dialogue.requests.post") as post,
            patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            audio_builds.deferred_generation(),
        ):
            with self.assertRaises(audio_builds.AudioNotReady):
                DialogueSession(ElevenLabsTTSProvider()).clip(lines)
        post.assert_not_called()
        notify.assert_not_called()


@override_settings(CACHES=LOCMEM, SITE_ADDRESS="https://example.test")
class LineAudioEndpointTests(SimpleTestCase):
    def test_missing_clip_is_built_in_the_background(self):
        with (
            tempfile.TemporaryDirectory() as media,
            override_settings(MEDIA_ROOT=media),
            patch.object(index.GenericDailyOfficeSerializer, "find_reusable_reader", return_value=None),
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech") as synthesize,
            patch.object(audio_builds, "schedule") as schedule,
        ):
            request = APIRequestFactory().post("/audio/", {"content": "Amen.", "line_type": "leader"}, format="json")
            response = index.AudioViewSet().retrieve(request)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["path"], "")
        synthesize.assert_not_called()
        schedule.assert_called_once()

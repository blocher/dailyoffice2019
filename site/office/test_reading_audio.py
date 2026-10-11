import datetime
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider


@override_settings(SITE_ADDRESS="https://example.test", REST_FRAMEWORK={"UNAUTHENTICATED_USER": None})
class ReadingAudioCompletenessTests(SimpleTestCase):
    html = "<p>First verse.</p><p>Second verse.</p><p>Third verse.</p>"
    clip = ("https://example.test/uploads/12345678.mp3", "/uploads/12345678.mp3")

    def setUp(self):
        self.serializer = index.OfficeAudioSerializer()
        self.office = SimpleNamespace(settings={})
        self.modules = [
            {
                "name": "Opening",
                "lines": [{"id": "opening_0", "line_type": "leader", "content": "Let us pray."}],
            },
            {
                "name": "First Reading",
                "lines": [
                    {
                        "id": "firstreading_0",
                        "line_type": "html",
                        "content": self.html,
                        "audio_voice": "reader-test",
                        "silence_before": 1,
                        "silence_after": 2,
                    }
                ],
            },
        ]
        self.enterContext(
            patch.object(index.GenericDailyOfficeSerializer, "reading_voice", return_value="reader-test")
        )
        self.enterContext(patch.object(index.GenericDailyOfficeSerializer, "get_clip_word_timing", return_value=[]))

    def reading(self, **kwargs):
        return self.serializer.handle_html(self.html, voice="reader-test", **kwargs)

    def test_any_missing_paragraph_rejects_the_reading(self):
        for failed in range(3):
            for missing in ((None, None), (self.clip[0], None), (None, self.clip[1])):
                with (
                    self.subTest(failed=failed, missing=missing),
                    patch.object(
                        index.GenericDailyOfficeSerializer,
                        "get_or_create_clip",
                        side_effect=[self.clip] * failed + [missing],
                    ) as clip,
                ):
                    with self.assertRaises(index.ReadingAudioUnavailable):
                        self.reading()
                    self.assertEqual(clip.call_count, failed + 1)
                    self.assertTrue(all(call.kwargs["raise_on_error"] for call in clip.call_args_list))

    def test_complete_failure_does_not_assemble_cached_liturgy_as_a_complete_office(self):
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(self.serializer, "get_modules", return_value=self.modules),
            patch.object(
                index.GenericDailyOfficeSerializer, "get_or_create_clip", side_effect=[self.clip, (None, None)]
            ),
            patch.object(index, "frame_tracks") as frame,
            patch.object(self.serializer, "get_single_track") as assemble,
        ):
            with self.assertRaises(index.ReadingAudioUnavailable):
                self.serializer.get_audio(self.office)
            frame.assert_not_called()
            assemble.assert_not_called()

    def test_successful_office_keeps_all_paragraphs_order_and_padding(self):
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(self.serializer, "get_modules", return_value=self.modules),
            patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=self.clip),
            patch.object(index, "frame_tracks", side_effect=lambda obj, tracks, *args: tracks),
            patch.object(self.serializer, "get_single_track", return_value=["complete.mp3"]) as assemble,
        ):
            audio = self.serializer.get_audio(self.office)
        self.assertEqual(len(audio["tracks"]), 4)
        self.assertEqual([track["module"] for track in audio["tracks"]], ["Opening"] + ["First Reading"] * 3)
        self.assertEqual(audio["tracks"][1]["silence_before"], 1)
        self.assertEqual(audio["tracks"][-1]["silence_after"], 2)
        self.assertEqual(audio["single_track"], ["complete.mp3"])
        assemble.assert_called_once_with(audio["tracks"])

    def test_synthesis_error_is_reported_and_wrapped_without_vendor_details(self):
        error = RuntimeError("synthetic private vendor message")
        with (
            patch.object(index.GenericDailyOfficeSerializer, "_get_or_create_clip", side_effect=error),
            patch.object(index.bugsnag, "notify") as notify,
        ):
            with self.assertRaises(index.ReadingAudioUnavailable) as raised:
                self.reading()
        self.assertIs(raised.exception.__cause__, error)
        self.assertNotIn(str(error), str(raised.exception))
        notify.assert_called_once()

    def test_audio_endpoint_returns_503_without_partial_audio_then_succeeds_on_retry(self):
        today = datetime.date(2026, 10, 11)
        request = APIRequestFactory().get("/", {"include_audio_links": "true"})
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(index, "MorningPrayer", return_value=self.office),
            patch.object(index.timezone, "localdate", return_value=today),
            patch.object(index.GenericDailyOfficeSerializer, "get_modules", return_value=self.modules),
            patch.object(
                index.GenericDailyOfficeSerializer,
                "get_or_create_clip",
                side_effect=[self.clip, self.clip, (None, None), self.clip],
            ),
            patch.object(index, "frame_tracks", side_effect=lambda obj, tracks, *args: tracks) as frame,
            patch.object(
                index.GenericDailyOfficeSerializer, "get_single_track", return_value=["incomplete.mp3"]
            ) as assemble,
        ):
            response = index.MorningPrayerView.as_view()(request, year=2026, month=10, day=11)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["detail"].code, "reading_audio_unavailable")
        self.assertNotIn("audio", response.data)
        frame.assert_not_called()
        assemble.assert_not_called()
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(index, "MorningPrayer", return_value=self.office),
            patch.object(index.timezone, "localdate", return_value=today),
            patch.object(index.GenericDailyOfficeSerializer, "get_modules", return_value=self.modules),
            patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=self.clip),
            patch.object(index, "frame_tracks", side_effect=lambda obj, tracks, *args: tracks),
            patch.object(index.GenericDailyOfficeSerializer, "get_single_track", return_value=["complete.mp3"]),
        ):
            response = index.MorningPrayerView.as_view()(request, year=2026, month=10, day=11)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["audio"]["tracks"]), 4)

    def test_display_and_cache_planning_do_not_require_generated_audio(self):
        with patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=(None, None)) as clip:
            self.assertEqual(self.reading(html=True, no_generate=True), self.html)
            self.assertEqual(self.reading(no_generate=True), [])
        self.assertTrue(all(not call.kwargs["raise_on_error"] for call in clip.call_args_list))

    def test_empty_markup_and_embedded_player_are_not_missing_speech(self):
        with patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip") as clip:
            self.assertEqual(self.serializer.handle_html("<p> </p>"), [])
            self.assertEqual(self.serializer.handle_html('<iframe src="example"></iframe>'), [])
        clip.assert_not_called()

    @override_settings(ELEVENLABS_TTS_MODEL="eleven_multilingual_v2", ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="")
    def test_retry_preserves_cached_and_newly_synthesized_paragraphs(self):
        provider = ElevenLabsTTSProvider()
        texts = ["First verse.", "Second verse.", "Third verse."]
        # A missing first, middle, or last paragraph, with zero or all other
        # paragraphs initially cached, exercises both cache/generation orders.
        for failed in range(3):
            for cached in ((), tuple(i for i in range(3) if i != failed)):
                with (
                    self.subTest(failed=failed, cached=cached),
                    tempfile.TemporaryDirectory() as media,
                    override_settings(MEDIA_ROOT=media),
                    patch.object(index, "TTS_PROVIDER", provider),
                    patch.object(
                        index.GenericDailyOfficeSerializer, "normalize_tts_text", side_effect=lambda text: text
                    ),
                    patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip"),
                    patch.object(index.bugsnag, "notify"),
                ):
                    root = Path(media) / provider.media_subdir
                    root.mkdir()
                    paths = [root / f"{self.serializer.tts_clip_key('reader-test', text)}.mp3" for text in texts]
                    for position in cached:
                        paths[position].write_bytes(b"cached audio")

                    def synthesize(voice, text, path):
                        if text == texts[failed]:
                            raise RuntimeError("synthetic synthesis failure")
                        Path(path).write_bytes(b"new audio")
                        return []

                    with patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech", side_effect=synthesize):
                        with self.assertRaises(index.ReadingAudioUnavailable):
                            self.reading()
                    preserved = {path: path.read_bytes() for path in paths if path.exists()}
                    self.assertFalse(paths[failed].exists())
                    self.assertTrue(all(paths[position] in preserved for position in cached))

                    def recover(voice, text, path):
                        Path(path).write_bytes(b"recovered audio")
                        return []

                    with patch.object(
                        index.GenericDailyOfficeSerializer, "synthesize_speech", side_effect=recover
                    ) as retry:
                        tracks = self.reading()
                    self.assertEqual(len(tracks), 3)
                    self.assertEqual(retry.call_count, 3 - len(preserved))
                    self.assertEqual(
                        [call.args[1] for call in retry.call_args_list],
                        [text for text, path in zip(texts, paths) if path not in preserved],
                    )
                    for path, original in preserved.items():
                        self.assertEqual(path.read_bytes(), original)

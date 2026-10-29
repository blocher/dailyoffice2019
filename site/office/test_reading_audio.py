import datetime
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider


@override_settings(
    SITE_ADDRESS="https://example.test",
    REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
    ELEVENLABS_TTS_MODEL="eleven_multilingual_v2",
)
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
        # A path of its own: build-status markers are keyed by path, and another
        # test's background build of "/" may still be writing them.
        request = APIRequestFactory().get("/test-reading-audio-retry", {"include_audio_links": "true"})
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

    def deuterocanonical_office(self, day, translation):
        passage = {9: "I Maccabees 1", 10: "I Maccabees 2", 11: "II Maccabees 6"}[day]
        office = SimpleNamespace(
            settings={
                "lectionary": "daily-office-readings",
                "reading_cycle": "1",
                "reading_length": "full",
                "bible_translation": translation,
                "display_language": "english",
                "reading_headings": "off",
                "reading_audio": "on",
            },
            office_readings=SimpleNamespace(ep_reading_1=passage, ep_reading_1_testament="DC"),
            readings={
                passage: SimpleNamespace(
                    esv="-",
                    nrsvce=(
                        '<h3>Heading</h3><p><sup class="versenum">1</sup>Fallback first verse.</p>'
                        '<p><sup class="versenum">2</sup>Fallback second verse.</p>'
                    ),
                    kjv="<p>Legacy first verse.</p><p>Legacy second verse.</p>",
                )
            },
            date=SimpleNamespace(date=datetime.date(2026, 10, day)),
        )
        office.get_modules = lambda: [index.EPFirstReading(office)]
        return office

    @override_settings(ELEVENLABS_TTS_MODEL="eleven_v4")
    def test_deuterocanonical_fallback_and_kjv_body_reach_the_audio_tracks(self):
        # Synthetic text exercises the actual reading/module path without
        # copying licensed passages or depending on production appointments.
        for day in (9, 10, 11):
            for translation in ("esv", "kjv"):
                with (
                    self.subTest(day=day, translation=translation),
                    patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
                    patch(
                        "office.elevenlabs_dialogue.DialogueSession.clip", return_value=(self.clip[1], [])
                    ) as dialogue_clips,
                    patch.object(
                        index.GenericDailyOfficeSerializer, "get_or_create_clip", return_value=self.clip
                    ) as clips,
                    patch.object(index, "frame_tracks", side_effect=lambda obj, tracks, *args: tracks),
                    patch.object(
                        index.GenericDailyOfficeSerializer, "get_single_track", return_value=["complete.mp3"]
                    ),
                ):
                    audio = self.serializer.get_audio(self.deuterocanonical_office(day, translation))
                spoken = [
                    call.args[0]
                    for call in clips.call_args_list
                    if call.kwargs.get("kind") == "reader" and not call.kwargs.get("no_generate")
                ]
                prefix = "Fallback" if translation == "esv" else "Legacy"
                self.assertEqual(spoken, [f"{prefix} first verse.", f"{prefix} second verse."])
                self.assertEqual(len(audio["tracks"]), 4)  # Introduction, two paragraphs, closing.
                self.assertEqual(
                    [line["content"] for call in dialogue_clips.call_args_list for line in call.args[0]],
                    [
                        index.passage_to_citation(
                            self.deuterocanonical_office(day, translation).office_readings.ep_reading_1
                        ),
                        "Here ends the Reading.",
                    ],
                )
                self.assertEqual(audio["tracks"][-1]["text"], "Here ends the Reading.")
                self.assertEqual(audio["single_track"], ["complete.mp3"])

    def test_deuterocanonical_fallback_failure_rejects_the_audio_response(self):
        def clip(content, line_type, **kwargs):
            if kwargs.get("kind") == "reader" and not kwargs.get("no_generate"):
                if content == "Fallback second verse.":
                    return None, None
            return self.clip

        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch("office.elevenlabs_dialogue.DialogueSession.clip", return_value=(self.clip[1], [])),
            patch.object(index.GenericDailyOfficeSerializer, "get_or_create_clip", side_effect=clip),
            patch.object(index, "frame_tracks") as frame,
            patch.object(index.GenericDailyOfficeSerializer, "get_single_track") as assemble,
        ):
            with self.assertRaises(index.ReadingAudioUnavailable):
                self.serializer.get_audio(self.deuterocanonical_office(10, "esv"))
        frame.assert_not_called()
        assemble.assert_not_called()

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


class MassReadingMissingTextTests(SimpleTestCase):
    def mass_reading_lines(self, scripture):
        reading = SimpleNamespace(
            long_citation="Isa 1:1",
            short_citation="Isa 1:1",
            short_text=False,
            testament="OT",
        )
        view = SimpleNamespace(
            bible_translation="esv",
            language="en",
            office=SimpleNamespace(settings={"reading_length": "full", "reading_headings": "on"}),
            remove_headings_if_needed=lambda text: text,
            audio=lambda citation, testament: None,
            closing=lambda testament: "The Word of the Lord.",
            closing_response=lambda testament: "Thanks be to God.",
        )
        with (
            patch.object(index.Scripture.objects, "get", return_value=scripture),
            patch.object(index.GenericDailyOfficeSerializer, "reading_voice", return_value=None),
            patch.object(index, "passage_to_citation", return_value="Isaiah 1:1"),
        ):
            return index.ReadingModule.get_mass_reading_lines(view, reading)

    def test_passage_without_text_in_translation_falls_back(self):
        """A passage missing in the chosen translation shows the fallback translation."""
        lines = self.mass_reading_lines(SimpleNamespace(esv=None, nrsvce="<p>The vision of Isaiah.</p>"))
        html = [line["content"] for line in lines if line["line_type"] == "html"]
        self.assertTrue(any("The vision of Isaiah." in content for content in html))

    def test_passage_without_text_in_any_translation_renders_empty(self):
        """A Scripture row with no text in any translation must not raise."""
        lines = self.mass_reading_lines(SimpleNamespace(esv=None, nrsvce=None))
        self.assertTrue(lines)

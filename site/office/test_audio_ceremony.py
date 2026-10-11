import datetime
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from mutagen.mp3 import MP3

from office.audio_ceremony import announcement, frame_tracks, INTERCESSION_INVITATION, spoken_day
from office.api.views.index import GenericDailyOfficeSerializer


class AudioCeremonyTests(SimpleTestCase):
    def office(self, name="Morning Prayer"):
        return SimpleNamespace(
            name=name,
            date=SimpleNamespace(
                date=datetime.date(2026, 10, 3),
                all=[SimpleNamespace(name="Morning Saint"), SimpleNamespace(name="Second Saint")],
                all_evening=[SimpleNamespace(name="Evening Saint")],
                primary=SimpleNamespace(name="Morning Saint"),
                primary_evening=SimpleNamespace(name="Evening Saint"),
            ),
        )

    def test_spoken_calendar_ordinals(self):
        for day, expected in [
            (1, "first"),
            (2, "second"),
            (3, "third"),
            (12, "twelfth"),
            (21, "twenty-first"),
            (22, "twenty-second"),
            (23, "twenty-third"),
            (30, "thirtieth"),
            (31, "thirty-first"),
        ]:
            self.assertEqual(spoken_day(day), expected)
        self.assertEqual(len({spoken_day(day) for day in range(1, 32)}), 31)

    def test_all_office_names_and_evening_commemorations(self):
        for name in ["Morning Prayer", "Midday Prayer", "Family Prayer in the Morning", "Family Prayer at Midday"]:
            self.assertEqual(
                announcement(self.office(name)),
                f"{'Daily Morning Prayer' if name == 'Morning Prayer' else name} for Saturday, October third, twenty twenty-six: Morning Saint and Second Saint.",
            )
        for name in [
            "Evening Prayer",
            "Compline",
            "Family Prayer in the Early Evening",
            "Family Prayer at the Close of Day",
        ]:
            self.assertIn("twenty twenty-six: Evening Saint.", announcement(self.office(name)))

    def test_commemoration_years_survive_tts_number_expansion(self):
        for year, spoken in [
            ("1255", "twelve fifty-five"),
            ("1,255", "twelve fifty-five"),
            ("604", "six oh-four"),
            ("1900", "nineteen hundred"),
            ("1905", "nineteen oh-five"),
            ("2000", "two thousand"),
            ("2005", "two thousand and five"),
            ("2019", "twenty nineteen"),
            ("c. 1255", "c. twelve fifty-five"),
            ("1255–1300", "twelve fifty-five–thirteen hundred"),
        ]:
            for office_name in ("Morning Prayer", "Evening Prayer"):
                with self.subTest(year=year, office=office_name):
                    office = self.office(office_name)
                    original = f"Example Saint, Bishop, {year}"
                    commemoration = SimpleNamespace(name=original)
                    office.date.all = office.date.all_evening = [commemoration]
                    text = announcement(office)
                    self.assertIn(f"Example Saint, Bishop, {spoken}.", text)
                    normalized = GenericDailyOfficeSerializer.normalize_tts_text(text)
                    self.assertIn(spoken, normalized)
                    self.assertEqual(commemoration.name, original)

    def test_actual_api_office_classes_supply_announcement_names(self):
        from office.api.views import index

        offices = {
            "MorningPrayer": "Morning Prayer",
            "EveningPrayer": "Evening Prayer",
            "MiddayPrayer": "Midday Prayer",
            "Compline": "Compline",
            "FamilyMorningPrayer": "Family Prayer in the Morning",
            "FamilyMiddayPrayer": "Family Prayer at Midday",
            "FamilyEarlyEveningPrayer": "Family Prayer in the Early Evening",
            "FamilyCloseOfDayPrayer": "Family Prayer at the Close of Day",
        }
        for class_name, name in offices.items():
            with self.subTest(office=class_name):
                # Use the real runtime type; skip unrelated database initialization.
                office = object.__new__(getattr(index, class_name))
                office.date = self.office().date
                self.assertEqual(announcement(office), announcement(self.office(name)))

    def test_real_bells_silences_and_assembled_mp3(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"),
        ):
            source = Path(__file__).parent / "audio_assets/prayer_chime.mp3"
            Path(directory, "spoken.mp3").write_bytes(source.read_bytes())
            serializer = Mock()
            serializer.get_or_create_clip.return_value = ("/spoken", "/uploads/spoken.mp3")
            original = [
                {
                    "path": "/uploads/spoken.mp3",
                    "url": "/spoken",
                    "line_id": "prayer",
                    "module": "Prayer",
                    "text": INTERCESSION_INVITATION,
                    "silence_after": 0.01,
                    "word_timing": [{"id": "prayer", "word": "Let", "start_time": 0.2, "end_time": 0.5}],
                }
            ]
            tracks = frame_tracks(self.office(), original, serializer, "https://example.test")
            self.assertEqual(len(tracks), 6)
            self.assertEqual(tracks[0]["silence_before"], 0)
            self.assertEqual(tracks[1]["silence_after"], 2.5)
            self.assertEqual(tracks[3]["silence_after"], 25)
            self.assertTrue(tracks[4]["skip_gap_before"])
            self.assertEqual(original[0]["silence_after"], 0.01)
            self.assertAlmostEqual(
                MP3(Path(directory) / tracks[1]["path"].removeprefix("/uploads/")).info.length, 8, delta=0.1
            )
            import subprocess

            def silence(seconds):
                path = str(Path(directory) / f"silence-{seconds}.mp3")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "anullsrc=r=44100:cl=mono",
                        "-t",
                        str(seconds),
                        "-b:a",
                        "128k",
                        path,
                    ],
                    check=True,
                )
                return path

            with patch.object(GenericDailyOfficeSerializer, "get_silence_clip", side_effect=silence):
                result = GenericDailyOfficeSerializer.get_single_track(tracks)
            self.assertTrue(result)
            for segment in result[3]:
                self.assertGreater(segment["end_time"], segment["start_time"])
            self.assertEqual(result[4][0]["word"], "Let")
            # Word timing follows the opening announcement, bells, and explicit silence.
            expected_start = MP3(Path(directory, "spoken.mp3")).info.length + 8 + 2.5 + 0.2
            self.assertAlmostEqual(result[4][0]["start_time"], expected_start, delta=0.2)
            combined = Path(directory) / result[1].removeprefix("/uploads/")
            expected = (
                sum(MP3(Path(directory) / t["path"].removeprefix("/uploads/")).info.length for t in tracks) + 29.5
            )
            self.assertAlmostEqual(MP3(combined).info.length, expected, delta=0.5)
            serializer.get_or_create_clip.assert_called_once_with(announcement(self.office()), "speaker", kind="line")

    def test_serializer_inserts_ceremony_without_changing_display_modules(self):
        from office.api.views import index
        from office.api.views.tts import GeminiTTSProvider

        modules = [
            {
                "name": "Intercessions, Thanksgivings, and Praise",
                "lines": [
                    {"id": "invitation", "line_type": "speaker", "content": "Old invitation", "silence_after": 10}
                ],
            }
        ]
        serializer = GenericDailyOfficeSerializer()
        office = self.office()
        office.settings = {}
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", GeminiTTSProvider()),
            patch.object(serializer, "get_modules", return_value=modules),
            patch.object(serializer, "get_or_create_clip", return_value=("/clip", "/uploads/clip.mp3")) as generate,
            patch.object(serializer, "get_clip_word_timing", return_value=[]),
            patch.object(serializer, "get_single_track", return_value=[]),
        ):
            audio = serializer.get_audio(office)
        self.assertEqual(modules[0]["lines"][0]["content"], "Old invitation")
        self.assertEqual(audio["tracks"][2]["text"], INTERCESSION_INVITATION)
        self.assertEqual(audio["tracks"][3]["silence_after"], 25)
        self.assertEqual(generate.call_args_list[0].args[:2], (INTERCESSION_INVITATION, "speaker"))

    @override_settings(ELEVENLABS_TTS_MODEL="eleven_multilingual_v2")
    def test_elevenlabs_inserts_same_ceremony_without_changing_display_modules(self):
        from office.api.views import index
        from office.api.views.tts import ElevenLabsTTSProvider

        modules = [
            {
                "name": "Intercessions, Thanksgivings, and Praise",
                "lines": [
                    {"id": "invitation", "line_type": "speaker", "content": "Old invitation", "silence_after": 10}
                ],
            }
        ]
        serializer = GenericDailyOfficeSerializer()
        office = self.office()
        office.settings = {}
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(serializer, "get_modules", return_value=modules),
            patch.object(serializer, "get_or_create_clip", return_value=("/clip", "/uploads/clip.mp3")) as generate,
            patch.object(serializer, "get_clip_word_timing", return_value=[]),
            patch.object(serializer, "get_single_track", return_value=[]),
        ):
            audio = serializer.get_audio(office)
        self.assertEqual(modules[0]["lines"][0]["content"], "Old invitation")
        self.assertEqual(audio["tracks"][2]["text"], INTERCESSION_INVITATION)
        self.assertEqual(audio["tracks"][3]["silence_after"], 25)
        self.assertEqual(generate.call_args_list[0].args[:2], (INTERCESSION_INVITATION, "speaker"))

    def test_empty_audio_does_not_create_bells_only_office(self):
        serializer = Mock()
        self.assertEqual(frame_tracks(self.office(), [], serializer, ""), [])
        serializer.get_or_create_clip.assert_not_called()

    def test_missing_announcement_preserves_remaining_office(self):
        serializer = Mock()
        serializer.get_or_create_clip.return_value = (None, None)
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            tracks = frame_tracks(self.office(), [{"text": "Prayer"}], serializer, "")
        self.assertTrue(any(track.get("text") == "Prayer" for track in tracks))
        self.assertFalse(any(track.get("line_id") == "audio_office_announcement" for track in tracks))

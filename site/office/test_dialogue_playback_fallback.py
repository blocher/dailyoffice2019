import base64
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import APIException

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider
from office.elevenlabs_dialogue import DialogueSession


@override_settings(
    ELEVENLABS_TTS_MODEL="eleven_v4",
    ELEVENLABS_API_KEY="synthetic",
    ELEVENLABS_TTS_VOICE_LEADER="leader",
    ELEVENLABS_TTS_VOICE_CONGREGATION="people",
    ELEVENLABS_TTS_MAX_RETRIES=0,
    ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
)
class DialoguePlaybackFallbackTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=2",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "128k",
                    str(path),
                ],
                check=True,
                capture_output=True,
            )
            cls.audio = path.read_bytes()

    def lines(self):
        return [
            {"id": "first", "line_type": "leader", "content": "Hello"},
            {"id": "second", "line_type": "congregation", "content": "Yes"},
        ]

    def response(self, lines=None):
        provider = ElevenLabsTTSProvider()
        characters, segments = [], []
        for i, line in enumerate(lines or self.lines()):
            submitted, unused = provider.prepare_text(line["content"])
            first = len(characters)
            characters.extend(submitted)
            segments.append(
                {
                    "dialogue_input_index": i,
                    "voice_id": "leader" if i == 0 else "people",
                    "character_start_index": first,
                    "character_end_index": len(characters),
                    "start_time_seconds": i * 0.8,
                    "end_time_seconds": (i + 1) * 0.8,
                }
            )
        alignment = {
            "characters": characters,
            "character_start_times_seconds": [0.0] * len(characters),
            "character_end_times_seconds": [0.0] * len(characters),
        }
        response = Mock(status_code=200, headers={"request-id": "synthetic-request"})
        response.json.return_value = {
            "audio_base64": base64.b64encode(self.audio).decode(),
            "voice_segments": segments,
            "alignment": alignment,
            "normalized_alignment": deepcopy(alignment),
        }
        return response

    def test_complete_audio_survives_and_cache_replays_without_highlights_or_generation(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
            patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            path, timing = session.clip(self.lines())
            self.assertIsNotNone(path)
            self.assertEqual(timing, [])
            self.assertFalse(session.highlighting_available)
            self.assertEqual(next(Path(directory).rglob("dialogue_*.mp3")).read_bytes(), self.audio)
            second = DialogueSession(ElevenLabsTTSProvider())
            changed_ids = [{**line, "id": "other-" + line["id"]} for line in self.lines()]
            self.assertEqual(second.clip(changed_ids), (path, []))
            self.assertFalse(second.highlighting_available)
            self.assertEqual(second.previous, [])
            self.assertEqual(post.call_count, 1)
            self.assertEqual(notify.call_args.kwargs["severity"], "warning")
            details = notify.call_args.kwargs["metadata"]["audio"]
            self.assertTrue(details["playback_only"])
            self.assertEqual(details["raw_alignment"]["reason"], "invalid_duration")
            self.assertEqual(details["normalized_alignment"]["reason"], "invalid_duration")
            report = str(details)
            for private in ("Hello", "Yes", "synthetic-request", "audio_base64", "xi-api-key"):
                self.assertNotIn(private, report)

    @override_settings(ELEVENLABS_TTS_INSTRUCTIONS="")
    def test_mapping_diagnostics_distinguish_zero_intervals_from_positive_interior(self):
        for positive in (False, True):
            with (
                self.subTest(positive_interior=positive),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                data = post.return_value.json.return_value
                if positive:
                    for alignment in (data["alignment"], data["normalized_alignment"]):
                        alignment["character_end_times_seconds"][2] = 0.1
                session = DialogueSession(ElevenLabsTTSProvider())
                self.assertIsNotNone(session.clip(self.lines())[0])
                details = notify.call_args.kwargs["metadata"]["audio"]
                for key in ("raw_alignment", "normalized_alignment"):
                    self.assertEqual(details[key]["positive_character_intervals"], int(positive))
                    self.assertGreater(details[key]["zero_character_intervals"], 0)
                self.assertFalse(session.highlighting_available)

    def test_corrupt_or_cut_audio_is_rejected_without_publishing(self):
        for audio in (b"not an MP3", self.audio[: len(self.audio) // 2]):
            with (
                self.subTest(audio_length=len(audio)),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.bugsnag.notify"),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
            ):
                post.return_value.json.return_value["audio_base64"] = base64.b64encode(audio).decode()
                self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
                self.assertFalse(list(Path(directory).rglob("dialogue_*.mp3")))
                self.assertFalse(list(Path(directory).rglob("*.dialogue.json")))

    def test_unavailable_character_times_allow_only_independently_validated_playback(self):
        for failure in ("missing_start", "missing_end", "missing_both", "empty", "short", "long", "null"):
            with (
                self.subTest(timing_metadata=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                for key in ("alignment", "normalized_alignment"):
                    alignment = post.return_value.json.return_value[key]
                    if failure in ("missing_start", "missing_both"):
                        del alignment["character_start_times_seconds"]
                    if failure in ("missing_end", "missing_both"):
                        del alignment["character_end_times_seconds"]
                    if failure == "empty":
                        alignment["character_start_times_seconds"] = []
                    elif failure == "short":
                        alignment["character_end_times_seconds"].pop()
                    elif failure == "long":
                        alignment["character_end_times_seconds"].append(0.0)
                    elif failure == "null":
                        alignment["character_end_times_seconds"] = None
                session = DialogueSession(ElevenLabsTTSProvider())
                path, timing = session.clip(self.lines())
                self.assertIsNotNone(path)
                self.assertEqual(timing, [])
                self.assertFalse(session.highlighting_available)
                self.assertEqual(next(Path(directory).rglob("dialogue_*.mp3")).read_bytes(), self.audio)
                details = notify.call_args.kwargs["metadata"]["audio"]
                for key in ("raw_alignment", "normalized_alignment"):
                    self.assertIn(
                        details[key]["reason"], ("unavailable_character_timing", "unequal_character_timing_lengths")
                    )
                self.assertEqual(session.clip(self.lines()), (path, []))
                self.assertEqual(post.call_count, 1)

    @override_settings(ELEVENLABS_TTS_INSTRUCTIONS="")
    def test_unavailable_raw_times_still_prefer_valid_normalized_timing(self):
        for failure in ("missing", "unequal"):
            with (
                self.subTest(timing_metadata=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                data = post.return_value.json.return_value
                if failure == "missing":
                    del data["alignment"]["character_start_times_seconds"]
                else:
                    data["alignment"]["character_end_times_seconds"].pop()
                normalized = data["normalized_alignment"]
                count = len(normalized["characters"])
                normalized["character_start_times_seconds"] = [i * 0.01 for i in range(count)]
                normalized["character_end_times_seconds"] = [(i + 1) * 0.01 for i in range(count)]
                session = DialogueSession(ElevenLabsTTSProvider())
                path, timing = session.clip(self.lines())
                self.assertIsNotNone(path)
                self.assertEqual([word["word"] for word in timing], ["Hello", "Yes"])
                self.assertTrue(session.highlighting_available)
                notify.assert_not_called()

    def test_unclassified_alignment_errors_do_not_enable_audio_only_fallback(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch.object(DialogueSession, "_timing", side_effect=ValueError("synthetic unexpected error")),
            patch.object(DialogueSession, "_decoded_duration") as decode,
        ):
            self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
            decode.assert_not_called()
            self.assertFalse(list(Path(directory).rglob("dialogue_*.mp3")))

    def test_missing_times_do_not_bypass_transcript_segment_or_audio_guards(self):
        for failure in (
            "transcript",
            "characters",
            "voice",
            "missing_turn",
            "missing_time",
            "bounds",
            "order",
            "late_end",
            "corrupt",
            "cut",
        ):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify"),
            ):
                data = post.return_value.json.return_value
                for key in ("alignment", "normalized_alignment"):
                    del data[key]["character_start_times_seconds"]
                    del data[key]["character_end_times_seconds"]
                if failure == "transcript":
                    data["alignment"]["characters"][0] = "?"
                elif failure == "characters":
                    del data["alignment"]["characters"]
                    del data["normalized_alignment"]["characters"]
                elif failure == "voice":
                    data["voice_segments"][0]["voice_id"] = "wrong"
                elif failure == "missing_turn":
                    data["voice_segments"].pop()
                elif failure == "missing_time":
                    del data["voice_segments"][0]["end_time_seconds"]
                elif failure == "bounds":
                    data["voice_segments"][0]["character_start_index"] = -1
                elif failure == "order":
                    data["voice_segments"].reverse()
                elif failure == "late_end":
                    data["voice_segments"][-1]["end_time_seconds"] = 5
                elif failure == "corrupt":
                    data["audio_base64"] = base64.b64encode(b"not an MP3").decode()
                elif failure == "cut":
                    data["audio_base64"] = base64.b64encode(self.audio[: len(self.audio) // 2]).decode()
                self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
                self.assertFalse(list(Path(directory).rglob("dialogue_*.mp3")))
                self.assertFalse(list(Path(directory).rglob("*.dialogue.json")))

    def test_mismatched_or_incomplete_segment_metadata_cannot_enable_fallback(self):
        for failure in ("voice", "order", "missing", "bounds", "transcript", "missing_time", "late_end"):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.bugsnag.notify"),
                patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
            ):
                data = post.return_value.json.return_value
                if failure == "voice":
                    data["voice_segments"][0]["voice_id"] = "wrong"
                elif failure == "order":
                    data["voice_segments"].reverse()
                elif failure == "missing":
                    data["voice_segments"].pop()
                elif failure == "bounds":
                    data["voice_segments"][0]["character_start_index"] = -1
                elif failure == "transcript":
                    data["alignment"]["characters"][0] = "?"
                elif failure == "missing_time":
                    del data["voice_segments"][0]["end_time_seconds"]
                elif failure == "late_end":
                    data["voice_segments"][-1]["end_time_seconds"] = 5
                self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
                self.assertFalse(list(Path(directory).rglob("dialogue_*.mp3")))

    def test_changed_cached_audio_is_not_served(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            self.assertIsNotNone(session.clip(self.lines())[0])
            next(Path(directory).rglob("dialogue_*.mp3")).write_bytes(b"synthetic damaged cache")
            self.assertEqual(session.clip(self.lines()), (None, []))
            self.assertEqual(post.call_count, 1)

    def test_failed_dialogue_aborts_complete_office_instead_of_omitting_chunk(self):
        serializer = index.GenericDailyOfficeSerializer()
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(serializer, "get_modules", return_value=[{"name": "Synthetic", "lines": self.lines()}]),
            patch.object(serializer, "normalize_tts_text", side_effect=lambda text: text),
            patch("office.elevenlabs_dialogue.DialogueSession.clip", return_value=(None, [])),
            patch.object(serializer, "get_single_track") as assembly,
        ):
            with self.assertRaises(APIException) as raised:
                serializer.get_audio(Mock(settings={}))
            self.assertEqual(raised.exception.status_code, 503)
            self.assertEqual(raised.exception.get_codes(), "office_audio_unavailable")
            assembly.assert_not_called()

    def test_playback_only_chunk_remains_in_office_and_marks_assembly(self):
        serializer = index.GenericDailyOfficeSerializer()
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(serializer, "get_modules", return_value=[{"name": "Synthetic", "lines": self.lines()}]),
            patch.object(serializer, "normalize_tts_text", side_effect=lambda text: text),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch.object(index, "frame_tracks", side_effect=lambda office, tracks, *args: tracks),
            patch.object(serializer, "get_single_track", wraps=serializer.get_single_track) as assembly,
        ):
            result = serializer.get_audio(Mock(settings={}))
            self.assertEqual(len(result["tracks"]), 1)
            self.assertEqual(result["tracks"][0]["member_ids"], ["first", "second"])
            self.assertFalse(result["tracks"][0]["highlighting_available"])
            self.assertEqual(result["tracks"][0]["word_timing"], [])
            self.assertEqual(assembly.call_args.args[0], result["tracks"])
            single = result["single_track"]
            self.assertEqual(len(single), 5)
            self.assertEqual([segment["id"] for segment in single[3]], ["first", "second"])
            self.assertTrue(all(segment["highlighting_available"] is False for segment in single[3]))
            self.assertTrue(all(segment["end_time"] > segment["start_time"] for segment in single[3]))
            self.assertEqual(single[4], [])

    def test_missing_cache_metadata_does_not_spend_again_or_discard_audio(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            self.assertIsNotNone(session.clip(self.lines())[0])
            audio = next(Path(directory).rglob("dialogue_*.mp3"))
            sidecar = next(Path(directory).rglob("*.dialogue.json"))
            sidecar.rename(sidecar.with_suffix(".unavailable"))
            self.assertEqual(session.clip(self.lines()), (None, []))
            self.assertEqual(audio.read_bytes(), self.audio)
            self.assertEqual(post.call_count, 1)

    def test_decoder_unavailable_rejects_fallback(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()),
            patch("office.elevenlabs_dialogue.subprocess.run", side_effect=FileNotFoundError),
        ):
            self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
            self.assertFalse(list(Path(directory).rglob("dialogue_*.mp3")))

    def test_valid_following_chunk_keeps_timing_and_resets_highlight_state(self):
        following = [{**line, "content": "Other" if i == 0 else "Fine"} for i, line in enumerate(self.lines())]
        valid = self.response(following)
        data = valid.json.return_value
        count = len(data["alignment"]["characters"])
        data["alignment"]["character_start_times_seconds"] = [i * 0.01 for i in range(count)]
        data["alignment"]["character_end_times_seconds"] = [(i + 1) * 0.01 for i in range(count)]
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch("office.elevenlabs_dialogue.requests.post", side_effect=[self.response(), valid]),
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            self.assertIsNotNone(session.clip(self.lines())[0])
            self.assertFalse(session.highlighting_available)
            path, timing = session.clip(following)
            self.assertIsNotNone(path)
            self.assertTrue(timing)
            self.assertTrue(session.highlighting_available)
            self.assertEqual(session.clip(following), (path, timing))
            self.assertTrue(session.highlighting_available)

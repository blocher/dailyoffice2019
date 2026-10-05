import base64
import tempfile
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from office.api.views.tts import ElevenLabsTTSProvider
from office.elevenlabs_dialogue import DialogueSession


@override_settings(
    ELEVENLABS_TTS_MODEL="eleven_v4",
    ELEVENLABS_API_KEY="test",
    ELEVENLABS_TTS_VOICE_LEADER="leader",
    ELEVENLABS_TTS_VOICE_CONGREGATION="people",
    ELEVENLABS_TTS_MAX_RETRIES=0,
    ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
)
class DialogueTests(SimpleTestCase):
    def lines(self, text="Hello", identifier="one"):
        return [
            {"id": identifier, "line_type": "leader", "content": text},
            {"id": "two", "line_type": "congregation", "content": "Amen"},
        ]

    def response(self):
        response = Mock(status_code=200, headers={"request-id": "previous"})
        response.json.return_value = {
            "audio_base64": base64.b64encode(b"audio").decode(),
            "voice_segments": [
                {"dialogue_input_index": 0, "character_start_index": 0, "character_end_index": 5},
                {"dialogue_input_index": 1, "character_start_index": 5, "character_end_index": 9},
            ],
            "alignment": {
                "characters": list("HelloAmen"),
                "character_start_times_seconds": [i * 0.1 for i in range(9)],
                "character_end_times_seconds": [(i + 1) * 0.1 for i in range(9)],
            },
        }
        return response

    def test_module_cache_stitching_and_line_identity(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            first, _ = session.clip(self.lines())
            with override_settings(ELEVENLABS_TTS_VOICE_LEADER="second-leader"):
                session.clip(self.lines())
            self.assertEqual(post.call_args.kwargs["json"]["previous_request_ids"], ["previous"])
            self.assertEqual(
                [i["voice_id"] for i in post.call_args.kwargs["json"]["inputs"]], ["second-leader", "people"]
            )
            again, timing = session.clip(self.lines(identifier="different-office-line"))
            self.assertEqual(first, again)
            self.assertEqual([word["id"] for word in timing], ["different-office-line", "two"])
            self.assertEqual(post.call_count, 2)
            self.assertEqual(session.previous, [])
            self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).previous, [])

    def test_expired_context_is_not_sent_and_failures_report(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
            patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            session.previous = [("expired", 0)]
            session.clip(self.lines())
            self.assertNotIn("previous_request_ids", post.call_args.kwargs["json"])
            post.return_value.status_code = 400
            self.assertEqual(session.clip(self.lines("Failure")), (None, []))
            notify.assert_called_once()
            self.assertEqual(session.previous, [])

    def test_serializer_groups_dialogue_by_module(self):
        from office.api.views import index

        serializer = index.GenericDailyOfficeSerializer()
        modules = [
            {"name": "Preces", "lines": self.lines()},
            {"name": "Collect", "lines": self.lines("Let us pray", "three")},
        ]
        office = Mock(settings={})
        with (
            patch.object(index, "TTS_PROVIDER", ElevenLabsTTSProvider()),
            patch.object(serializer, "get_modules", return_value=modules),
            patch.object(serializer, "normalize_tts_text", side_effect=lambda text: text),
            patch("office.elevenlabs_dialogue.DialogueSession.clip", return_value=("/uploads/test.mp3", [])) as clip,
            patch.object(index, "frame_tracks", side_effect=lambda office, tracks, *args: tracks),
            patch.object(serializer, "get_single_track", return_value=[]),
        ):
            audio = serializer.get_audio(office)
        self.assertEqual(clip.call_count, 2)
        self.assertEqual([line["line_type"] for line in clip.call_args_list[0].args[0]], ["leader", "congregation"])
        self.assertEqual([track["module"] for track in audio["tracks"]], ["Preces", "Collect"])

    def test_large_modules_split_within_limit(self):
        session = DialogueSession(ElevenLabsTTSProvider())
        chunks = list(session.chunks(self.lines("word " * 1500), lambda text: text))
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(
                sum(len(session.provider.prepare_text(turn["text"])[0]) for turn in session.speaking_turns(chunk)),
                2000,
            )

    def test_out_of_order_speech_is_rejected_not_sorted_into_highlights(self):
        response = self.response()
        data = response.json.return_value
        # The provider says Amen before Hello, although the script says Hello first.
        data["alignment"]["character_start_times_seconds"] = [1 + i * 0.1 for i in range(5)] + [
            i * 0.1 for i in range(4)
        ]
        data["alignment"]["character_end_times_seconds"] = [1.1 + i * 0.1 for i in range(5)] + [
            0.1 + i * 0.1 for i in range(4)
        ]
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=response),
            patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
        ):
            self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
            notify.assert_called_once()

    def test_consecutive_printed_lines_form_one_turn_and_keep_line_ids(self):
        lines = [
            {"id": "first", "line_type": "leader", "content": "Hello"},
            {"id": "second", "line_type": "leader", "content": "Amen"},
        ]
        response = self.response()
        data = response.json.return_value
        data["voice_segments"] = [{"dialogue_input_index": 0, "character_start_index": 0, "character_end_index": 10}]
        data["alignment"] = {
            "characters": list("Hello Amen"),
            "character_start_times_seconds": [i * 0.1 for i in range(10)],
            "character_end_times_seconds": [(i + 1) * 0.1 for i in range(10)],
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=response) as post,
        ):
            session = DialogueSession(ElevenLabsTTSProvider())
            path, timing = session.clip(lines)
            self.assertIsNotNone(path)
            self.assertEqual([word["id"] for word in timing], ["first", "second"])
            self.assertEqual(len(post.call_args.kwargs["json"]["inputs"]), 1)
            again, timing = session.clip([{**lines[0], "content": "Hello Amen", "id": "merged"}])
            self.assertEqual(path, again)
            self.assertEqual([word["id"] for word in timing], ["merged", "merged"])
            self.assertEqual(post.call_count, 1)

    def test_reading_voice_override_survives_chunking_and_turn_grouping(self):
        session = DialogueSession(ElevenLabsTTSProvider())
        lines = [
            {"id": str(i), "line_type": "reader", "audio_voice": "assigned-reader", "content": text}
            for i, text in enumerate(["A reading from Genesis.", "In the beginning.", "The Word of the Lord."])
        ]
        chunks = list(session.chunks(lines, lambda text: text))
        turns = session.speaking_turns(chunks[0])
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["voice"], "assigned-reader")
        self.assertEqual(turns[0]["text"], "A reading from Genesis. In the beginning. The Word of the Lord.")

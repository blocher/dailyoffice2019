import base64
import tempfile
from pathlib import Path

import requests
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

    def test_retry_after_seconds_and_http_date_before_success(self):
        for header in ("7", "Thu, 01 Jan 1970 00:16:47 GMT"):
            with (
                self.subTest(header=header),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory, ELEVENLABS_TTS_MAX_RETRIES=4),
                patch("office.elevenlabs_dialogue.time.time", return_value=1000),
                patch("office.elevenlabs_dialogue.time.sleep") as sleep,
                patch(
                    "office.elevenlabs_dialogue.requests.post",
                    side_effect=[Mock(status_code=429, headers={"Retry-After": header}), self.response()],
                ) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                session = DialogueSession(ElevenLabsTTSProvider())
                path, timing = session.clip(self.lines())
                self.assertIsNotNone(path)
                self.assertEqual(len(list(Path(directory).rglob("*.mp3"))), 1)
                self.assertEqual([word["id"] for word in timing], ["one", "two"])
                sleep.assert_called_once_with(7)
                self.assertEqual(post.call_count, 2)
                self.assertEqual(session.previous, [("previous", 1000)])
                notify.assert_not_called()

    def test_missing_invalid_or_past_retry_after_uses_backoff(self):
        for header in (None, "", "bad", "-1", "1.5", "NaN", "Infinity", "Thu, 01 Jan 1970 00:00:00 GMT", "0"):
            with (
                self.subTest(header=header),
                override_settings(ELEVENLABS_TTS_MAX_RETRIES=4),
                patch("office.elevenlabs_dialogue.time.sleep") as sleep,
                patch(
                    "office.elevenlabs_dialogue.requests.post",
                    side_effect=[Mock(status_code=429, headers={"Retry-After": header}), self.response()],
                ) as post,
            ):
                session = DialogueSession(ElevenLabsTTSProvider())
                session._request({}, "test")
                sleep.assert_called_once_with(1)
                self.assertEqual(post.call_count, 2)

    def test_retry_sleep_budget_does_not_shorten_provider_guidance(self):
        for headers, attempts, waited in ((["31"], 1, 0), (["9" * 400], 1, 0), (["20", "20"], 2, 20)):
            with (
                self.subTest(headers=headers),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory, ELEVENLABS_TTS_MAX_RETRIES=4),
                patch("office.elevenlabs_dialogue.time.sleep") as sleep,
                patch(
                    "office.elevenlabs_dialogue.requests.post",
                    side_effect=[
                        Mock(status_code=429, headers={"Retry-After": header}, text="private vendor body")
                        for header in headers
                    ],
                ) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                session = DialogueSession(ElevenLabsTTSProvider())
                session.previous = [("private-request-id", 9999999999)]
                self.assertEqual(session.clip(self.lines()), (None, []))
                self.assertEqual(post.call_count, attempts)
                self.assertEqual(session.previous, [])
                self.assertEqual(list(Path(directory).rglob("*.mp3")), [])
                self.assertEqual(list(Path(directory).rglob("*.json")), [])
                self.assertEqual(sum(call.args[0] for call in sleep.call_args_list), waited)
                details = notify.call_args.kwargs["metadata"]["audio"]
                self.assertEqual(details["http_status"], 429)
                self.assertEqual(details["attempts"], attempts)
                self.assertEqual(details["retry_stop_reason"], "sleep_budget_exceeded")
                self.assertEqual(details["retry_wait_seconds"], waited)
                report = str(notify.call_args)
                for private in ("private vendor body", "private-request-id", "Hello", "Amen", "xi-api-key"):
                    self.assertNotIn(private, report)

    def test_retry_attempt_limit_and_exhaustion_diagnostics(self):
        for configured, attempts in ((0, 1), (2, 3), (100, 5), (-1, 1)):
            with (
                self.subTest(configured=configured),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory, ELEVENLABS_TTS_MAX_RETRIES=configured),
                patch("office.elevenlabs_dialogue.time.sleep") as sleep,
                patch(
                    "office.elevenlabs_dialogue.requests.post", return_value=Mock(status_code=429, headers={})
                ) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
                self.assertEqual(post.call_count, attempts)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 4, 8][: attempts - 1])
                details = notify.call_args.kwargs["metadata"]["audio"]
                self.assertEqual(details["attempts"], attempts)
                self.assertEqual(details["retry_stop_reason"], "attempts_exhausted")

    def test_transport_and_other_http_failures_keep_retry_policy(self):
        for failure, attempts in (
            (requests.Timeout("private"), 3),
            (requests.ConnectionError("private"), 3),
            (Mock(status_code=503, headers={}), 3),
            (Mock(status_code=400, headers={}), 1),
        ):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory, ELEVENLABS_TTS_MAX_RETRIES=2),
                patch("office.elevenlabs_dialogue.time.sleep") as sleep,
                patch(
                    "office.elevenlabs_dialogue.requests.post",
                    side_effect=failure if isinstance(failure, Exception) else None,
                    return_value=failure,
                ) as post,
                patch("office.elevenlabs_dialogue.bugsnag.notify") as notify,
            ):
                self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines()), (None, []))
                self.assertEqual(post.call_count, attempts)
                self.assertEqual(sleep.call_count, attempts - 1)
                self.assertNotIn("private", str(notify.call_args))

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

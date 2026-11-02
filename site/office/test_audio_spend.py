import base64
import datetime
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from office.api.views import index
from office.api.views.tts import ElevenLabsTTSProvider
from office.audio_spend import AudioRegenerated, PossiblyChargedRetry
from office.elevenlabs_dialogue import DialogueSession
from office.models import AudioClip, TTSGeneration


def notified(notify, error_class):
    return [call for call in notify.call_args_list if isinstance(call.args[0], error_class)]


@override_settings(
    ELEVENLABS_TTS_MODEL="eleven_v4",
    ELEVENLABS_API_KEY="test",
    ELEVENLABS_TTS_VOICE_LEADER="leader",
    ELEVENLABS_TTS_VOICE_CONGREGATION="people",
    ELEVENLABS_TTS_MAX_RETRIES=0,
    ELEVENLABS_PRONUNCIATION_DICTIONARY_ID="",
)
class DialogueSpendTests(TestCase):
    lines = [
        {"id": "one", "line_type": "leader", "content": "Hello"},
        {"id": "two", "line_type": "congregation", "content": "Amen"},
    ]

    def response(self, segments=True):
        response = Mock(status_code=200, headers={"request-id": "request"})
        response.json.return_value = {
            "audio_base64": base64.b64encode(b"audio").decode(),
            "voice_segments": (
                [
                    {"dialogue_input_index": 0, "character_start_index": 0, "character_end_index": 5},
                    {"dialogue_input_index": 1, "character_start_index": 5, "character_end_index": 9},
                ]
                if segments
                else []
            ),
            "alignment": {
                "characters": list("HelloAmen"),
                "character_start_times_seconds": [i * 0.1 for i in range(9)],
                "character_end_times_seconds": [(i + 1) * 0.1 for i in range(9)],
            },
        }
        return response

    def test_each_paid_request_is_recorded_and_a_lost_clip_is_reported(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response()) as post,
            patch("office.audio_spend.bugsnag.notify") as notify,
        ):
            DialogueSession(ElevenLabsTTSProvider()).clip(self.lines)
            first = TTSGeneration.objects.get()
            submitted = sum(len(turn["text"]) for turn in post.call_args.kwargs["json"]["inputs"])
            self.assertEqual((first.kind, first.characters, first.regenerated), ("dialogue", submitted, False))
            self.assertFalse(notified(notify, AudioRegenerated))

            # A cache hit costs nothing and records nothing.
            DialogueSession(ElevenLabsTTSProvider()).clip(self.lines)
            self.assertEqual(post.call_count, 1)

            # The audio disappears but its timing sidecar survives.
            next(Path(directory, "elevenlabs").glob("dialogue_*.mp3")).unlink()
            DialogueSession(ElevenLabsTTSProvider()).clip(self.lines)
            self.assertEqual(post.call_count, 2)
            self.assertTrue(TTSGeneration.objects.filter(key=first.key, regenerated=True).exists())
            self.assertEqual(len(notified(notify, AudioRegenerated)), 1)

    def test_audio_paid_for_but_rejected_is_still_recorded(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
            patch("office.elevenlabs_dialogue.requests.post", return_value=self.response(segments=False)) as post,
            patch("office.elevenlabs_dialogue.bugsnag.notify"),
            patch("office.audio_spend.bugsnag.notify") as notify,
        ):
            self.assertEqual(DialogueSession(ElevenLabsTTSProvider()).clip(self.lines), (None, []))
            post.return_value = self.response()
            DialogueSession(ElevenLabsTTSProvider()).clip(self.lines)
            self.assertEqual(list(TTSGeneration.objects.values_list("regenerated", flat=True)), [True, False])
            self.assertIn("never kept", notified(notify, AudioRegenerated)[0].kwargs["metadata"]["audio"]["reason"])

    @override_settings(ELEVENLABS_TTS_MAX_RETRIES=1)
    def test_only_retries_that_may_have_been_billed_are_reported(self):
        for failure, reported in ((requests.Timeout(), 1), (Mock(status_code=429, headers={}), 0)):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
                override_settings(MEDIA_ROOT=directory),
                patch("office.elevenlabs_dialogue.requests.post", side_effect=[failure, self.response()]),
                patch("office.elevenlabs_dialogue.time.sleep"),
                patch("office.audio_spend.bugsnag.notify") as notify,
            ):
                DialogueSession(ElevenLabsTTSProvider()).clip(self.lines)
                self.assertEqual(len(notified(notify, PossiblyChargedRetry)), reported)


class ClipSpendTests(TestCase):
    def provider(self):
        provider = Mock(media_subdir="elevenlabs", voice_for_text=Mock(return_value="reader"))
        provider.name = "elevenlabs"
        provider.prepare_text = lambda text: (f"[calm]\n{text}", [])
        return provider

    def generate(self, directory):
        def synthesize(voice, text, file_path):
            Path(file_path).write_bytes(b"audio")
            return []

        with (
            override_settings(MEDIA_ROOT=directory, MEDIA_URL="/uploads/"),
            patch.object(index.GenericDailyOfficeSerializer, "synthesize_speech", side_effect=synthesize),
            patch.object(index.GenericDailyOfficeSerializer, "record_audio_clip"),
        ):
            return index.GenericDailyOfficeSerializer.get_or_create_clip("In the beginning.", "reader", voice="reader")

    def test_regenerating_a_clip_whose_record_survives_is_reported(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(index, "TTS_PROVIDER", self.provider()),
            patch("office.audio_spend.bugsnag.notify") as notify,
        ):
            self.generate(directory)
            generation = TTSGeneration.objects.get()
            self.assertEqual(generation.characters, len("[calm]\nIn the beginning."))
            self.assertFalse(generation.regenerated)

            AudioClip.objects.create(key=generation.key, filename=f"elevenlabs/{generation.key}.mp3")
            Path(directory, "elevenlabs", f"{generation.key}.mp3").unlink()
            self.generate(directory)
            self.assertTrue(TTSGeneration.objects.filter(regenerated=True).exists())
            reason = notified(notify, AudioRegenerated)[0].kwargs["metadata"]["audio"]["reason"]
            self.assertIn("AudioClip record survives", reason)


@override_settings(ELEVENLABS_API_KEY="test", ELEVENLABS_DAILY_CREDIT_BUDGET=0)
class CheckTTSSpendTests(TestCase):
    day = datetime.date(2026, 11, 10)

    def generation(self, day, characters, regenerated=False):
        row = TTSGeneration.objects.create(
            provider="elevenlabs", kind="dialogue", key="k", characters=characters, regenerated=regenerated
        )
        noon = timezone.make_aware(datetime.datetime.combine(day, datetime.time(12)))
        TTSGeneration.objects.filter(pk=row.pk).update(created=noon)

    def usage(self, credits_by_day):
        """One hourly bucket at noon local time for each day."""
        times, values = [], []
        for day, credits in credits_by_day.items():
            noon = timezone.make_aware(datetime.datetime.combine(day, datetime.time(12)))
            times.append(int(noon.timestamp() * 1000))
            values.append(credits)
        response = Mock()
        response.json.return_value = {"time": times, "usage": {"All": values}}
        return response

    def run_check(self, credits_by_day, ledger_from):
        for offset in range((self.day - ledger_from).days + 1):
            self.generation(ledger_from + datetime.timedelta(days=offset), 1000)
        with (
            patch("office.management.commands.check_tts_spend.requests.get", return_value=self.usage(credits_by_day)),
            patch("office.management.commands.check_tts_spend.bugsnag.notify") as notify,
        ):
            out = StringIO()
            call_command("check_tts_spend", "--date", str(self.day), stdout=out)
        return notify, out.getvalue()

    def week(self, today_credits):
        credits = {self.day - datetime.timedelta(days=n): 500 for n in range(1, 8)}
        credits[self.day] = today_credits
        return credits

    def test_a_normal_day_does_not_alert(self):
        notify, out = self.run_check(self.week(520), self.day - datetime.timedelta(days=7))
        notify.assert_not_called()
        self.assertIn("billed 520 credits; recorded 1,000 characters", out)

    def test_unexplained_spend_alerts(self):
        notify, out = self.run_check(self.week(1000), self.day - datetime.timedelta(days=7))
        notify.assert_called_once()
        self.assertIn("about 500 credits are not explained", str(notify.call_args.args[0]))

    def test_regeneration_alerts(self):
        self.generation(self.day, 300, regenerated=True)
        notify, _ = self.run_check(self.week(650), self.day - datetime.timedelta(days=7))
        self.assertIn("300 characters", str(notify.call_args.args[0]))

    def test_ratio_is_skipped_until_a_baseline_exists(self):
        notify, out = self.run_check(self.week(1000), self.day - datetime.timedelta(days=1))
        notify.assert_not_called()

    @override_settings(ELEVENLABS_DAILY_CREDIT_BUDGET=900)
    def test_budget_alerts(self):
        notify, _ = self.run_check(self.week(1000), self.day)
        self.assertIn("over the daily budget of 900", str(notify.call_args.args[0]))

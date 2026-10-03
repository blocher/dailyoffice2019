import datetime
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from office.api.views import index


@override_settings(REST_FRAMEWORK={"UNAUTHENTICATED_USER": None})
class AudioWindowTests(SimpleTestCase):
    today = datetime.date(2026, 10, 3)
    offices = (
        "office/morning_prayer",
        "office/evening_prayer",
        "office/midday_prayer",
        "office/compline",
        "family/morning_prayer",
        "family/early_evening_prayer",
        "family/midday_prayer",
        "family/close_of_day_prayer",
    )

    def request(self, office, date, params=None, trusted=False):
        path = f"/api/v1/{office}/{date.year}-{date.month}-{date.day}"
        request = APIRequestFactory().get(path, params or {})
        if trusted:
            request._audio_prewarm = True
        match = resolve(path)
        with patch.object(index.timezone, "localdate", return_value=self.today):
            return match.func(request, *match.args, **match.kwargs)

    def test_all_offices_reject_outside_window_before_building_audio(self):
        with patch.object(index.OfficeAudioSerializer, "get_audio") as generate:
            for office in self.offices:
                for offset in (-4, 10, 9000):
                    with self.subTest(office=office, offset=offset):
                        response = self.request(
                            office,
                            self.today + datetime.timedelta(days=offset),
                            {
                                "include_audio_links": "true",
                                "_audio_prewarm": "true",
                            },
                        )
                        self.assertEqual(response.status_code, 403)
            generate.assert_not_called()

    def test_boundaries_text_and_trusted_job_reach_correct_serializer(self):
        with (
            patch.object(index, "EveningPrayer"),
            patch.object(index, "OfficeAudioSerializer") as audio,
            patch.object(index, "OfficeSerializer") as text,
        ):
            audio.return_value.data = {"audio": []}
            text.return_value.data = {"modules": []}
            for offset in (-3, 0, 9):
                response = self.request(
                    "office/evening_prayer",
                    self.today + datetime.timedelta(days=offset),
                    {
                        "include_audio_links": "true",
                    },
                )
                self.assertEqual(response.status_code, 200)
            future = datetime.date(2050, 11, 17)
            self.assertEqual(self.request("office/evening_prayer", future).status_code, 200)
            self.assertEqual(
                self.request(
                    "office/evening_prayer",
                    future,
                    {
                        "include_audio_links": "true",
                    },
                    trusted=True,
                ).status_code,
                200,
            )
            self.assertEqual(audio.call_count, 4)
            text.assert_called_once()

    def test_management_job_preserves_sequential_requested_range(self):
        from office.management.commands import update_audio_files

        calls = []

        def view(request, *args, **kwargs):
            self.assertTrue(request._audio_prewarm)
            calls.append(request.path.rsplit("/", 1)[-1])
            return SimpleNamespace(content=b"", status_code=200)

        with (
            patch.object(update_audio_files.timezone, "now", return_value=datetime.datetime(2026, 10, 3)),
            patch.object(update_audio_files, "resolve", return_value=SimpleNamespace(func=view, args=(), kwargs={})),
            patch("builtins.print"),
        ):
            call_command("update_audio_files", days=12, skip_yesterday=True, stdout=StringIO())
        expected = [
            (self.today + datetime.timedelta(days=i)).isoformat() for i in range(12) for _ in range(8 * 2 * 11)
        ]
        self.assertEqual(calls, expected)

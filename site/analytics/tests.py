import datetime

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import ResolverMatch, reverse
from rest_framework.test import APIClient

from analytics.middleware import AnalyticsMiddleware
from analytics.models import AnalyticsEvent
from analytics.utils import parse_client_meta, record_audio_loaded
from office.models import Setting, SettingOption

IOS_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
ANDROID_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _resolver(url_name):
    return ResolverMatch(
        func=lambda request: None,
        args=(),
        kwargs={"year": 2026, "month": 7, "day": 19},
        url_name=url_name,
    )


class OfficeViewMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _run(self, url_name="morning_prayer_view", query="", status=200, **headers):
        request = self.factory.get(f"/api/v1/office/morning_prayer/2026-7-19{query}", **headers)
        resolver = _resolver(url_name)

        def get_response(req):
            req.resolver_match = resolver
            return HttpResponse(status=status)

        AnalyticsMiddleware(get_response)(request)

    def test_office_view_logged_once(self):
        self._run(HTTP_X_CLIENT_ID="abc-123", HTTP_X_CLIENT_PLATFORM="ios", HTTP_USER_AGENT=IOS_UA)
        events = AnalyticsEvent.objects.all()
        self.assertEqual(events.count(), 1)
        event = events.first()
        self.assertEqual(event.event_type, AnalyticsEvent.OFFICE_VIEW)
        self.assertEqual(event.service_type, AnalyticsEvent.SERVICE_OFFICE)
        self.assertEqual(event.office, "morning_prayer")
        self.assertEqual(event.office_date, datetime.date(2026, 7, 19))
        self.assertEqual(event.client_id, "abc-123")
        self.assertEqual(event.platform, "ios")
        self.assertEqual(event.os, "iOS")

    def test_include_audio_links_not_counted(self):
        self._run(query="?include_audio_links=true")
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_bible_translation_captured(self):
        self._run(query="?bible_translation=kjv")
        self.assertEqual(AnalyticsEvent.objects.first().translation, "kjv")

    def test_non_2xx_not_counted(self):
        self._run(status=404)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_unrelated_route_not_counted(self):
        self._run(url_name="day_view")
        self.assertEqual(AnalyticsEvent.objects.count(), 0)

    def test_family_service_type(self):
        self._run(url_name="family_close_of_day_view")
        event = AnalyticsEvent.objects.first()
        self.assertEqual(event.service_type, AnalyticsEvent.SERVICE_FAMILY)
        self.assertEqual(event.office, "close_of_day_prayer")


class SettingsCaptureTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
        setting = Setting.objects.create(name="bible_translation", title="Bible Translation")
        SettingOption.objects.create(setting=setting, name="ESV", value="esv", order=1)
        SettingOption.objects.create(setting=setting, name="KJV", value="kjv", order=2)

    def _run(self, query):
        request = self.factory.get(f"/api/v1/office/morning_prayer/2026-7-19{query}")
        resolver = _resolver("morning_prayer_view")

        def get_response(req):
            req.resolver_match = resolver
            return HttpResponse(status=200)

        AnalyticsMiddleware(get_response)(request)

    def test_only_known_settings_captured(self):
        self._run("?bible_translation=kjv&psalter=60&extra_collects=abc&include_audio_links=")
        event = AnalyticsEvent.objects.get()
        self.assertEqual(event.settings.get("bible_translation"), "kjv")
        # Not a registered Setting name in this test -> excluded.
        self.assertNotIn("psalter", event.settings)
        self.assertNotIn("extra_collects", event.settings)
        self.assertNotIn("include_audio_links", event.settings)


class AudioLoadedTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_initial_request_logged(self):
        request = self.factory.get("/api/v1/audio_track/x.mp3?cid=zzz", HTTP_USER_AGENT=DESKTOP_UA)
        record_audio_loaded(request, is_initial_request=True)
        self.assertEqual(AnalyticsEvent.objects.filter(event_type=AnalyticsEvent.AUDIO_LOADED).count(), 1)
        self.assertEqual(AnalyticsEvent.objects.first().client_id, "zzz")

    def test_range_continuation_not_logged(self):
        request = self.factory.get("/api/v1/audio_track/x.mp3")
        record_audio_loaded(request, is_initial_request=False)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)


class IngestEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("analytics_event")

    def test_audio_play_created(self):
        response = self.client.post(
            self.url,
            {
                "event_type": "audio_play",
                "service_type": "office",
                "office": "compline",
                "office_date": "2026-7-19",
                "translation": "esv",
                "client_id": "user-1",
            },
            format="json",
            HTTP_X_CLIENT_PLATFORM="android",
            HTTP_USER_AGENT=ANDROID_UA,
        )
        self.assertEqual(response.status_code, 204)
        event = AnalyticsEvent.objects.get()
        self.assertEqual(event.event_type, AnalyticsEvent.AUDIO_PLAY)
        self.assertEqual(event.office, "compline")
        self.assertEqual(event.office_date, datetime.date(2026, 7, 19))
        self.assertEqual(event.platform, "android")
        self.assertEqual(event.os, "Android")

    def test_office_view_event_rejected(self):
        response = self.client.post(self.url, {"event_type": "office_view"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)


class ClientMetaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_explicit_platform_header(self):
        request = self.factory.get("/", HTTP_X_CLIENT_PLATFORM="ios", HTTP_USER_AGENT=IOS_UA)
        platform, browser, os_family = parse_client_meta(request)
        self.assertEqual(platform, "ios")
        self.assertEqual(os_family, "iOS")

    def test_declared_platform_argument_wins(self):
        request = self.factory.get("/", HTTP_USER_AGENT=ANDROID_UA)
        platform, _, _ = parse_client_meta(request, declared_platform="android")
        self.assertEqual(platform, "android")

    def test_unknown_platform_without_header(self):
        request = self.factory.get("/", HTTP_USER_AGENT=DESKTOP_UA)
        platform, browser, os_family = parse_client_meta(request)
        self.assertEqual(platform, "unknown")
        self.assertIn("Windows", os_family)
        self.assertIn("Chrome", browser)

    def test_invalid_platform_falls_back_to_unknown(self):
        request = self.factory.get("/", HTTP_X_CLIENT_PLATFORM="banana", HTTP_USER_AGENT=DESKTOP_UA)
        platform, _, _ = parse_client_meta(request)
        self.assertEqual(platform, "unknown")


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(username="staff", password="pw", is_staff=True, is_superuser=True)

    def test_dashboard_renders_for_staff(self):
        AnalyticsEvent.objects.create(event_type=AnalyticsEvent.OFFICE_VIEW, office="compline", client_id="a")
        AnalyticsEvent.objects.create(event_type=AnalyticsEvent.AUDIO_PLAY, office="compline", client_id="a")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:analytics_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analytics dashboard")

    def test_dashboard_shows_setting_distribution(self):
        cache.clear()
        setting = Setting.objects.create(name="bible_translation", title="Bible Translation")
        SettingOption.objects.create(setting=setting, name="ESV", value="esv", order=1)
        AnalyticsEvent.objects.create(
            event_type=AnalyticsEvent.OFFICE_VIEW,
            office="compline",
            client_id="a",
            settings={"bible_translation": "esv"},
        )
        AnalyticsEvent.objects.create(
            event_type=AnalyticsEvent.OFFICE_VIEW,
            office="compline",
            client_id="b",
            settings={"bible_translation": "esv"},
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:analytics_dashboard") + "?setting=bible_translation")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Settings usage")
        self.assertContains(response, "Bible Translation")
        self.assertContains(response, "ESV")

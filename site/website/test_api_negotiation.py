import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from churchcal.calendar_feeds import ChurchCalendarFeedService

BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


# Production has no browsable API (DEBUG off); pin that here so the result
# does not depend on the local .env.
@patch.object(APIView, "renderer_classes", [JSONRenderer])
@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class APIContentNegotiationTests(TestCase):
    def assert_json(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        return response.json()

    def test_html_only_accept_gets_json(self):
        # Google Translate's proxy forwards the app's XHRs like this.
        data = self.assert_json(self.client.get("/api/v1/available_settings/", HTTP_ACCEPT="text/html"))
        self.assertIsInstance(data, list)

    def test_browser_accept_gets_json(self):
        self.assert_json(self.client.get("/api/v1/available_settings/", HTTP_ACCEPT=BROWSER_ACCEPT))

    def test_json_accept_and_format_override_still_work(self):
        self.assert_json(self.client.get("/api/v1/available_settings/", HTTP_ACCEPT="application/json"))
        self.assert_json(self.client.get("/api/v1/available_settings/?format=json", HTTP_ACCEPT="text/html"))

    def test_unknown_format_is_not_found(self):
        response = self.client.get("/api/v1/available_settings/?format=api", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 404)

    def test_calendar_feed_is_still_ics(self):
        with tempfile.TemporaryDirectory() as directory:
            feed = Path(directory) / "feed.ics"
            feed.write_bytes(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")
            with patch.object(ChurchCalendarFeedService, "get_feed_path", return_value=feed):
                for accept in ("text/html", "text/calendar", "*/*"):
                    with self.subTest(accept=accept):
                        response = self.client.get("/api/v1/calendar/feed/every.ics", HTTP_ACCEPT=accept)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response["Content-Type"], "text/calendar; charset=utf-8")
                        self.assertEqual(b"".join(response.streaming_content), feed.read_bytes())

    def test_api_docs_still_render(self):
        response = self.client.get("/api/", HTTP_ACCEPT=BROWSER_ACCEPT)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        response = self.client.get("/api/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("paths", response.json())

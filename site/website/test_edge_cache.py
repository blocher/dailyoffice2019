"""Cloudflare edge caching of public API content (website/edge_cache.py)."""

from unittest import mock

import requests
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from office import response_cache
from website import edge_cache
from website.edge_cache import EdgeCacheMiddleware

EDGE = "public, max-age=0, s-maxage=86400"


@override_settings(EDGE_CACHE_SECONDS=86400)
class EdgeCacheMiddlewareTests(SimpleTestCase):
    def respond(self, path, method="get", status=200, **headers):
        response = HttpResponse(status=status, headers=headers)
        request = getattr(RequestFactory(), method)(path)
        return EdgeCacheMiddleware(lambda request: response)(request)

    def test_content_paths_are_edge_cached_and_tagged(self):
        for path in (
            "/api/v1/office/morning_prayer/2026-11-2",
            "/api/v1/family/close_of_day_prayer/2026-11-02",
            "/api/v1/calendar/2026-11-1",
            "/api/v1/calendar/2026-11",
            "/api/v1/readings/2026-11-1",
            "/api/v1/available_settings/",
            "/api/v1/litany",
            "/api/v1/psalms/topics/",
        ):
            with self.subTest(path):
                response = self.respond(path)
                self.assertEqual(response["Cache-Control"], EDGE)
                self.assertEqual(response["Cache-Tag"], "content")

    def test_site_messages_are_kept_only_a_minute(self):
        response = self.respond("/api/v1/site_messages/")
        self.assertEqual(response["Cache-Control"], "public, max-age=0, s-maxage=60")

    def test_other_paths_are_left_alone(self):
        for path in (
            "/api/v1/office/compline/2026-11-1/audio",
            "/api/v1/readings_audio/morning/2026-11-1",
            "/api/v1/audio_track/x.mp3",
            "/api/v1/calendar/feed/every.ics",
            "/api/v1/analytics/event",
            "/admin/",
        ):
            with self.subTest(path):
                self.assertFalse(self.respond(path).has_header("Cache-Tag"))

    def test_only_successful_reads_without_their_own_cache_control(self):
        path = "/api/v1/litany"
        self.assertFalse(self.respond(path, method="post").has_header("Cache-Tag"))
        self.assertFalse(self.respond(path, status=500).has_header("Cache-Tag"))
        kept = self.respond(path, **{"Cache-Control": "no-store"})
        self.assertEqual(kept["Cache-Control"], "no-store")
        self.assertFalse(kept.has_header("Cache-Tag"))

    def test_responses_setting_a_cookie_are_not_edge_cached(self):
        response = HttpResponse()
        response.set_cookie("csrftoken", "x")
        response = EdgeCacheMiddleware(lambda request: response)(RequestFactory().get("/api/v1/litany"))
        self.assertFalse(response.has_header("Cache-Tag"))


class PurgeTests(SimpleTestCase):
    @override_settings(CLOUDFLARE_ZONE_ID="", CLOUDFLARE_API_TOKEN="")
    def test_does_nothing_unconfigured(self):
        with mock.patch.object(edge_cache.requests, "post") as post:
            self.assertFalse(edge_cache.purge())
        post.assert_not_called()

    @override_settings(CLOUDFLARE_ZONE_ID="zone", CLOUDFLARE_API_TOKEN="token")
    def test_purges_the_content_tag(self):
        with mock.patch.object(edge_cache.requests, "post") as post:
            self.assertTrue(edge_cache.purge())
        post.assert_called_once_with(
            "https://api.cloudflare.com/client/v4/zones/zone/purge_cache",
            json={"tags": ["content"]},
            headers={"Authorization": "Bearer token"},
            timeout=5,
        )

    @override_settings(CLOUDFLARE_ZONE_ID="zone", CLOUDFLARE_API_TOKEN="token")
    def test_failures_are_logged_not_raised(self):
        with (
            mock.patch.object(edge_cache.requests, "post", side_effect=requests.ConnectionError),
            self.assertLogs("website.edge_cache", "WARNING"),
        ):
            self.assertFalse(edge_cache.purge())

    def test_clearing_the_office_cache_purges(self):
        with mock.patch.object(edge_cache, "purge") as purge:
            response_cache.clear()
        purge.assert_called_once_with()

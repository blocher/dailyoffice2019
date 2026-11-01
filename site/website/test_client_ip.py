"""The client's address, from behind Cloudflare and nginx (website/client_ip.py)."""

from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from website.client_ip import client_ip

CLOUDFLARE = "162.158.63.249"


class ClientIpTests(SimpleTestCase):
    def ip(self, **meta):
        return client_ip(RequestFactory().get("/", **meta))

    def test_through_cloudflare_it_is_cloudflares_client(self):
        self.assertEqual(
            self.ip(
                HTTP_X_REAL_IP=CLOUDFLARE,
                HTTP_CF_CONNECTING_IP="203.0.113.7",
                HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.7, " + CLOUDFLARE,
            ),
            "203.0.113.7",
        )

    def test_straight_to_the_server_it_is_nginxs_peer(self):
        # Not believed from anyone but Cloudflare.
        self.assertEqual(
            self.ip(HTTP_X_REAL_IP="198.51.100.9", HTTP_CF_CONNECTING_IP="1.2.3.4", HTTP_X_FORWARDED_FOR="5.6.7.8"),
            "198.51.100.9",
        )

    def test_cloudflare_over_ipv6(self):
        self.assertEqual(
            self.ip(HTTP_X_REAL_IP="2606:4700::1", HTTP_CF_CONNECTING_IP="2001:db8::5"),
            "2001:db8::5",
        )

    def test_without_nginx_it_is_the_connection(self):
        self.assertEqual(self.ip(REMOTE_ADDR="192.0.2.4", HTTP_X_FORWARDED_FOR="5.6.7.8"), "192.0.2.4")

    def test_nonsense_is_ignored(self):
        self.assertEqual(self.ip(HTTP_X_REAL_IP=CLOUDFLARE, HTTP_CF_CONNECTING_IP="nope"), CLOUDFLARE)
        self.assertEqual(self.ip(HTTP_X_REAL_IP="nope", REMOTE_ADDR="192.0.2.4"), "192.0.2.4")


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ThrottleByClientIpTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_a_forged_forwarded_for_does_not_escape_the_throttle(self):
        from analytics.views import OfflineOfficeViewsThrottle

        throttle = OfflineOfficeViewsThrottle()
        factory = RequestFactory()
        for forged in ("1.1.1.1", "2.2.2.2"):
            request = factory.post("/", HTTP_X_REAL_IP="198.51.100.9", HTTP_X_FORWARDED_FOR=forged)
            self.assertEqual(throttle.get_ident(request), "198.51.100.9")

    def test_offline_views_are_capped_per_address_and_day(self):
        from analytics import offline_views

        view = {"service_type": "office", "office": "compline"}

        def post(client_id, count):
            return (
                APIClient()
                .post(
                    "/api/v1/analytics/offline_views",
                    {"client_id": client_id, "views": [view] * count},
                    format="json",
                    HTTP_X_REAL_IP="198.51.100.9",
                )
                .json()["accepted"]
            )

        # A new device id each time: each is under its own daily cap.
        with mock.patch.object(offline_views, "MAX_PER_IP_PER_DAY", 20):
            accepted = [post(f"device-{i}", 8) for i in range(4)]
        self.assertEqual(accepted, [8, 8, 4, 0])

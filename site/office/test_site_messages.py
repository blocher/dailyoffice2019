"""Site messages: platform targeting and optional app version rules."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory

from office.api.views.index import SiteMessageViewSet
from office.models import SiteMessage, parse_app_version


class ParseAppVersionTests(SimpleTestCase):
    def test_pads_so_short_and_long_forms_are_equal(self):
        self.assertEqual(parse_app_version("4"), parse_app_version("4.0.0"))
        self.assertLess(parse_app_version("4.0.9"), parse_app_version("4.1"))
        self.assertLess(parse_app_version("3.10.0"), parse_app_version("4.0.0"))
        self.assertGreater(parse_app_version("3.10.0"), parse_app_version("3.9.9"))

    def test_ignores_suffixes_and_rejects_non_numbers(self):
        self.assertEqual(parse_app_version("4.1.0-beta"), parse_app_version("4.1"))
        self.assertIsNone(parse_app_version(""))
        self.assertIsNone(parse_app_version(None))
        self.assertIsNone(parse_app_version("latest"))


class MatchesAppVersionTests(SimpleTestCase):
    def message(self, rule, version="", version_to=""):
        return SiteMessage(text="x", ios_version_rule=rule, ios_version=version, ios_version_to=version_to)

    def assertMatches(self, message, expected):
        for app_version, should_match in expected.items():
            with self.subTest(app_version=app_version):
                self.assertEqual(message.matches_app_version("ios", app_version), should_match)

    def test_rules(self):
        self.assertMatches(self.message("lt", "4.0.0"), {"3.1.3": True, "4.0.0": False, "4.0.1": False})
        self.assertMatches(self.message("lte", "4.0.0"), {"3.1.3": True, "4.0": True, "4.0.1": False})
        self.assertMatches(self.message("eq", "4.0.0"), {"3.1.3": False, "4": True, "4.0.1": False})
        self.assertMatches(self.message("gte", "4.1"), {"4.0.9": False, "4.1.0": True, "5.0": True})
        self.assertMatches(self.message("gt", "4.1"), {"4.1.0": False, "4.1.1": True})
        self.assertMatches(
            self.message("between", "4.0", "4.2"), {"3.9": False, "4.0.0": True, "4.2.0": True, "4.2.1": False}
        )

    def test_no_rule_matches_everything(self):
        self.assertMatches(self.message(""), {"": True, "1.0": True})

    def test_rule_hides_message_from_unknown_versions(self):
        self.assertMatches(self.message("lt", "4.0.0"), {"": False, "unknown": False})

    def test_rules_apply_per_platform(self):
        message = SiteMessage(
            text="x", ios_version_rule="gte", ios_version="4.1", android_version_rule="lt", android_version="4.0"
        )
        self.assertTrue(message.matches_app_version("ios", "4.1"))
        self.assertFalse(message.matches_app_version("android", "4.1"))
        self.assertTrue(message.matches_app_version("android", "3.2"))
        self.assertTrue(message.matches_app_version("web", ""))


class SiteMessageCleanTests(SimpleTestCase):
    def errors(self, **fields):
        try:
            SiteMessage(text="x", **fields).full_clean(exclude=["uuid"])
        except ValidationError as error:
            return error.message_dict
        return {}

    def test_valid_rules(self):
        self.assertEqual(self.errors(), {})
        self.assertEqual(self.errors(ios_version_rule="lt", ios_version="4.0.0"), {})
        self.assertEqual(
            self.errors(android_version_rule="between", android_version="4.0", android_version_to="4.2"), {}
        )

    def test_rule_needs_a_version(self):
        self.assertIn("ios_version", self.errors(ios_version_rule="gte"))

    def test_version_needs_a_rule(self):
        self.assertIn("android_version_rule", self.errors(android_version="4.0"))

    def test_between_needs_an_ordered_upper_bound(self):
        self.assertIn("ios_version_to", self.errors(ios_version_rule="between", ios_version="4.0"))
        self.assertIn(
            "ios_version_to", self.errors(ios_version_rule="between", ios_version="4.2", ios_version_to="4.0")
        )

    def test_upper_bound_only_for_between(self):
        self.assertIn("ios_version_to", self.errors(ios_version_rule="gte", ios_version="4.0", ios_version_to="5"))

    def test_version_format(self):
        self.assertIn("ios_version", self.errors(ios_version_rule="gte", ios_version="four"))


class SiteMessageApiTests(TestCase):
    def setUp(self):
        self.everyone = SiteMessage.objects.create(text="Everyone", order=0)
        self.upgrade = SiteMessage.objects.create(
            text="Please upgrade",
            order=1,
            ios_version_rule="lt",
            ios_version="4.0.0",
            android_version_rule="lt",
            android_version="4.0.0",
        )
        self.feature = SiteMessage.objects.create(
            text="New on iOS", order=2, show_on_android=False, ios_version_rule="gte", ios_version="4.1"
        )

    def texts(self, **params):
        request = APIRequestFactory().get("/api/v1/site_messages/", params)
        response = SiteMessageViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)
        return [message["text"] for message in response.data]

    def test_web_ignores_version_rules(self):
        self.assertEqual(self.texts(platform="web"), ["Everyone", "Please upgrade", "New on iOS"])

    def test_old_ios_gets_the_upgrade_notice(self):
        self.assertEqual(self.texts(platform="ios", app_version="3.2.0"), ["Everyone", "Please upgrade"])

    def test_new_ios_gets_the_feature_announcement(self):
        self.assertEqual(self.texts(platform="ios", app_version="4.1.0"), ["Everyone", "New on iOS"])

    def test_android_uses_its_own_rule(self):
        self.assertEqual(self.texts(platform="android", app_version="3.2.0"), ["Everyone", "Please upgrade"])
        self.assertEqual(self.texts(platform="android", app_version="4.1.0"), ["Everyone"])

    def test_app_without_a_version_gets_only_unrestricted_messages(self):
        self.assertEqual(self.texts(platform="ios"), ["Everyone"])


class SiteMessageAdminTests(TestCase):
    def test_change_form_and_list_show_version_rules(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(user)
        message = SiteMessage.objects.create(
            text="Please upgrade", ios_version_rule="between", ios_version="3.0", ios_version_to="3.9"
        )
        response = self.client.get(f"/admin/office/sitemessage/{message.pk}/change/")
        self.assertContains(response, 'name="android_version_rule"')
        self.assertContains(response, 'name="ios_version_to"')
        self.assertContains(self.client.get("/admin/office/sitemessage/"), "iOS 3.0–3.9")

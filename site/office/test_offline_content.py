"""Offline downloads: the content change log, its endpoint, and its analytics."""

import datetime
from io import StringIO

from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from analytics.middleware import AnalyticsMiddleware
from analytics.models import AnalyticsEvent
from office import offline_content
from office.models import AboutItem, ContentChange, SiteMessage


class MergeRangesTests(SimpleTestCase):
    def test_merges_overlapping_and_adjacent_ranges(self):
        d = datetime.date
        merged = offline_content.merge_ranges(
            [(d(2026, 12, 5), d(2026, 12, 6)), (d(2026, 12, 1), d(2026, 12, 3)), (d(2026, 12, 4), d(2026, 12, 4))]
        )
        self.assertEqual(merged, [(d(2026, 12, 1), d(2026, 12, 6))])

    def test_keeps_separate_ranges_apart(self):
        d = datetime.date
        merged = offline_content.merge_ranges([(d(2026, 12, 1), d(2026, 12, 1)), (d(2026, 12, 3), d(2026, 12, 3))])
        self.assertEqual(len(merged), 2)


class ChangesSinceTests(TestCase):
    def test_a_new_device_only_learns_the_version(self):
        change = offline_content.record_change(note="x")
        self.assertEqual(
            offline_content.changes_since(0), {"version": change.id, "all": False, "urgent": False, "dates": []}
        )

    def test_nothing_new(self):
        change = offline_content.record_change()
        summary = offline_content.changes_since(change.id)
        self.assertFalse(summary["all"])
        self.assertEqual(summary["dates"], [])

    def test_dated_changes_are_merged(self):
        first = offline_content.record_change(start_date=datetime.date(2026, 12, 1))
        offline_content.record_change(start_date=datetime.date(2026, 12, 2), end_date=datetime.date(2026, 12, 4))
        offline_content.record_change(start_date=datetime.date(2026, 12, 9))
        summary = offline_content.changes_since(first.id - 1)
        self.assertFalse(summary["all"])
        self.assertEqual(summary["dates"], [["2026-12-01", "2026-12-04"], ["2026-12-09", "2026-12-09"]])

    def test_an_undated_change_covers_everything(self):
        first = offline_content.record_change(start_date=datetime.date(2026, 12, 1))
        offline_content.record_change(urgent=True)
        summary = offline_content.changes_since(first.id - 1)
        self.assertTrue(summary["all"])
        self.assertTrue(summary["urgent"])
        self.assertEqual(summary["dates"], [])

    def test_only_changes_after_the_version_count(self):
        old = offline_content.record_change(urgent=True)
        offline_content.record_change(start_date=datetime.date(2026, 12, 1))
        summary = offline_content.changes_since(old.id)
        self.assertFalse(summary["urgent"])
        self.assertEqual(summary["dates"], [["2026-12-01", "2026-12-01"]])

    def test_reversed_dates_are_put_in_order(self):
        change = offline_content.record_change(
            start_date=datetime.date(2026, 12, 5), end_date=datetime.date(2026, 12, 1)
        )
        self.assertEqual(change.start_date, datetime.date(2026, 12, 1))
        self.assertEqual(change.end_date, datetime.date(2026, 12, 5))


class ContentChangesEndpointTests(TestCase):
    def test_endpoint(self):
        first = offline_content.record_change()
        offline_content.record_change(start_date=datetime.date(2026, 12, 25))
        response = APIClient().get("/api/v1/content_changes", {"since": first.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dates"], [["2026-12-25", "2026-12-25"]])
        self.assertIn("max-age=60", response["Cache-Control"])

    def test_bad_since_is_treated_as_new(self):
        offline_content.record_change()
        response = APIClient().get("/api/v1/content_changes", {"since": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dates"], [])


class AdminEditsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("editor", password="x")

    def log(self, model, action=CHANGE):
        return LogEntry.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(model),
            object_id="1",
            object_repr="Something",
            action_flag=action,
        )

    def test_content_edits_record_a_soft_change(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.log(AboutItem, ADDITION)
        change = ContentChange.objects.get()
        self.assertEqual(change.source, ContentChange.SOURCE_ADMIN)
        self.assertFalse(change.urgent)
        self.assertIsNone(change.start_date)
        self.assertIn("office.aboutitem", change.note)

    def test_edits_that_never_change_an_office_are_ignored(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.log(SiteMessage)
            self.log(ContentChange)
            self.log(get_user_model())
        self.assertFalse(ContentChange.objects.exists())


class InvalidateOfflineCommandTests(TestCase):
    def test_dates(self):
        call_command("invalidate_offline", "--dates", "2026-12-01:2026-12-07", "--note", "typo", stdout=StringIO())
        change = ContentChange.objects.get()
        self.assertEqual(
            (change.start_date, change.end_date), (datetime.date(2026, 12, 1), datetime.date(2026, 12, 7))
        )
        self.assertEqual(change.note, "typo")
        self.assertFalse(change.urgent)

    def test_all_urgent(self):
        call_command("invalidate_offline", "--all", "--urgent", stdout=StringIO())
        change = ContentChange.objects.get()
        self.assertIsNone(change.start_date)
        self.assertTrue(change.urgent)


class OfflineSyncAnalyticsTests(TestCase):
    def test_offline_downloads_are_not_office_views(self):
        factory = RequestFactory()
        request = factory.get("/api/v1/office/morning_prayer/2026-11-2", HTTP_X_OFFLINE_SYNC="1")

        class Match:
            url_name = "morning_prayer_view"
            kwargs = {"year": 2026, "month": 11, "day": 2}

        request.resolver_match = Match()

        class Ok:
            status_code = 200

        AnalyticsMiddleware._maybe_log_office_view(request, Ok())
        self.assertFalse(AnalyticsEvent.objects.exists())

        request = factory.get("/api/v1/office/morning_prayer/2026-11-2")
        request.resolver_match = Match()
        AnalyticsMiddleware._maybe_log_office_view(request, Ok())
        self.assertEqual(AnalyticsEvent.objects.count(), 1)

    def test_offline_views_are_recorded_with_their_time(self):
        viewed_at = timezone.now() - datetime.timedelta(days=2)
        response = APIClient().post(
            "/api/v1/analytics/offline_views",
            {
                "client_id": "abc",
                "platform": "ios",
                "views": [
                    {
                        "service_type": "office",
                        "office": "morning_prayer",
                        "office_date": "2026-11-2",
                        "translation": "esv",
                        "viewed_at": viewed_at.isoformat(),
                        "settings": {"not_a_setting": "x"},
                    },
                    {"service_type": "office", "office": "not_an_office"},
                    "junk",
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"accepted": 1})
        event = AnalyticsEvent.objects.get()
        self.assertTrue(event.offline)
        self.assertEqual(event.event_type, AnalyticsEvent.OFFICE_VIEW)
        self.assertEqual(event.office_date, datetime.date(2026, 11, 2))
        self.assertEqual(event.platform, AnalyticsEvent.PLATFORM_IOS)
        self.assertEqual(event.settings, {})
        self.assertLess(abs((event.created - viewed_at).total_seconds()), 1)

    def test_times_are_clamped(self):
        APIClient().post(
            "/api/v1/analytics/offline_views",
            {"views": [{"service_type": "family", "office": "morning_prayer", "viewed_at": "1999-01-01T00:00:00Z"}]},
            format="json",
        )
        event = AnalyticsEvent.objects.get()
        self.assertGreater(event.created, timezone.now() - datetime.timedelta(days=61))

    def test_views_must_be_a_list(self):
        response = APIClient().post("/api/v1/analytics/offline_views", {"views": "x"}, format="json")
        self.assertEqual(response.status_code, 400)

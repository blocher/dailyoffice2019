from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from icalendar import Calendar

from churchcal.calendar_feeds import (
    ChurchCalendarFeedBuilder,
    FeedDay,
    OfficeDayDetails,
    OfficeReadingsResolver,
    get_feed_window_start_years,
)
from churchcal.ce_bce_replacement import replace_ce_bce_in_text
from churchcal.utils import advent
from office.models import StandardOfficeDay, ThirtyDayPsalterDay


class CeBceReplacementTests(SimpleTestCase):
    def test_replaces_bce_variants(self):
        cases = [
            ("born circa 300 BCE", "born circa 300 BC"),
            ("born circa 300 B.C.E.", "born circa 300 BC"),
            ("born circa 300 b.c.e.", "born circa 300 BC"),
            ("born circa 300 bce.", "born circa 300 BC"),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                updated, replacements = replace_ce_bce_in_text(original)
                self.assertEqual(updated, expected)
                self.assertTrue(replacements)

    def test_replaces_ce_variants(self):
        cases = [
            ("died in 100 CE", "died in 100 AD"),
            ("died in 100 C.E.", "died in 100 AD"),
            ("died in 100 ce.", "died in 100 AD"),
            ("(100 CE)", "(100 AD)"),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                updated, replacements = replace_ce_bce_in_text(original)
                self.assertEqual(updated, expected)
                self.assertTrue(replacements)

    def test_includes_context_around_replacements(self):
        text = "He was born in Alexandria around 300 BCE and died in Rome in 100 CE."
        _, replacements = replace_ce_bce_in_text(text, context_chars=20)
        self.assertEqual(len(replacements), 2)
        self.assertIn("300 BCE", replacements[0].context_before)
        self.assertIn("300 BC", replacements[0].context_after)
        self.assertIn("100 CE", replacements[1].context_before)
        self.assertIn("100 AD", replacements[1].context_after)

    def test_does_not_replace_within_words_or_ids(self):
        cases = [
            "face",
            "service",
            "acceptance",
            "abce",
            "uuid_bce_field",
            "foo-ce-bar",
            "something.ce.other",
            "abc123bce456",
            "https://example.com/bce/article",
            "early CE period",
            "source-id-ce-123",
        ]
        for original in cases:
            with self.subTest(original=original):
                updated, replacements = replace_ce_bce_in_text(original)
                self.assertEqual(updated, original)
                self.assertEqual(replacements, [])

    def test_replaces_at_line_boundaries(self):
        text = "300 BCE\nDied in 100 CE."
        updated, replacements = replace_ce_bce_in_text(text)
        self.assertEqual(updated, "300 BC\nDied in 100 AD")
        self.assertEqual(len(replacements), 2)


class CalendarFeedWindowTests(SimpleTestCase):
    def test_feed_window_uses_previous_current_and_next_two_church_years(self):
        self.assertEqual(get_feed_window_start_years(date(2026, 4, 26)), [2024, 2025, 2026, 2027])

    def test_feed_window_rolls_forward_on_advent(self):
        advent_start = advent(2026)
        before_advent = advent_start - date.resolution

        self.assertEqual(get_feed_window_start_years(before_advent), [2024, 2025, 2026, 2027])
        self.assertEqual(get_feed_window_start_years(advent_start), [2025, 2026, 2027, 2028])


class CalendarFeedScopeTests(SimpleTestCase):
    def test_scope_selection_matches_major_major_minor_and_every_rules(self):
        office_details = OfficeDayDetails(
            mp_psalms_30_day="1",
            mp_psalms_60_day="1, 2",
            mp_reading_1="Genesis 1",
            mp_reading_2="John 1",
            ep_psalms_30_day="3",
            ep_psalms_60_day="4, 5",
            ep_reading_1="Romans 1",
            ep_reading_2="Luke 1",
        )
        major_day = FeedDay(
            event_date=date(2026, 3, 25),
            major_feast_name="The Annunciation",
            major_or_minor_feast_name="The Annunciation",
            primary_name="The Annunciation",
            commemorations=("The Annunciation",),
            fast_day=False,
            feast_day=True,
            office_details=office_details,
            mass_reading_citations=("Isaiah 7:10-14",),
        )
        commemoration_day = FeedDay(
            event_date=date(2026, 1, 2),
            major_feast_name=None,
            major_or_minor_feast_name="St. Example",
            primary_name="St. Example",
            commemorations=("St. Example",),
            fast_day=False,
            feast_day=False,
            office_details=office_details,
            mass_reading_citations=(),
        )
        feria_day = FeedDay(
            event_date=date(2026, 1, 3),
            major_feast_name=None,
            major_or_minor_feast_name=None,
            primary_name="Saturday after the First Sunday after Christmas",
            commemorations=("Saturday after the First Sunday after Christmas",),
            fast_day=False,
            feast_day=False,
            office_details=office_details,
            mass_reading_citations=(),
        )

        self.assertTrue(major_day.should_include_for_scope("major"))
        self.assertTrue(major_day.should_include_for_scope("major_minor"))
        self.assertTrue(major_day.should_include_for_scope("every"))

        self.assertFalse(commemoration_day.should_include_for_scope("major"))
        self.assertTrue(commemoration_day.should_include_for_scope("major_minor"))
        self.assertTrue(commemoration_day.should_include_for_scope("every"))

        self.assertFalse(feria_day.should_include_for_scope("major"))
        self.assertFalse(feria_day.should_include_for_scope("major_minor"))
        self.assertTrue(feria_day.should_include_for_scope("every"))

        self.assertEqual(feria_day.summary_for_scope("every"), feria_day.primary_name)


class CalendarFeedSerializationTests(SimpleTestCase):
    def setUp(self):
        self.office_details = OfficeDayDetails(
            mp_psalms_30_day="1",
            mp_psalms_60_day="1, 2",
            mp_reading_1="Genesis 1",
            mp_reading_2="John 1",
            ep_psalms_30_day="3",
            ep_psalms_60_day="4, 5",
            ep_reading_1="Romans 1",
            ep_reading_2="Luke 1",
        )
        self.major_day = FeedDay(
            event_date=date(2026, 3, 25),
            major_feast_name="The Annunciation",
            major_or_minor_feast_name="The Annunciation",
            primary_name="The Annunciation",
            commemorations=("The Annunciation",),
            fast_day=False,
            feast_day=True,
            office_details=self.office_details,
            mass_reading_citations=("Isaiah 7:10-14", "Luke 1:26-38"),
        )
        self.feria_day = FeedDay(
            event_date=date(2026, 3, 26),
            major_feast_name=None,
            major_or_minor_feast_name=None,
            primary_name="Thursday after the Annunciation",
            commemorations=("Thursday after the Annunciation",),
            fast_day=False,
            feast_day=False,
            office_details=self.office_details,
            mass_reading_citations=(),
        )

    def _builder(self):
        builder = ChurchCalendarFeedBuilder.__new__(ChurchCalendarFeedBuilder)
        builder.generated_at = datetime(2026, 4, 26, 12, 0, 0)
        return builder

    def test_normal_feed_contains_event_urls_descriptions_and_scope_filtering(self):
        parsed = Calendar.from_ical(self._builder().serialize("major", [self.major_day, self.feria_day]))
        events = [component for component in parsed.walk() if component.name == "VEVENT"]

        self.assertEqual(len(events), 1)
        self.assertEqual(str(events[0].get("summary")), "The Annunciation")
        self.assertEqual(str(events[0].get("url")), self.major_day.day_page_url)
        self.assertIn("MORNING PRAYER", str(events[0].get("description")))
        self.assertIn("Isaiah 7:10-14", str(events[0].get("description")))

    def test_cancel_feed_marks_events_cancelled_with_stable_uid(self):
        builder = self._builder()
        normal = Calendar.from_ical(builder.serialize("every", [self.major_day]))
        canceled = Calendar.from_ical(builder.serialize("every", [self.major_day], canceled=True))

        normal_event = [component for component in normal.walk() if component.name == "VEVENT"][0]
        canceled_event = [component for component in canceled.walk() if component.name == "VEVENT"][0]

        self.assertEqual(str(normal_event.get("uid")), str(canceled_event.get("uid")))
        self.assertEqual(str(canceled_event.get("status")), "CANCELLED")
        self.assertEqual(canceled_event.decoded("sequence"), 1)


class CalendarFeedEndpointTests(SimpleTestCase):
    def test_calendar_feed_endpoint_serves_inline_text_calendar(self):
        with TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "major.ics"
            feed_path.write_bytes(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")

            with patch("churchcal.api.views.ChurchCalendarFeedService.get_feed_path", return_value=feed_path):
                response = self.client.get("/api/v1/calendar/feed/major.ics")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/calendar"))
        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("acna-major.ics", response["Content-Disposition"])

    def test_calendar_feed_endpoint_accepts_apple_calendar_headers(self):
        with TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "major.ics"
            feed_path.write_bytes(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")

            with patch("churchcal.api.views.ChurchCalendarFeedService.get_feed_path", return_value=feed_path):
                response = self.client.get(
                    "/api/v1/calendar/feed/major.ics",
                    HTTP_ACCEPT="text/calendar",
                    HTTP_USER_AGENT="CalendarAgent/1000 CFNetwork/1496.0.7 Darwin/23.5.0",
                )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/calendar"))
        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("acna-major.ics", response["Content-Disposition"])

    def test_calendar_feed_endpoint_supports_download_and_cancel_routes(self):
        with TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "major-cancel.ics"
            feed_path.write_bytes(b"BEGIN:VCALENDAR\r\nMETHOD:CANCEL\r\nEND:VCALENDAR\r\n")

            with patch("churchcal.api.views.ChurchCalendarFeedService.get_feed_path", return_value=feed_path):
                response = self.client.get("/api/v1/calendar/feed/major/cancel.ics?download=1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("acna-major-cancel.ics", response["Content-Disposition"])


class OfficeReadingsResolverTests(TestCase):
    def test_unsaved_or_ferial_commemoration_falls_back_to_standard_office_day(self):
        StandardOfficeDay.objects.create(
            month=12,
            day=2,
            mp_psalms="1, 2",
            mp_reading_1="Isaiah 1",
            mp_reading_1_testament="OT",
            mp_reading_2="Matthew 1",
            mp_reading_2_testament="NT",
            ep_psalms="3, 4",
            ep_reading_1="Romans 1",
            ep_reading_1_testament="NT",
            ep_reading_2="Luke 1",
            ep_reading_2_testament="NT",
        )
        ThirtyDayPsalterDay.objects.create(day=2, mp_psalms="5", ep_psalms="6")

        resolver = OfficeReadingsResolver()
        fake_calendar_date = SimpleNamespace(
            primary=SimpleNamespace(pk=None),
            date=date(2026, 12, 2),
        )

        details = resolver.resolve(fake_calendar_date)

        self.assertEqual(details.mp_psalms_30_day, "5")
        self.assertEqual(details.mp_psalms_60_day, "1, 2")
        self.assertEqual(details.mp_reading_1, "Isaiah 1")

from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase, TestCase
from icalendar import Calendar

from churchcal.api.serializer import CommemorationSerializer
from churchcal.calendar_feeds import (
    ChurchCalendarFeedBuilder,
    FeedDay,
    OfficeDayDetails,
    OfficeReadingsResolver,
    get_feed_window_start_years,
)
from churchcal.ce_bce_replacement import replace_ce_bce_in_text
from churchcal.management.commands.import_mass_readings import Command as ImportMassReadingsCommand
from churchcal.migrations._holy_day_mass_readings_0017 import forward
from churchcal.models import Calendar as ChurchCalendar, CommemorationRank, MassReading, SanctoraleCommemoration
from churchcal.utils import advent
from office.models import Scripture, StandardOfficeDay, ThirtyDayPsalterDay


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


class CommemorationSaintNameTests(SimpleTestCase):
    def test_uses_saint_name_when_set(self):
        obj = SimpleNamespace(saint_name="Lancelot Andrewes", name="Lancelot Andrewes, Bishop")
        self.assertEqual(CommemorationSerializer().get_saint_name(obj), "Lancelot Andrewes")

    def test_falls_back_to_name_before_the_first_comma(self):
        for obj in (
            SimpleNamespace(saint_name="", name="Lancelot Andrewes, Bishop of Winchester"),
            SimpleNamespace(name="The Holy Name"),
        ):
            self.assertEqual(
                CommemorationSerializer().get_saint_name(obj),
                obj.name.split(",")[0],
            )


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


class HolyDayMassReadingsTests(TestCase):
    """Migration 0017 gives Conversion of Paul and the Nativity of John the Baptist their Eucharist readings."""

    def setUp(self):
        self.calendar = ChurchCalendar.objects.create(
            name="Book of Common Prayer 2019", year="2019", abbreviation="ACNA_BCP2019"
        )
        holy_day = CommemorationRank.objects.create(
            name="HOLY_DAY", formatted_name="Holy Day", precedence_rank=3, calendar=self.calendar
        )
        commemoration = CommemorationRank.objects.create(
            name="COMMEMORATION", formatted_name="Commemoration", precedence_rank=8, calendar=self.calendar
        )
        self.feasts = {}
        for name, month, day, rank, saint_type in (
            ("Conversion of Paul the Apostle", 1, 25, holy_day, None),
            ("The Nativity of John the Baptist", 6, 24, holy_day, None),
            ("Peter and Paul, Apostles", 6, 29, holy_day, None),
            ("The Beheading of John the Baptist", 8, 29, commemoration, "SAINT_1"),
        ):
            self.feasts[name] = SanctoraleCommemoration.objects.create(
                name=name, calendar=self.calendar, rank=rank, color="Red", month=month, day=day, saint_type=saint_type
            )

    def add_reading(self, abbreviation, feast, citation, reading_number, order):
        return MassReading.objects.create(
            calendar=self.calendar,
            commemoration=self.feasts[feast],
            abbreviation=abbreviation,
            long_citation=citation,
            long_text=f"<p>{citation}</p>",
            short_citation="",
            service="",
            years="ABC",
            reading_type="gospel",
            book="-",
            testament="NT",
            reading_number=reading_number,
            order=order,
        )

    def citations(self, name, year):
        return [r.long_citation for r in self.feasts[name].get_all_mass_readings_for_year(year)]

    def test_moves_misattached_readings_to_the_right_holy_days(self):
        acts = Scripture.objects.create(passage="Acts 26:9-21")
        for i, citation in enumerate(["Acts 26:9-21", "Psalms 67", "Galatians 1:11-24", "Matthew 10:16-25"]):
            self.add_reading("Paul", "Peter and Paul, Apostles", citation, i + 1, 873 + i)
        for i, citation in enumerate(["Ezekiel 34:11-16", "Psalms 87", "II Timothy 4:1-8", "John 21:15-19"]):
            self.add_reading("PeterPaul", "Peter and Paul, Apostles", citation, i + 1, 915 + i)
        for i, citation in enumerate(["Isaiah 40:1-11", "Psalms 85:7-13", "Acts 13:14-26", "Luke 1:57-80"]):
            self.add_reading("JohnTheBaptist", "The Beheading of John the Baptist", citation, i + 1, 911 + i)

        forward(apps, None)

        for year in "ABC":
            with self.subTest(year=year):
                self.assertEqual(
                    self.citations("Conversion of Paul the Apostle", year),
                    ["Acts 26:9-21", "Psalms 67", "Galatians 1:11-24", "Matthew 10:16-25"],
                )
                self.assertEqual(
                    self.citations("The Nativity of John the Baptist", year),
                    ["Isaiah 40:1-11", "Psalms 85:7-13", "Acts 13:14-26", "Luke 1:57-80"],
                )
                self.assertEqual(
                    self.citations("Peter and Paul, Apostles", year),
                    ["Ezekiel 34:11-16", "Psalms 87", "II Timothy 4:1-8", "John 21:15-19"],
                )
        self.assertFalse(MassReading.objects.filter(commemoration=self.feasts["The Beheading of John the Baptist"]))

        paul = MassReading.objects.filter(abbreviation="Paul")
        self.assertEqual(paul.get(long_citation="Acts 26:9-21").long_scripture, acts)
        self.assertEqual(paul.get(long_citation="Acts 26:9-21").long_text, "<p>Acts 26:9-21</p>")
        self.assertFalse(paul.filter(long_scripture__isnull=True))
        self.assertEqual(Scripture.objects.filter(passage="Acts 26:9-21").count(), 1)

    def test_creates_missing_readings_and_is_idempotent(self):
        Scripture.objects.create(passage="Luke 1:57-80", esv="<p>Zechariah's song</p>")

        forward(apps, None)
        forward(apps, None)

        for year in "ABC":
            with self.subTest(year=year):
                self.assertEqual(len(self.citations("Conversion of Paul the Apostle", year)), 4)
                self.assertEqual(len(self.citations("The Nativity of John the Baptist", year)), 4)

        readings = self.feasts["The Nativity of John the Baptist"].get_all_mass_readings_for_year("A")
        self.assertEqual(
            [(r.reading_number, r.reading_type, r.book, r.testament) for r in readings],
            [
                (1, "prophecy", "Isaiah", "OT"),
                (2, "psalm", "Psalms", "OT"),
                (3, "epistle", "Acts", "NT"),
                (4, "gospel", "Luke", "NT"),
            ],
        )
        self.assertEqual([r.long_scripture.passage for r in readings], [r.long_citation for r in readings])
        self.assertEqual(readings[3].long_text, "<p>Zechariah's song</p>")
        self.assertEqual(MassReading.objects.count(), 8)

    def test_importer_maps_sheet_codes_to_the_right_holy_days(self):
        command = ImportMassReadingsCommand()
        command.calendar = self.calendar
        self.assertEqual(command.get_commemoration("Paul"), self.feasts["Conversion of Paul the Apostle"])
        self.assertEqual(command.get_commemoration("JohnTheBaptist"), self.feasts["The Nativity of John the Baptist"])
        self.assertEqual(command.get_commemoration("PeterPaul"), self.feasts["Peter and Paul, Apostles"])

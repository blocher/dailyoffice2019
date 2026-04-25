from datetime import date, datetime, time
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from icalendar import Calendar

from patrons.calendar import build_ics_calendar
from patrons.dates import EASTERN_TIME, occurrence_date, parse_month_day
from patrons.models import (
    CalendarFeed,
    Event,
    FamilyMember,
    PatronalFeast,
    TextMessageSend,
    TextRecipient,
    TextSchedule,
)
from patrons.sms import format_patronal_feast_message, send_due_reminders
from patrons.views import feast_items


class PatronsModelTests(TestCase):
    def test_family_member_full_name_includes_optional_names(self):
        member = FamilyMember.objects.create(
            first_name="Benjamin",
            middle_name="James",
            confirmation_name="Joseph",
            last_name="Locher",
        )

        self.assertEqual(member.full_name, "Benjamin James Joseph Locher")

    def test_family_member_full_name_wraps_maiden_name(self):
        member = FamilyMember.objects.create(
            first_name="Mary",
            confirmation_name="Catherine",
            maiden_name="Smith",
            last_name="Jones",
        )

        self.assertEqual(member.full_name, "Mary Catherine (Smith) Jones")

    def test_patronal_feast_month_day_validation_allows_feb_29(self):
        member = FamilyMember.objects.create(first_name="Leap", last_name="Locher")
        feast = PatronalFeast(
            family_member=member,
            normalized_name="St. Leap",
            feast_name="St. Leap",
            general_month=2,
            general_day=29,
        )

        feast.full_clean()

    def test_patronal_feast_month_day_validation_rejects_invalid_dates(self):
        member = FamilyMember.objects.create(first_name="April", last_name="Locher")
        feast = PatronalFeast(
            family_member=member,
            normalized_name="St. April",
            feast_name="St. April",
            general_month=4,
            general_day=31,
        )

        with self.assertRaises(ValidationError):
            feast.full_clean()

    def test_occurrence_date_maps_feb_29_to_feb_28_in_non_leap_years(self):
        self.assertEqual(occurrence_date(2024, 2, 29), date(2024, 2, 29))
        self.assertEqual(occurrence_date(2025, 2, 29), date(2025, 2, 28))

    def test_parse_month_day_accepts_both_month_day_and_day_month(self):
        self.assertEqual(parse_month_day("Dec 24"), (12, 24))
        self.assertEqual(parse_month_day("24-Dec"), (12, 24))

    def test_feast_name_fallback_order(self):
        member = FamilyMember.objects.create(first_name="Mary", last_name="Locher")
        feast = PatronalFeast.objects.create(
            family_member=member,
            normalized_name="Blessed Virgin Mary",
            feast_name="Our Lady of Grace",
            traditional_calendar_name="Traditional Name",
            episcopal_calendar_name="Episcopal Name",
            general_month=5,
            general_day=31,
        )

        self.assertEqual(feast.display_feast_name, "Traditional Name")
        feast.general_calendar_name = "General Name"
        self.assertEqual(feast.display_feast_name, "General Name")

    def test_patronal_feast_view_items_are_unique_per_feast_per_day(self):
        member = FamilyMember.objects.create(first_name="James", last_name="Locher")
        PatronalFeast.objects.create(
            family_member=member,
            normalized_name="St. James",
            feast_name="Base Feast",
            general_calendar_name="General Feast",
            traditional_calendar_name="Traditional Feast",
            episcopal_calendar_name="Episcopal Feast",
            general_month=5,
            general_day=1,
            traditional_month=5,
            traditional_day=1,
            episcopal_month=5,
            episcopal_day=1,
        )

        items = list(feast_items(date(2026, 1, 1)))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "St. James: General Feast")
        self.assertEqual(items[0]["details"], "Catholic, Traditional Catholic, Episcopal")
        self.assertEqual(items[0]["calendar_values"], "general traditional episcopal")


class PatronImportTests(TestCase):
    def test_import_commands_load_expected_counts(self):
        call_command("import_patronal_feasts")
        self.assertEqual(FamilyMember.objects.count(), 7)
        self.assertEqual(PatronalFeast.objects.count(), 33)

        call_command("import_patron_events")
        self.assertEqual(FamilyMember.objects.count(), 7)
        self.assertEqual(Event.objects.count(), 20)


class PatronViewTests(TestCase):
    def test_index_requires_staff(self):
        response = self.client.get(reverse("patrons:index"))
        self.assertEqual(response.status_code, 302)

        user = User.objects.create_user(username="person", password="secret")
        self.client.force_login(user)
        response = self.client.get(reverse("patrons:index"))
        self.assertEqual(response.status_code, 302)

        staff = User.objects.create_user(username="staff", password="secret", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("patrons:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="view-tabs"')
        self.assertContains(response, 'id="view-tab-list"')
        self.assertContains(response, 'id="view-tab-calendar"')
        self.assertContains(response, 'id="list-view"')
        self.assertContains(response, 'id="calendar-view"')
        self.assertContains(response, 'id="person-filter"')
        self.assertContains(response, 'id="type-filter"')
        self.assertContains(response, 'id="calendar-filter"')
        self.assertContains(response, 'id="sort-filter"')

    def test_detail_views_require_staff_and_show_details(self):
        member = FamilyMember.objects.create(first_name="Mary", last_name="Locher")
        feast = PatronalFeast.objects.create(
            family_member=member,
            normalized_name="Blessed Virgin Mary",
            feast_name="The Visitation of the Blessed Virgin Mary",
            general_calendar_name="The Visitation of the Blessed Virgin Mary",
            traditional_calendar_name="The Visitation of the Blessed Virgin Mary",
            episcopal_calendar_name="The Visitation of the Blessed Virgin Mary",
            general_month=5,
            general_day=31,
            traditional_month=7,
            traditional_day=2,
            episcopal_month=5,
            episcopal_day=31,
        )
        event = Event.objects.create(
            family_member=member,
            event_type=Event.BIRTHDAY,
            date=date(2015, 5, 9),
            details="Born at home.",
        )

        response = self.client.get(feast.get_absolute_url())
        self.assertEqual(response.status_code, 302)

        staff = User.objects.create_user(username="staff-detail", password="secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(feast.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catholic/General")
        self.assertContains(response, "Catholic/Traditional")
        self.assertContains(response, "May 31")
        self.assertContains(response, "Jul 2")

        response = self.client.get(event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Birthday")
        self.assertContains(response, "Born at home.")

        response = self.client.get(reverse("patrons:index"))
        self.assertContains(response, feast.get_absolute_url())
        self.assertContains(response, event.get_absolute_url())

    def test_calendar_feed_requires_current_enabled_token(self):
        feed = CalendarFeed.objects.create(name="Private Feed")

        response = self.client.get(reverse("patrons:calendar_feed", args=[feed.token]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/calendar"))

        old_token = feed.token
        feed.rotate_token()
        self.assertNotEqual(old_token, feed.token)
        self.assertFalse(CalendarFeed.objects.filter(token=old_token).exists())
        response = self.client.get(reverse("patrons:calendar_feed", args=[old_token]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get("/patrons/calendar/not-a-token.ics")
        self.assertEqual(response.status_code, 404)

    def test_ics_contains_titles_descriptions_and_feb_29_fallback(self):
        member = FamilyMember.objects.create(first_name="Leap", last_name="Locher")
        PatronalFeast.objects.create(
            family_member=member,
            normalized_name="St. Leap",
            feast_name="Leap Feast",
            general_calendar_name="General Leap Feast",
            general_month=2,
            general_day=29,
            traditional_month=2,
            traditional_day=29,
        )
        Event.objects.create(family_member=member, event_type=Event.BIRTHDAY, date=date(2024, 2, 29))

        parsed = Calendar.from_ical(build_ics_calendar(date(2025, 1, 1)))
        events = [component for component in parsed.walk() if component.name == "VEVENT"]
        summaries = [str(component.get("summary")) for component in events]
        descriptions = [str(component.get("description", "")) for component in events]
        starts = [component.decoded("dtstart") for component in events]

        self.assertIn("Leap: St. Leap: General Leap Feast", summaries)
        self.assertTrue(any("Catholic, Traditional Catholic" in description for description in descriptions))
        self.assertIn(date(2025, 2, 28), starts)


class PatronSmsTests(TestCase):
    def setUp(self):
        self.member = FamilyMember.objects.create(first_name="Mary", last_name="Locher")
        self.recipient = TextRecipient.objects.create(family_member=self.member, telephone_number="+15551234567")
        self.schedule = TextSchedule.objects.get(time=time(17, 0), relative_days=-1)

    def test_patronal_feast_message_uses_relative_phrase_and_labels(self):
        feast = PatronalFeast.objects.create(
            family_member=self.member,
            normalized_name="St. Mary Magdalene",
            feast_name="St. Mary Magdalene",
            general_calendar_name="St. Mary Magdalene",
            general_month=7,
            general_day=22,
        )

        message = format_patronal_feast_message(feast, date(2026, 7, 22), date(2026, 7, 21))

        self.assertEqual(
            message,
            "Mary is celebrating a patronal feast Tomorrow for St. Mary Magdalene: St. Mary Magdalene. Catholic",
        )

    @override_settings(
        PATRONS_SMS_ENABLED=True,
        TWILIO_ACCOUNT_SID="AC123",
        TWILIO_AUTH_TOKEN="secret",
        TWILIO_FROM_NUMBER="+15557654321",
    )
    def test_send_due_reminders_sends_once_and_tracks_success(self):
        Event.objects.create(family_member=self.member, event_type=Event.BAPTISM, date=date(2026, 4, 21))
        now = datetime(2026, 4, 20, 17, 0, tzinfo=EASTERN_TIME)
        twilio_message = Mock(sid="SM123")

        with patch("patrons.sms.Client") as client:
            client.return_value.messages.create.return_value = twilio_message
            self.assertEqual(send_due_reminders(now=now), 1)
            self.assertEqual(send_due_reminders(now=now), 0)

        send = TextMessageSend.objects.get()
        self.assertTrue(send.success)
        self.assertEqual(send.provider_message_id, "SM123")
        self.assertIn("Mary has a Baptism Day anniversary Tomorrow.", send.message)

    @override_settings(
        PATRONS_SMS_ENABLED=True,
        TWILIO_ACCOUNT_SID="AC123",
        TWILIO_AUTH_TOKEN="secret",
        TWILIO_FROM_NUMBER="+15557654321",
    )
    def test_send_due_reminders_tracks_twilio_failure(self):
        Event.objects.create(family_member=self.member, event_type=Event.BAPTISM, date=date(2026, 4, 21))
        now = datetime(2026, 4, 20, 17, 0, tzinfo=EASTERN_TIME)

        with patch("patrons.sms.Client") as client:
            client.return_value.messages.create.side_effect = Exception("Twilio said no")
            self.assertEqual(send_due_reminders(now=now), 1)

        send = TextMessageSend.objects.get()
        self.assertFalse(send.success)
        self.assertEqual(send.error_message, "Twilio said no")

    @override_settings(PATRONS_SMS_ENABLED=True)
    def test_send_due_reminders_uses_feb_29_fallback(self):
        PatronalFeast.objects.create(
            family_member=self.member,
            normalized_name="St. Leap",
            feast_name="Leap Feast",
            general_month=2,
            general_day=29,
        )
        now = datetime(2025, 2, 27, 17, 0, tzinfo=EASTERN_TIME)

        self.assertEqual(send_due_reminders(now=now, dry_run=True), 1)

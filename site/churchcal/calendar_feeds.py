from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.utils import timezone
from icalendar import Calendar, Event

from churchcal.calculations import ChurchYear
from churchcal.models import MassReading
from churchcal.utils import advent
from office.models import HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay

VALID_CALENDAR_FEED_SCOPES = ("major", "major_minor", "every")

PUBLIC_SITE_BASE_URL = "https://www.dailyoffice2019.com"
CALENDAR_FEED_DIRECTORY_NAME = "calendar_feeds"
CALENDAR_FEED_MANIFEST_NAME = "manifest.json"

CALENDAR_FEED_LABELS = {
    "major": "Major Feasts",
    "major_minor": "Major Feasts + Commemorations",
    "every": "Every Day",
}


def get_current_church_year_start(today: date) -> int:
    return today.year if today >= advent(today.year) else today.year - 1


def get_feed_window_start_years(today: date) -> list[int]:
    current_start_year = get_current_church_year_start(today)
    return list(range(current_start_year - 1, current_start_year + 3))


def get_feed_scope_label(scope: str) -> str:
    if scope not in VALID_CALENDAR_FEED_SCOPES:
        raise ValueError(f"Invalid calendar feed scope: {scope}")
    return CALENDAR_FEED_LABELS[scope]


def get_calendar_feed_directory() -> Path:
    return Path(settings.MEDIA_ROOT) / CALENDAR_FEED_DIRECTORY_NAME


def get_calendar_feed_manifest_path() -> Path:
    return get_calendar_feed_directory() / CALENDAR_FEED_MANIFEST_NAME


def get_calendar_feed_filename(scope: str, canceled: bool = False) -> str:
    suffix = "-cancel" if canceled else ""
    return f"acna-{scope}{suffix}.ics"


def get_calendar_feed_path(scope: str, canceled: bool = False) -> Path:
    return get_calendar_feed_directory() / get_calendar_feed_filename(scope, canceled=canceled)


@dataclass(frozen=True)
class OfficeDayDetails:
    mp_psalms_30_day: str
    mp_psalms_60_day: str
    mp_reading_1: str
    mp_reading_2: str
    ep_psalms_30_day: str
    ep_psalms_60_day: str
    ep_reading_1: str
    ep_reading_2: str


@dataclass(frozen=True)
class FeedDay:
    event_date: date
    major_feast_name: str | None
    major_or_minor_feast_name: str | None
    primary_name: str
    commemorations: tuple[str, ...]
    fast_day: bool
    feast_day: bool
    office_details: OfficeDayDetails
    mass_reading_citations: tuple[str, ...]

    def summary_for_scope(self, scope: str) -> str:
        if scope == "major":
            return self.major_feast_name or self.primary_name
        if scope == "major_minor":
            return self.major_or_minor_feast_name or self.primary_name
        return self.major_or_minor_feast_name or self.primary_name

    def should_include_for_scope(self, scope: str) -> bool:
        if scope == "major":
            return bool(self.major_feast_name)
        if scope == "major_minor":
            return bool(self.major_or_minor_feast_name)
        if scope == "every":
            return True
        raise ValueError(f"Invalid calendar feed scope: {scope}")

    @property
    def event_uid_date(self) -> str:
        return self.event_date.isoformat()

    @property
    def day_page_url(self) -> str:
        return f"{PUBLIC_SITE_BASE_URL}/day/" f"{self.event_date.year}/{self.event_date.month}/{self.event_date.day}/"

    @property
    def morning_prayer_url(self) -> str:
        return (
            f"{PUBLIC_SITE_BASE_URL}/morning_prayer/"
            f"{self.event_date.year}/{self.event_date.month}/{self.event_date.day}"
        )

    @property
    def readings_url(self) -> str:
        return (
            f"{PUBLIC_SITE_BASE_URL}/readings/" f"{self.event_date.year}/{self.event_date.month}/{self.event_date.day}"
        )

    def description_lines(self) -> list[str]:
        lines = list(self.commemorations)

        if self.fast_day:
            lines.extend(["", "FAST DAY"])

        if self.feast_day:
            lines.extend(["", "SUNDAY OR MAJOR HOLY DAY"])

        lines.extend(
            [
                "",
                "MORNING PRAYER",
                f"Psalms {self.office_details.mp_psalms_30_day} (30 day cycle)",
                f"Psalms {self.office_details.mp_psalms_60_day} (60 day cycle)",
                self.office_details.mp_reading_1,
                self.office_details.mp_reading_2,
                "",
                "EVENING PRAYER",
                f"Psalms {self.office_details.ep_psalms_30_day} (30 day cycle)",
                f"Psalms {self.office_details.ep_psalms_60_day} (60 day cycle)",
                self.office_details.ep_reading_1,
                self.office_details.ep_reading_2,
            ]
        )

        if self.mass_reading_citations:
            lines.extend(["", "EUCHARIST"])
            lines.extend(self.mass_reading_citations)

        lines.extend(
            [
                "",
                f"Day Page: {self.day_page_url}",
                f"Morning Prayer: {self.morning_prayer_url}",
                f"Readings: {self.readings_url}",
            ]
        )
        return lines


class OfficeReadingsResolver:
    def __init__(self):
        self.standard_days = {
            (office_day.month, office_day.day): office_day for office_day in StandardOfficeDay.objects.all()
        }
        self.holy_days = {
            office_day.commemoration_id: office_day
            for office_day in HolyDayOfficeDay.objects.select_related("commemoration").all()
        }
        self.psalter_days = {psalter_day.day: psalter_day for psalter_day in ThirtyDayPsalterDay.objects.all()}

    def resolve(self, calendar_date) -> OfficeDayDetails:
        office_day = self._resolve_office_day(calendar_date)
        psalter_day = self.psalter_days[calendar_date.date.day]
        return OfficeDayDetails(
            mp_psalms_30_day=psalter_day.mp_psalms,
            mp_psalms_60_day=office_day.mp_psalms,
            mp_reading_1=office_day.mp_reading_1,
            mp_reading_2=office_day.mp_reading_2,
            ep_psalms_30_day=psalter_day.ep_psalms,
            ep_psalms_60_day=office_day.ep_psalms,
            ep_reading_1=office_day.ep_reading_1,
            ep_reading_2=office_day.ep_reading_2,
        )

    def _resolve_office_day(self, calendar_date):
        commemoration = calendar_date.primary
        commemoration_id = getattr(commemoration, "original_pk", None) or getattr(commemoration, "pk", None)
        if commemoration_id and commemoration_id in self.holy_days:
            return self.holy_days[commemoration_id]

        return self.standard_days[(calendar_date.date.month, calendar_date.date.day)]


class MassReadingsResolver:
    def __init__(self):
        self.cache: dict[tuple, tuple[str, ...]] = {}

    def resolve(self, calendar_date) -> tuple[str, ...]:
        if calendar_date.primary.rank.precedence_rank > 4:
            return ()

        key = self._cache_key(calendar_date)
        if key in self.cache:
            return self.cache[key]

        citations = tuple(
            reading.long_citation
            for reading in self._get_queryset(
                calendar_date.primary, calendar_date.proper, calendar_date.year.mass_year
            )
            if reading.long_citation
        )
        self.cache[key] = citations
        return citations

    def _cache_key(self, calendar_date) -> tuple:
        commemoration = self._resolve_original_commemoration(calendar_date.primary)
        proper = self._resolve_original_proper(calendar_date.primary, calendar_date.proper)
        return (
            getattr(commemoration, "pk", None) or getattr(commemoration, "original_pk", None),
            getattr(proper, "pk", None),
            calendar_date.year.mass_year,
            calendar_date.primary.name,
        )

    def _resolve_original_commemoration(self, commemoration):
        if hasattr(commemoration, "original_commemoration") and commemoration.original_commemoration:
            return commemoration.original_commemoration
        return commemoration

    def _resolve_original_proper(self, commemoration, proper):
        if hasattr(commemoration, "original_proper") and commemoration.original_proper:
            return commemoration.original_proper
        if hasattr(commemoration, "proper") and commemoration.proper:
            return commemoration.proper
        return proper

    def _get_queryset(self, commemoration, proper, year, time="morning"):
        original_commemoration = self._resolve_original_commemoration(commemoration)
        original_proper = self._resolve_original_proper(commemoration, proper)

        if original_proper and commemoration.rank.name == "SUNDAY":
            query = MassReading.objects.filter(years__contains=year, proper=original_proper)
        else:
            commemoration_id = getattr(original_commemoration, "original_pk", None) or getattr(
                original_commemoration, "pk", None
            )
            query = MassReading.objects.filter(years__contains=year, commemoration_id=commemoration_id)

        if year in ["A", "C"] and time == "morning":
            query = query.order_by("reading_number", "-order")
        else:
            query = query.order_by("reading_number", "order")

        if commemoration.name == "Eve of Easter Day":
            query = query.filter(abbreviation="EasterEve")

        if commemoration.name == "Easter Day":
            if time == "morning":
                query = query.filter(service="Principal Service")
            else:
                query = query.filter(service="Evening Service")

        if commemoration.name == "Eve of The Nativity of our Lord Jesus Christ: Christmas Day":
            query = query.filter(service="I")

        if commemoration.name == "The Nativity of Our Lord Jesus Christ: Christmas Day":
            if time == "morning":
                query = query.filter(service="II")
            else:
                query = query.filter(service="III")

        if commemoration.name in ["Eve of Palm Sunday", "Palm Sunday"]:
            query = query.filter(service="Liturgy of the Word")

        readings = list(query.all())
        if readings:
            return readings

        saint_type = getattr(original_commemoration, "saint_type", None)
        if saint_type:
            return list(
                MassReading.objects.filter(common__abbreviation=saint_type).order_by("reading_number", "order")
            )

        return readings


class ChurchCalendarFeedBuilder:
    def __init__(self):
        self.office_resolver = OfficeReadingsResolver()
        self.mass_resolver = MassReadingsResolver()
        self.generated_at = timezone.now()

    def build_feed_days(self, today: date | None = None) -> list[FeedDay]:
        today = today or timezone.localdate()
        years = get_feed_window_start_years(today)
        feed_days: list[FeedDay] = []
        for year_start in years:
            church_year = ChurchYear(year_start)
            for calendar_date in church_year:
                feed_days.append(self._build_feed_day(calendar_date))
        return sorted(feed_days, key=lambda feed_day: feed_day.event_date)

    def build_all(self, today: date | None = None) -> dict[tuple[str, bool], bytes]:
        feed_days = self.build_feed_days(today=today)
        calendars: dict[tuple[str, bool], bytes] = {}
        for scope in VALID_CALENDAR_FEED_SCOPES:
            calendars[(scope, False)] = self.serialize(scope, feed_days, canceled=False)
            calendars[(scope, True)] = self.serialize(scope, feed_days, canceled=True)
        return calendars

    def serialize(self, scope: str, feed_days: Iterable[FeedDay], canceled: bool = False) -> bytes:
        label = get_feed_scope_label(scope)
        calendar = Calendar()
        calendar.add("prodid", "-//Daily Office 2019//ACNA Calendar//dailyoffice2019.com//")
        calendar.add("version", "2.0")
        calendar.add("calscale", "GREGORIAN")
        calendar.add("x-wr-calname", f"Daily Office 2019: {label}{' (Undo)' if canceled else ''}")
        calendar.add(
            "x-wr-caldesc",
            f"Daily Office 2019 ACNA calendar feed for {label.lower()}"
            f"{' with cancellation events for undoing imported items.' if canceled else '.'}",
        )
        calendar.add("x-published-ttl", "PT12H")
        calendar.add("method", "CANCEL" if canceled else "PUBLISH")

        for feed_day in feed_days:
            if not feed_day.should_include_for_scope(scope):
                continue

            event = Event()
            event.add("uid", f"acna-{scope}-{feed_day.event_uid_date}@dailyoffice2019.com")
            event.add("summary", feed_day.summary_for_scope(scope))
            event.add("dtstart", feed_day.event_date)
            event.add("dtend", feed_day.event_date + timedelta(days=1))
            event.add("dtstamp", self.generated_at)
            event.add("sequence", 1 if canceled else 0)
            event.add("url", feed_day.day_page_url)

            if canceled:
                event.add("status", "CANCELLED")
                event.add(
                    "description",
                    (
                        "Cancellation event for removing a previously imported Daily Office calendar item. "
                        "Subscription is still the safer option for ongoing updates."
                    ),
                )
            else:
                event.add("description", "\n".join(feed_day.description_lines()))

            calendar.add_component(event)

        return calendar.to_ical()

    def _build_feed_day(self, calendar_date) -> FeedDay:
        major_feast_name = calendar_date.required[0].name if calendar_date.required else None
        major_or_minor_feast_name = None
        for feast in calendar_date.all:
            if "FERIA" not in feast.rank.name:
                major_or_minor_feast_name = feast.name
                break

        return FeedDay(
            event_date=calendar_date.date,
            major_feast_name=major_feast_name,
            major_or_minor_feast_name=major_or_minor_feast_name,
            primary_name=calendar_date.primary.name,
            commemorations=tuple(feast.name for feast in calendar_date.all),
            fast_day=calendar_date.fast_day != calendar_date.FAST_NONE,
            feast_day=calendar_date.primary.rank.precedence_rank <= 4,
            office_details=self.office_resolver.resolve(calendar_date),
            mass_reading_citations=self.mass_resolver.resolve(calendar_date),
        )


class ChurchCalendarFeedService:
    @classmethod
    def ensure_current(cls, today: date | None = None, force: bool = False) -> dict[str, object]:
        today = today or timezone.localdate()
        manifest = cls._read_manifest()
        if force or cls._manifest_is_stale(manifest, today):
            cls._regenerate(today)
            manifest = cls._read_manifest()
        return manifest

    @classmethod
    def get_feed_path(cls, scope: str, canceled: bool = False, today: date | None = None) -> Path:
        get_feed_scope_label(scope)
        cls.ensure_current(today=today)
        return get_calendar_feed_path(scope, canceled=canceled)

    @classmethod
    def _regenerate(cls, today: date) -> None:
        builder = ChurchCalendarFeedBuilder()
        calendars = builder.build_all(today=today)

        directory = get_calendar_feed_directory()
        directory.mkdir(parents=True, exist_ok=True)

        for (scope, canceled), content in calendars.items():
            cls._write_atomic(get_calendar_feed_path(scope, canceled=canceled), content)

        manifest = {
            "build_date": today.isoformat(),
            "window_start_years": get_feed_window_start_years(today),
            "generated_at": timezone.now().isoformat(),
            "files": {
                get_calendar_feed_filename(scope, canceled=canceled): {
                    "scope": scope,
                    "canceled": canceled,
                    "size": len(content),
                }
                for (scope, canceled), content in calendars.items()
            },
        }
        cls._write_atomic(get_calendar_feed_manifest_path(), json.dumps(manifest, indent=2).encode("utf-8"))

    @classmethod
    def _manifest_is_stale(cls, manifest: dict[str, object] | None, today: date) -> bool:
        if not manifest or manifest.get("build_date") != today.isoformat():
            return True

        for scope in VALID_CALENDAR_FEED_SCOPES:
            if not get_calendar_feed_path(scope).exists():
                return True
            if not get_calendar_feed_path(scope, canceled=True).exists():
                return True
        return False

    @classmethod
    def _read_manifest(cls) -> dict[str, object] | None:
        manifest_path = get_calendar_feed_manifest_path()
        if not manifest_path.exists():
            return None

        try:
            return json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            return None

    @classmethod
    def _write_atomic(cls, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary_file:
            temporary_file.write(content)
            temp_name = temporary_file.name

        os.replace(temp_name, path)

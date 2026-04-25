from dataclasses import dataclass
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from icalendar import Calendar, Event as ICalEvent

from patrons.dates import years_for_window
from patrons.models import Event, PatronalFeast


@dataclass(frozen=True)
class CalendarOccurrence:
    kind: str
    occurrence_date: object
    title: str
    description: str
    uid: str


def calendar_window(today):
    return today - relativedelta(months=12), today + relativedelta(months=36)


def event_occurrences(start, end):
    events = Event.objects.select_related("family_member").all()
    for event in events:
        for year in years_for_window(start, end):
            occurrence = event.occurrence_for_year(year)
            if start <= occurrence <= end:
                yield CalendarOccurrence(
                    kind="event",
                    occurrence_date=occurrence,
                    title="{}: {}".format(event.family_member.first_name, event.get_event_type_display()),
                    description=event.details,
                    uid="patrons-event-{}-{}@dailyoffice2019.com".format(event.pk, occurrence.isoformat()),
                )


def patronal_feast_occurrences(start, end):
    feasts = PatronalFeast.objects.select_related("family_member").all()
    for feast in feasts:
        for year in years_for_window(start, end):
            for occurrence in feast.occurrence_dates_for_year(year):
                if start <= occurrence <= end:
                    labels = feast.calendar_labels_for_date(occurrence)
                    description = "Calendars: {}".format(", ".join(labels)) if labels else ""
                    yield CalendarOccurrence(
                        kind="feast",
                        occurrence_date=occurrence,
                        title="{}: {}: {}".format(
                            feast.family_member.first_name,
                            feast.normalized_name,
                            feast.display_feast_name,
                        ),
                        description=description,
                        uid="patrons-feast-{}-{}@dailyoffice2019.com".format(feast.pk, occurrence.isoformat()),
                    )


def all_occurrences(today):
    start, end = calendar_window(today)
    occurrences = [*event_occurrences(start, end), *patronal_feast_occurrences(start, end)]
    return sorted(occurrences, key=lambda occurrence: (occurrence.occurrence_date, occurrence.title))


def build_ics_calendar(today):
    cal = Calendar()
    cal.add("prodid", "-//Daily Office Patrons//dailyoffice2019.com//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Patrons")

    for occurrence in all_occurrences(today):
        event = ICalEvent()
        event.add("summary", occurrence.title)
        event.add("dtstart", occurrence.occurrence_date)
        event.add("dtend", occurrence.occurrence_date + timedelta(days=1))
        event.add("uid", occurrence.uid)
        if occurrence.description:
            event.add("description", occurrence.description)
        cal.add_component(event)

    return cal.to_ical()

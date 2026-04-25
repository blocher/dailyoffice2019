from datetime import date as date_class, timedelta

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from patrons.calendar import build_ics_calendar
from patrons.dates import (
    display_month_day,
    jan_first_sort_key,
    month_day_matches,
    next_occurrence,
    occurrence_date,
)
from patrons.models import CalendarFeed, Event, FamilyMember, PatronalFeast


CALENDAR_FILTERS = (
    ("general", "Catholic/General"),
    ("traditional", "Catholic/Traditional"),
    ("episcopal", "Episcopal"),
)

# Short labels for message API (pipe-delimited) lines.
SHORT_CALENDAR = (
    ("general", "Catholic"),
    ("traditional", "Traditional"),
    ("episcopal", "Episcopal"),
)


EVENT_SUBTYPE_LABELS = {
    Event.BIRTHDAY: "Birthday",
    Event.BAPTISM: "Baptism",
    Event.WEDDING: "Marriage",
    Event.CONFIRMATION: "Confirmation",
    Event.FIRST_CONFESSION: "Confession",
    Event.FIRST_COMMUNION: "Communion",
    Event.DIACONAL_ORDINATION: "Diaconal Ordination",
    Event.PRIESTLY_ORDINATION: "Priestly Ordination",
    Event.DEATH: "Death",
}


def _person_display_name(member):
    if (member.first_name or "").strip():
        return member.first_name.strip()
    full = (member.full_name or "").strip()
    if full:
        return full.split()[0]
    return ""


def _feast_entry_lines(feast):
    primary = (
        (feast.normalized_name or "").strip()
        or (feast.display_feast_name or "").strip()
        or (feast.feast_name or "").strip()
    )
    display = (feast.display_feast_name or "").strip() or (feast.feast_name or "").strip()
    if primary and display and display != primary:
        return primary, display
    return primary, ""


def _feast_title_for_message(feast, value):
    for prefix, _short in SHORT_CALENDAR:
        month = getattr(feast, "{}_month".format(prefix))
        day = getattr(feast, "{}_day".format(prefix))
        calendar_name = (getattr(feast, "{}_calendar_name".format(prefix)) or "").strip()
        if calendar_name and month and day and month_day_matches(value, month, day):
            return calendar_name
    if (feast.feast_name or "").strip():
        return feast.feast_name.strip()
    return (feast.display_feast_name or "").strip()


def _format_month_day_long(occ):
    return "{} {}".format(occ.strftime("%B"), occ.day)


def _feast_calendar_for_day(feast, value):
    matching = []
    mismatch_notes = []
    for prefix, short in SHORT_CALENDAR:
        month = getattr(feast, "{}_month".format(prefix))
        day = getattr(feast, "{}_day".format(prefix))
        if not month or not day:
            continue
        if month_day_matches(value, month, day):
            matching.append(short)
        else:
            occ = occurrence_date(value.year, month, day)
            mismatch_notes.append("{} on {}".format(short, _format_month_day_long(occ)))
    main = ", ".join(matching)
    if mismatch_notes:
        if main:
            return "{} ({})".format(main, "; ".join(mismatch_notes))
        return "({})".format("; ".join(mismatch_notes))
    return main


def _ordinal(value):
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return "{}{}".format(value, suffix)


def _query_grace_includes_all(request):
    raw = request.GET.get("grace")
    if raw is None:
        return False
    s = raw.strip().lower()
    if s in ("", "0", "false", "no", "off", "f", "n"):
        return False
    return True


def _member_excluded_by_grace_param(member, request):
    if _query_grace_includes_all(request):
        return False
    return (member.first_name or "").strip().casefold() == "grace"


def _when_phrase(message_day, window_start, local_today):
    if window_start == local_today:
        if message_day == window_start:
            return "TODAY"
        if message_day == window_start + timedelta(days=1):
            return "TOMORROW"
    return message_day.isoformat()


def _life_event_message_label(event):
    label = event.get_event_type_display()
    if label.endswith(" Day"):
        return label
    return "{} Day".format(label)


def _feast_entries_for_day(value, when_text, day_order, request):
    entries = []
    for feast in PatronalFeast.objects.select_related("family_member").all():
        if not feast.matches_date(value):
            continue
        if _member_excluded_by_grace_param(feast.family_member, request):
            continue
        feast_title = _feast_title_for_message(feast, value)
        line = "{} | {} | {} | {}".format(
            _person_display_name(feast.family_member),
            when_text,
            feast_title,
            _feast_calendar_for_day(feast, value),
        )
        entries.append(
            {
                "person": feast.family_member.full_name,
                "day_order": day_order,
                "kind_sort": 0,
                "detail_sort": (
                    (feast.normalized_name or "").casefold(),
                    (feast_title or "").casefold(),
                ),
                "message": line,
            }
        )
    return entries


def _event_entries_for_day(value, when_text, day_order, request):
    entries = []
    for event in Event.objects.select_related("family_member").all():
        if not event.matches_date(value):
            continue
        if _member_excluded_by_grace_param(event.family_member, request):
            continue
        anniversary = value.year - event.date.year
        life_event_label = _life_event_message_label(event)
        entries.append(
            {
                "person": event.family_member.full_name,
                "day_order": day_order,
                "kind_sort": 1,
                "detail_sort": (life_event_label.casefold(), event.date.year),
                "message": "{} | {} | {} | {} anniversary ({})".format(
                    _person_display_name(event.family_member),
                    when_text,
                    life_event_label,
                    _ordinal(anniversary),
                    event.date.year,
                ),
            }
        )
    return entries


def _message_response_window(request, window_start):
    d0 = window_start
    d1 = window_start + timedelta(days=1)
    local_today = timezone.localdate()
    all_entries = []
    for day_order, message_day in enumerate((d0, d1)):
        when_text = _when_phrase(message_day, window_start, local_today)
        all_entries.extend(_feast_entries_for_day(message_day, when_text, day_order, request))
        all_entries.extend(_event_entries_for_day(message_day, when_text, day_order, request))

    all_entries.sort(key=lambda e: (e["day_order"], e["person"].casefold(), e["kind_sort"], e["detail_sort"]))
    body = "\n".join(entry["message"] for entry in all_entries)
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def message_today(request):
    today = timezone.localdate()
    return _message_response_window(request, today)


def message_tomorrow(request):
    return _message_response_window(request, timezone.localdate() + timedelta(days=1))


def message_date(request, year, month, day):
    try:
        window_start = date_class(year, month, day)
    except ValueError:
        return HttpResponse("Invalid date.", status=404, content_type="text/plain; charset=utf-8")
    return _message_response_window(request, window_start)


def calendar_feed(request, token):
    try:
        CalendarFeed.objects.get(token=token, enabled=True)
    except (CalendarFeed.DoesNotExist, ValidationError, ValueError):
        return HttpResponse("Calendar feed not found.", status=404)

    content = build_ics_calendar(timezone.localdate())
    return HttpResponse(content, content_type="text/calendar; charset=utf-8")


def index(request):
    today = timezone.localdate()
    items = list(feast_items(today)) + list(event_items(today))
    items.sort(key=lambda item: (item["sort_from_today"], item["person"], item["title"]))

    return render(
        request,
        "patrons/index.html",
        {
            "items": items,
            "family_members": FamilyMember.objects.all(),
            "event_types": Event.EVENT_TYPE_CHOICES,
            "calendar_filters": CALENDAR_FILTERS,
            "calendar_feed": CalendarFeed.objects.filter(enabled=True).first(),
            "today": today,
        },
    )


def feast_detail(request, pk):
    feast = get_object_or_404(PatronalFeast.objects.select_related("family_member"), pk=pk)
    return render(
        request,
        "patrons/feast_detail.html",
        {
            "feast": feast,
            "calendar_rows": feast_calendar_rows(feast),
        },
    )


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.select_related("family_member"), pk=pk)
    return render(request, "patrons/event_detail.html", {"event": event})


def feast_items(today):
    for feast in PatronalFeast.objects.select_related("family_member").all():
        occurrence_groups = {}
        for prefix, label, month, day in feast.iter_month_days():
            occurrence = occurrence_date(today.year, month, day)
            occurrence_groups.setdefault(occurrence, []).append((prefix, label, month, day))

        for feast_date, labels_and_dates in occurrence_groups.items():
            month = feast_date.month
            day = feast_date.day
            upcoming = min(next_occurrence(today, item[2], item[3]) for item in labels_and_dates)
            labels = [item[1] for item in labels_and_dates]
            badge_map = {
                "general": ("C", "Catholic"),
                "traditional": ("T", "Traditional Catholic"),
                "episcopal": ("E", "Episcopal"),
            }
            calendar_badges = []
            for prefix, code_and_label in badge_map.items():
                if any(item_prefix == prefix for item_prefix, _label, _month, _day in labels_and_dates):
                    code, label = code_and_label
                    calendar_badges.append({"code": code, "label": label})
            entry_primary, entry_secondary = _feast_entry_lines(feast)
            yield {
                "kind": "feast",
                "kind_label": "Patron",
                "person": feast.family_member.full_name,
                "person_display": _person_display_name(feast.family_member),
                "person_id": feast.family_member_id,
                "saint_name": feast.normalized_name,
                "month": labels_and_dates[0][2],
                "day": labels_and_dates[0][3],
                "calendar_values": " ".join([item[0] for item in labels_and_dates]),
                "event_type": "",
                "event_type_label": "",
                "title": "{}: {}".format(feast.normalized_name, feast.display_feast_name),
                "entry_primary": entry_primary,
                "entry_secondary": entry_secondary,
                "detail_url": feast.get_absolute_url(),
                "date_label": display_month_day(month, day),
                "details": ", ".join(labels),
                "calendar_badges": calendar_badges,
                "event_year": "",
                "sort_from_today": (upcoming - today).days,
                "sort_jan_first": jan_first_sort_key(today.year, month, day),
            }


def event_items(today):
    for event in Event.objects.select_related("family_member").all():
        occurrence_date = event.occurrence_for_year(today.year)
        upcoming = next_occurrence(today, event.date.month, event.date.day)
        yield {
            "kind": "event",
            "kind_label": EVENT_SUBTYPE_LABELS.get(
                event.event_type, event.get_event_type_display().replace(" Day", "")
            ),
            "person": event.family_member.full_name,
            "person_display": _person_display_name(event.family_member),
            "person_id": event.family_member_id,
            "saint_name": "",
            "month": event.date.month,
            "day": event.date.day,
            "calendar_values": "",
            "event_type": event.event_type,
            "event_type_label": event.get_event_type_display(),
            "title": event.get_event_type_display(),
            "entry_primary": event.get_event_type_display(),
            "entry_secondary": "",
            "detail_url": event.get_absolute_url(),
            "date_label": display_month_day(event.date.month, event.date.day),
            "details": event.details
            or "Original date: {} {}, {}".format(
                event.date.strftime("%b"),
                event.date.day,
                event.date.year,
            ),
            "calendar_badges": [],
            "event_year": str(event.date.year),
            "sort_from_today": (upcoming - today).days,
            "sort_jan_first": jan_first_sort_key(today.year, event.date.month, event.date.day),
        }


def feast_calendar_rows(feast):
    return [
        {
            "calendar": "Catholic/General",
            "name": feast.general_calendar_name or "",
            "date": display_month_day(feast.general_month, feast.general_day),
        },
        {
            "calendar": "Catholic/Traditional",
            "name": feast.traditional_calendar_name or "",
            "date": display_month_day(feast.traditional_month, feast.traditional_day),
        },
        {
            "calendar": "Episcopal",
            "name": feast.episcopal_calendar_name or "",
            "date": display_month_day(feast.episcopal_month, feast.episcopal_day),
        },
    ]

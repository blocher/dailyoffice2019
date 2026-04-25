import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


EASTERN_TIME = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class MonthDay:
    month: int
    day: int

    @property
    def display(self):
        return "{} {}".format(calendar.month_abbr[self.month], self.day)


def is_leap_year(year):
    return calendar.isleap(year)


def validate_month_day(month, day):
    if month is None and day is None:
        return
    if month is None or day is None:
        raise ValueError("Month and day must be provided together.")
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")
    if day < 1:
        raise ValueError("Day must be at least 1.")
    max_day = calendar.monthrange(2024 if month == 2 else 2023, month)[1]
    if day > max_day:
        raise ValueError("Day is not valid for this month.")


def occurrence_date(year, month, day):
    validate_month_day(month, day)
    if month == 2 and day == 29 and not is_leap_year(year):
        return date(year, 2, 28)
    return date(year, month, day)


def date_to_month_day(value):
    if value.month == 2 and value.day == 28 and not is_leap_year(value.year):
        return MonthDay(2, 29)
    return MonthDay(value.month, value.day)


def month_day_matches(value, month, day):
    return occurrence_date(value.year, month, day) == value


def next_occurrence(from_date, month, day):
    candidate = occurrence_date(from_date.year, month, day)
    if candidate < from_date:
        candidate = occurrence_date(from_date.year + 1, month, day)
    return candidate


def occurrence_sort_key(from_date, month, day):
    return (next_occurrence(from_date, month, day) - from_date).days


def jan_first_sort_key(year, month, day):
    return (occurrence_date(year, month, day) - date(year, 1, 1)).days


def years_for_window(start, end):
    return range(start.year, end.year + 1)


def eastern_datetime(day, value):
    return datetime.combine(day, value, tzinfo=EASTERN_TIME)


def is_schedule_due(now, scheduled_time, grace_minutes=31):
    local_now = now.astimezone(EASTERN_TIME)
    scheduled_at = eastern_datetime(local_now.date(), scheduled_time)
    return scheduled_at <= local_now < scheduled_at + timedelta(minutes=grace_minutes)


def parse_month_name(value):
    value = value.strip()
    months = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
    months.update({name.lower(): index for index, name in enumerate(calendar.month_abbr) if name})
    try:
        return months[value.lower()]
    except KeyError as exc:
        raise ValueError("Unknown month: {}".format(value)) from exc


def parse_month_day(value):
    value = (value or "").strip()
    if not value:
        return None, None
    pieces = [piece for piece in re.split(r"[\s-]+", value.replace(",", "")) if piece]
    if len(pieces) != 2:
        raise ValueError("Expected month and day, got: {}".format(value))

    for month_piece, day_piece in (pieces, pieces[::-1]):
        try:
            return parse_month_name(month_piece), int(day_piece)
        except ValueError:
            continue

    raise ValueError("Expected month and day, got: {}".format(value))


def display_month_day(month, day):
    if month is None or day is None:
        return ""
    return MonthDay(month, day).display


def relative_day_phrase(days_until):
    if days_until == 0:
        return "Today"
    if days_until == 1:
        return "Tomorrow"
    if days_until == -1:
        return "Yesterday"
    if days_until > 1:
        return "In {} days".format(days_until)
    return "{} days ago".format(abs(days_until))


def default_time(hour, minute):
    return time(hour=hour, minute=minute)

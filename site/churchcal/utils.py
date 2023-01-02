from datetime import date

from django.utils import timezone

import arrow
from delorean import Delorean


def weekday_after(weekday, month, day, year=None, number_after=1):
    if not year:
        year = arrow.utcnow().format("YYYY")

    weekday = weekday.lower()
    direction = "last" if number_after < 1 else "next"
    number_after = abs(number_after)
    d = Delorean(datetime=timezone.datetime(year, month, day), timezone="UTC")
    return d._shift_date(direction, weekday, number_after).date


def easter(year):
    "Returns Easter as a date object."
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return date(year, month, day)


def advent(year):
    return weekday_after(weekday="sunday", month=12, day=25, year=year, number_after=-4)


week_days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

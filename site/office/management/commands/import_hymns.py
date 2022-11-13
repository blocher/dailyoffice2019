import requests
from django.core.management.base import BaseCommand

from office.models import StandardOfficeDay


def get_for_reading(day, attribute):
    citation = getattr(day, attribute)
    url = f"https://hymnary.org/api/scripture?reference={citation}"
    result = requests.get(url)
    if result.status_code != 200:
        return None
    results = result.json()
    if not len(results):
        return None
    results = list(results.values())
    results.sort(key=lambda x: int(x["number of hymnals"]), reverse=True)
    try:
        return results[0]["title"]
    except KeyError:
        return results[0]["text link"].split("/")[-1]


def get_for_day(day):
    mp1 = get_for_reading(day, "mp_reading_1")
    mp2 = get_for_reading(day, "mp_reading_2")
    ep1 = get_for_reading(day, "ep_reading_1")
    ep2 = get_for_reading(day, "ep_reading_2")
    print(
        day.month,
        "|",
        day.day,
        "|",
        day.mp_reading_1,
        "|",
        mp1,
        "|",
        day.mp_reading_2,
        "|",
        mp2,
        "|",
        day.ep_reading_1,
        "|",
        ep1,
        "|",
        day.ep_reading_2,
        "|",
        ep2,
    )


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        days = StandardOfficeDay.objects.order_by("month", "day").all()
        for day in days:
            print(get_for_day(day))

import csv
from datetime import date
from pathlib import Path

from django.db import transaction

from patrons.dates import parse_month_day, parse_month_name
from patrons.models import Event, FamilyMember, PatronalFeast


DATA_DIR = Path(__file__).resolve().parent / "data"
PATRONAL_FEASTS_CSV = DATA_DIR / "patronal_feasts.csv"
EVENTS_CSV = DATA_DIR / "events.csv"


FAMILY_FIELDS = {
    "first_name": "Family Member (first name)",
    "middle_name": "Family Member (middle name)",
    "confirmation_name": "Family Member (confirmation name)",
    "maiden_name": "Family Member (maiden name)",
    "last_name": "Family Member (last name)",
}


EVENT_TYPE_MAP = {
    "birthday": Event.BIRTHDAY,
    "baptism": Event.BAPTISM,
    "baptism day": Event.BAPTISM,
    "wedding": Event.WEDDING,
    "wedding day": Event.WEDDING,
    "confirmation": Event.CONFIRMATION,
    "confirmation day": Event.CONFIRMATION,
    "first confession": Event.FIRST_CONFESSION,
    "first confession day": Event.FIRST_CONFESSION,
    "first communion": Event.FIRST_COMMUNION,
    "first communion day": Event.FIRST_COMMUNION,
    "ordination (diaconal)": Event.DIACONAL_ORDINATION,
    "diaconal ordination": Event.DIACONAL_ORDINATION,
    "diaconal ordination day": Event.DIACONAL_ORDINATION,
    "ordination (priestly)": Event.PRIESTLY_ORDINATION,
    "priestly ordination": Event.PRIESTLY_ORDINATION,
    "priestly ordination day": Event.PRIESTLY_ORDINATION,
    "death": Event.DEATH,
    "death day": Event.DEATH,
}


def family_values(row):
    return {field: row.get(csv_field, "").strip() for field, csv_field in FAMILY_FIELDS.items()}


def row_has_family(row):
    return any(family_values(row).values())


def get_or_update_family_member(values):
    member, _created = FamilyMember.objects.update_or_create(
        first_name=values["first_name"],
        middle_name=values["middle_name"],
        confirmation_name=values["confirmation_name"],
        maiden_name=values["maiden_name"],
        last_name=values["last_name"],
        defaults=values,
    )
    return member


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        yield from csv.DictReader(csv_file)


@transaction.atomic
def import_patronal_feasts(path=PATRONAL_FEASTS_CSV):
    PatronalFeast.objects.all().delete()

    current_member = None
    created_count = 0
    for row in read_csv(path):
        if row_has_family(row):
            current_member = get_or_update_family_member(family_values(row))

        normalized_name = row.get("Normalized Name", "").strip()
        feast_name = row.get("Feast Name", "").strip()
        if not normalized_name or not feast_name:
            continue
        if current_member is None:
            continue

        general_month, general_day = parse_month_day(row.get("General Roman Calendar (USA)", ""))
        traditional_month, traditional_day = parse_month_day(row.get("Traditional Roman Calendar (1954)", ""))
        episcopal_month, episcopal_day = parse_month_day(row.get("Episcopal Church", ""))
        feast = PatronalFeast(
            family_member=current_member,
            normalized_name=normalized_name,
            feast_name=feast_name,
            general_calendar_name=row.get("Feast Name on General Roman Calendar", "").strip(),
            traditional_calendar_name=row.get("Feast Name on Traditional Roman Calendar", "").strip(),
            episcopal_calendar_name=row.get("Feast Name in Episcopal Church", "").strip(),
            general_month=general_month,
            general_day=general_day,
            traditional_month=traditional_month,
            traditional_day=traditional_day,
            episcopal_month=episcopal_month,
            episcopal_day=episcopal_day,
        )
        feast.full_clean()
        feast.save()
        created_count += 1

    return created_count


@transaction.atomic
def import_patron_events(path=EVENTS_CSV):
    Event.objects.all().delete()

    created_count = 0
    for row in read_csv(path):
        member = get_or_update_family_member(family_values(row))
        event_type = EVENT_TYPE_MAP[row["Event Type"].strip().lower()]
        event = Event(
            family_member=member,
            event_type=event_type,
            date=date(
                int(row["Year"].strip()),
                parse_month_name(row["Month"]),
                int(row["Day"].strip()),
            ),
        )
        event.full_clean()
        event.save()
        created_count += 1

    return created_count

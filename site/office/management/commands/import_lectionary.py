from django.core.management.base import BaseCommand
from django.db.models import Q

from churchcal.calculations import ChurchYear
from churchcal.models import (
    Commemoration,
    SanctoraleCommemoration,
    SanctoraleBasedCommemoration,
    Proper,
    Common,
    MassReading,
)
from office.models import LectionaryItem


def add_ember_readings():
    common_1 = Common.objects.filter(abbreviation="EMBER_DAY_1").first()
    if not common_1:
        Common.objects.filter(abbreviation="EMBER_DAY").update(abbreviation="EMBER_DAY_1")
    common_2 = Common.objects.filter(abbreviation="EMBER_DAY_2").first()
    if not common_2:
        common_2 = Common.objects.get(abbreviation="EMBER_DAY_1")
        common_2.abbreviation = "EMBER_DAY_2"
        common_2.uuid = None
        common_2.save()
    Common.objects.filter(abbreviation="EMBER_DAY_1").update(name="Ember Day (I)")
    Common.objects.filter(abbreviation="EMBER_DAY_2").update(name="Ember Day (II)")
    ember_readings = MassReading.objects.filter(abbreviation__contains="EMBER_DAY_SPRING_FRI").all()
    for reading in ember_readings:
        com = common_1 if reading.service == "I" else common_2
        match = MassReading.objects.filter(
            service=reading.service, long_citation=reading.long_citation, common=com
        ).first()
        if not match:
            reading.uuid = None
            reading.common = com
            reading.abbreviation = "EMBER_DAY_1" if reading.service == "I" else "EMBER_DAY_2"
            reading.commemoration = None
            reading.save()


def add_rogation_readings():
    common_1 = Common.objects.filter(abbreviation="ROGATION_DAY_1").first()
    if not common_1:
        Common.objects.filter(abbreviation="ROGATION_DAY").update(abbreviation="ROGATION_DAY_1")
    common_2 = Common.objects.filter(abbreviation="ROGATION_DAY_2").first()
    if not common_2:
        common_2 = Common.objects.get(abbreviation="ROGATION_DAY_1")
        common_2.abbreviation = "ROGATION_DAY_2"
        common_2.uuid = None
        common_2.save()
    Common.objects.filter(abbreviation="ROGATION_DAY_1").update(name="Rogation Day (I)")
    Common.objects.filter(abbreviation="ROGATION_DAY_2").update(name="Rogation Day (II)")
    ember_readings = MassReading.objects.filter(abbreviation__contains="ROGATION_DAY_MON").all()
    for reading in ember_readings:
        com = common_1 if reading.service == "I" else common_2
        match = MassReading.objects.filter(
            service=reading.service, long_citation=reading.long_citation, common=com
        ).first()
        if not match:
            reading.uuid = None
            reading.common = com
            reading.abbreviation = "ROGATION_DAY_1" if reading.service == "I" else "ROGATION_DAY_2"
            reading.commemoration = None
            reading.save()


def get_items():
    feasts = []
    year = ChurchYear(2021)
    for day in year:
        if (
            day.primary.rank.precedence_rank <= 2
            or "Presentation" in day.primary.name
            or "Circumcision" in day.primary.name
        ):
            if day.primary.rank.precedence_rank == 2 and day.proper:
                continue
            feast = Commemoration.objects.get(pk=day.primary.pk)
            feasts.append(feast)
    pre_new_year_holy_days = SanctoraleCommemoration.objects.filter(rank__precedence_rank=3, month__gte=11).order_by(
        "month", "day"
    )
    post_new_year_holy_days = SanctoraleCommemoration.objects.filter(rank__precedence_rank=3, month__lt=11).order_by(
        "month", "day"
    )
    feast_pks = [f.pk for f in feasts]
    missing_epiphanies = (
        SanctoraleBasedCommemoration.objects.filter(name__contains="Epiphany", calendar__abbreviation="ACNA_BCP2019")
        .exclude(pk__in=feast_pks)
        .order_by("number_after")
        .all()
    )
    for second_last_position, feast in enumerate(feasts):
        if "The Second to Last Sunday of Epiphany" in feast.name:
            break
    for missing in missing_epiphanies:
        feasts.insert(second_last_position, missing)
        second_last_position = second_last_position + 1
    early_propers = Proper.objects.filter(number__lte=25).order_by("number").all()
    late_propers = Proper.objects.filter(number__gt=25).order_by("number").all()
    for all_saints_position, feast in enumerate(feasts):
        if "All Saint" in feast.name:
            break
    for proper in early_propers:
        feasts.insert(all_saints_position, proper)
        all_saints_position = all_saints_position + 1
    for proper in late_propers:
        all_saints_position = all_saints_position + 1
        feasts.insert(all_saints_position, proper)

    add_ember_readings()
    add_rogation_readings()

    commons = (
        Common.objects.order_by("name")
        .exclude(abbreviation__contains="EMBER")
        .exclude(abbreviation__contains="ROGATION")
        .all()
    )
    holidays = []
    for day in year:
        if day.primary.rank.name in ["NATIONAL_DAY_UNITED_STATES", "NATIONAL_DAY_CANADA"]:
            feast = Commemoration.objects.get(pk=day.primary.pk)
            holidays.append(feast)

    embers = (
        Common.objects.order_by("name")
        .filter(Q(abbreviation__contains="EMBER") | Q(abbreviation__contains="ROGATION"))
        .all()
    )

    return (
        feasts
        + list(pre_new_year_holy_days)
        + list(post_new_year_holy_days)
        + list(embers)
        + list(holidays)
        + list(commons)
    )

    # commemoration = models.ForeignKey(Commemoration, on_delete=models.SET_NULL, null=True, blank=True)
    # proper = models.ForeignKey(Proper, on_delete=models.SET_NULL, null=True, blank=True)
    # common = models.ForeignKey(Common, on_delete=models.SET_NULL, null=True, blank=True)
    # order = models.PositiveSmallIntegerField(default=0)
    # service = models.CharField(max_length=255)


def order():
    highest = LectionaryItem.objects.order_by("-order").first()
    if highest:
        return highest.order + 1
    return 1


def import_proper(proper):
    LectionaryItem.objects.create(proper=proper, order=order())


def import_common(common):
    LectionaryItem.objects.create(common=common, order=order())


def import_commemoration(commemoration):
    readings = commemoration.massreading_set.order_by("order").all()
    services = []
    for reading in readings:
        if reading.service not in services:
            services.append(reading.service)
    for service in services:
        sanctorale = commemoration if type(commemoration) == SanctoraleCommemoration else None
        LectionaryItem.objects.create(
            commemoration=commemoration, sanctorale_commemoration=sanctorale, order=order(), service=service
        )


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        LectionaryItem.objects.all().delete()
        items = get_items()
        for item in items:
            if type(item) == Proper:
                import_proper(item)
            if type(item) == Common:
                import_common(item)
            if isinstance(item, Commemoration):
                import_commemoration(item)
        items = LectionaryItem.objects.order_by("order").all()
        for item in items:
            print(item.name_and_service, item.date_string)

from django.core.management.base import BaseCommand

from churchcal.calculations import ChurchYear
from churchcal.models import Commemoration, SanctoraleCommemoration, SanctoraleBasedCommemoration, Proper, Common
from office.models import LectionaryItem


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
    commons = Common.objects.order_by("name").all()
    return feasts + list(pre_new_year_holy_days) + list(post_new_year_holy_days) + list(commons)

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

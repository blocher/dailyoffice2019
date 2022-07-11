from django.core.management.base import BaseCommand

from churchcal.calculations import ChurchYear
from churchcal.models import CommemorationRank
from office.models import Collect, CollectCategory


def create_collect(title, text, order, category_name):
    text = text.replace("Amen.", "").strip()
    text = f"<p>{text} <strong>Amen.</strong></p>"
    collect = Collect.objects.get_or_create(text=text)[0]
    collect.title = title
    collect.order = order
    collect.collect_type = "collect"
    collect.collect_category = None
    collect.collect_category = CollectCategory.objects.get(name=category_name)
    collect.save()


def create_collects_from_commemoration(commemoration, i):
    print(i)
    name = commemoration.name
    if "Rogation Day" in name:
        name = "Rogation Day"
    if "Ember Day" in name:
        name = "Ember Day"
    if commemoration.eve_collect:
        i = i + 1
        title = f"{name} (Eve)"
        create_collect(title, commemoration.eve_collect, i, commemoration.rank.formatted_name)
    if commemoration.collect:
        i = i + 1
        title = name
        if commemoration.alternate_collect:
            title = f"{name} (I)"
        create_collect(title, commemoration.collect, i, commemoration.rank.formatted_name)
    if commemoration.alternate_collect:
        i = i + 1
        title = f"{name} (II)"
        create_collect(title, commemoration.alternate_collect, i, commemoration.rank.formatted_name)
    return i


class Command(BaseCommand):
    help = "Migrate Collects to New Format"

    def handle(self, *args, **options):
        i = 13
        commemoration_ranks = (
            CommemorationRank.objects.filter(calendar__abbreviation="ACNA_BCP2019").order_by("precedence_rank").all()
        )
        for commemoration_rank in commemoration_ranks:
            i = i + 1
            CollectCategory.objects.get_or_create(name=commemoration_rank.formatted_name, order=i)
        Collect.objects.filter(collect_type="collect").all().delete()

        year = ChurchYear(2021)
        for day in year:
            print(day)
        # i = 0
        # sanctorale_based = SanctoraleBasedCommemoration.objects.filter(calendar__abbreviation="ACNA_BCP2019").order_by(
        #     "month_after", "day_after", "number_after").all()
        # i = loop_through_commemorations(sanctorale_based, i)
        # temporale_commemoration = TemporaleCommemoration.objects.filter(
        #     calendar__abbreviation="ACNA_BCP2019").order_by(
        #     "days_after_easter").all()
        # i = loop_through_commemorations(temporale_commemoration, i)
        # sanctorale_commemoration = SanctoraleCommemoration.objects.filter(
        #     calendar__abbreviation="ACNA_BCP2019").order_by(
        #     "month", "day").all()
        # i = loop_through_commemorations(sanctorale_commemoration, i)

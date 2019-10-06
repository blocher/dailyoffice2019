from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from churchcal.models import (
    CommemorationRank,
    Commemoration,
    Calendar,
    SanctoraleCommemoration,
    SanctoraleBasedCommemoration,
    TemporaleCommemoration,
)


class Command(BaseCommand):

    help = "Imports all Episcopal commemorations"

    def add_arguments(self, parser):

        parser.add_argument("--calendar", dest="calendar", help="Calendar to import for")

    def handle(self, *args, **options):

        if not options["calendar"]:
            raise Exception("You must supply a calendar id for which to import ranks.")

        try:
            calendar = Calendar.objects.get(pk=options["calendar"])
        except Calendar.DoesNotExist:
            raise Exception("You must supply a valid calendar id for which to import ranks.")

        print("===DELETING OLD DATA===".format(calendar.name))
        TemporaleCommemoration.objects.filter(calendar=calendar).delete()
        SanctoraleBasedCommemoration.objects.filter(calendar=calendar).delete()
        SanctoraleCommemoration.objects.filter(calendar=calendar).delete()
        Commemoration.objects.filter(calendar=calendar).delete()
        # CommemorationRank.objects.all().delete()

        # print ("===IMPORTING {}} RANKS===".format(calendar.name))
        # call_command('import_ranks', calendar=calendar)

        print("===IMPORTING {} SANCTORALE===".format(calendar.name))
        call_command("import_sanctorale", calendar=calendar.pk)

        print("===IMPORTING {} SANCTORALE BASED===".format(calendar.name))
        call_command("import_sanctorale_based", calendar=calendar.pk)

        print("===IMPORTING {} TEMPORALE===".format(calendar.name))
        call_command("import_temporale", calendar=calendar.pk)

        print("===IMPORTING {} SANCTORALE (NOT AFTER RESTRICTIONS)===".format(calendar.name))
        call_command("import_sanctorale", not_after=True, calendar=calendar.pk)

        print("===IMPORTING {} SANCTORALE BASED (NOT AFTER RESTRICTIONS)===".format(calendar.name))
        call_command("import_sanctorale_based", not_after=True, calendar=calendar.pk)

        print("===IMPORTING {} TEMPORALE (NOT AFTER RESTRICTIONS)===".format(calendar.name))
        call_command("import_temporale", not_after=True, calendar=calendar.pk)

        print("===IMPORTING PROPERS===".format(calendar.name))
        call_command("import_propers", calendar=calendar.pk)

        print("===IMPORTING SEASONS===".format(calendar.name))
        call_command("import_seasons", calendar=calendar.pk)

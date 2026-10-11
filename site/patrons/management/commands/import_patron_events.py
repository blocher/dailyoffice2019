from django.core.management.base import BaseCommand

from patrons.importers import EVENTS_CSV, import_patron_events


class Command(BaseCommand):
    help = "Import patron events from CSV."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=EVENTS_CSV, help="CSV file to import.")

    def handle(self, *args, **options):
        count = import_patron_events(options["file"])
        self.stdout.write(self.style.SUCCESS("Imported {} patron events.".format(count)))

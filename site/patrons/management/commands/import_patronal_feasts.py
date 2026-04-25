from django.core.management.base import BaseCommand

from patrons.importers import PATRONAL_FEASTS_CSV, import_patronal_feasts


class Command(BaseCommand):
    help = "Import patronal feasts from CSV."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=PATRONAL_FEASTS_CSV, help="CSV file to import.")

    def handle(self, *args, **options):
        count = import_patronal_feasts(options["file"])
        self.stdout.write(self.style.SUCCESS("Imported {} patronal feasts.".format(count)))

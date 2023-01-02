from builtins import NotImplementedError

from django.core.management.base import BaseCommand
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from churchcal.models import Calendar

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    help = "Imports Episcopal commemorations"

    def add_arguments(self, parser):
        parser.add_argument("--not_after", action="store_true", dest="not_after", help="Import not after import_dates")

        parser.add_argument("--calendar", dest="calendar", help="Calendar to import for")

    def handle(self, *args, **options):
        if not options["calendar"]:
            self.calendar = Calendar.objects.get(abbreviation="ACNA_BCP2019")
        else:
            try:
                self.calendar = Calendar.objects.get(pk=options["calendar"])
            except Calendar.DoesNotExist:
                raise Exception("You must supply a valid calendar id for which to import ranks.")

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=self.calendar.google_sheet_id, range=self.RANGE_NAME).execute()
        except HttpError as e:
            print("Data not found for this denomination")
            return

        self.values = result.get("values", [])

        if not self.values:
            print("No data found.")
            return

        self.values.pop(0)

        if options["not_after"]:
            self.import_not_after()
        else:
            self.import_dates()

    def import_dates(self):
        raise NotImplementedError

    def import_not_after(self):
        raise NotImplementedError

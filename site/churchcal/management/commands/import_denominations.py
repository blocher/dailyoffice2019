from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings
from googleapiclient.discovery import build

from churchcal.models import Denomination, Calendar

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    help = "Imports List of Denominations"

    SPREADSHEET_ID = "1Xas3sNlNclSeluPU0GGIu8IAK8YVpUGOHELNukKSqn8"
    RANGE_NAME = "Calendars!A3:F100"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range=self.RANGE_NAME).execute()
        self.values = result.get("values", [])

        for row in self.values:

            denomination = Denomination.objects.get_or_create(name=row[0])[0]
            denomination.abbreviation = row[1]
            denomination.save()

            calendar = Calendar.objects.get_or_create(denomination=denomination, year=row[4])[0]
            calendar.name = row[3]
            calendar.abbreviation = row[5]
            calendar.google_sheet_id = row[2]

            calendar.save()

            print("===IMPORTING RANKS FOR {}===".format(calendar.name))
            call_command("import_ranks", calendar=calendar.pk)

            print("===IMPORTING ALL FOR {}===".format(calendar.name))
            call_command("import_all", calendar=calendar.pk)

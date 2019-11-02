from django.core.management.base import BaseCommand

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from office.models import ThirtyDayPsalterDay


SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):

    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "30DayPsalter!A3:C33"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=self.SHEET_ID, range=self.RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            print("Worksheet not found")
            return

        for row in result.get("values", []):
            day = ThirtyDayPsalterDay.objects.get_or_create(day=row[0])[0]
            day.day = row[0]
            day.mp_psalms = row[1].replace(" ", "")
            day.ep_psalms = row[2].replace(" ", "")
            day.save()

        print("All done")

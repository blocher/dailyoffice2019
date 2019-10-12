from django.core.management.base import BaseCommand

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from office.models import OfficeDay
from bible import Passage


SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


def get_psalms(passage):
    text = ""
    passage = "".join(passage.split())
    passages = passage.split(",")
    for passage in passages:
        passage = "Psalm {}".format(passage)
        passage = Passage(passage, source="esv")
        text = text + passage.html

    return text


class Command(BaseCommand):
    help = "My shiny new management command."

    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "OfficeDates!A3:K368"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=self.SHEET_ID, range=self.RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            print("Data not found for this denomination")
            return

        OfficeDay.objects.all().delete()

        for row in result.get("values", []):
            OfficeDay.objects.create(
                month=row[0],
                day=row[1],
                holy_day=row[2],
                mp_psalms=row[3],
                mp_psalms_text=get_psalms(row[3]),
                mp_reading_1=row[4],
                mp_reading_1_abbreviated=row[5],
                mp_reading_2=row[6],
                ep_psalms=row[7],
                ep_psalms_text=get_psalms(row[7]),
                ep_reading_1=row[8],
                ep_reading_1_abbreviated=row[9],
                ep_reading_2=row[10],
            )

        print("All done")

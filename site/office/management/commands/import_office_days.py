import scriptures
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

    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "OfficeDates!A3:K368"

    def parse_passage(self, passage):
        try:
            passage = scriptures.extract(passage)[0]
            return scriptures.reference_to_string(*passage)
        except:
            return "-"

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

        for row in result.get("values", []):
            day = OfficeDay.objects.get_or_create(month=row[0], day=row[1])
            day = day[0]
            day.month = row[0]
            day.day = row[1]
            day.holy_day = row[2]
            day.mp_psalms = row[3]
            # day.mp_psalms_text = (get_psalms(row[3])
            day.mp_reading_1 = self.parse_passage(row[4])
            day.mp_reading_1_abbreviated = row[5]
            day.mp_reading_2 = self.parse_passage(row[6])
            day.ep_psalms = row[7]
            # day.ep_psalms_text = (get_psalms(row[7])
            day.ep_reading_1 = self.parse_passage(row[8])
            day.ep_reading_1_abbreviated = row[9]
            day.ep_reading_2 = self.parse_passage(row[10])
            day.save()

        print("All done")

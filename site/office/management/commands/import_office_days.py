import scriptures
from django.core.management.base import BaseCommand

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bible.sources import PassageNotFoundException
from churchcal.models import Commemoration
from office.models import StandardOfficeDay, HolyDayOfficeDay
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

    HOLY_DAY_RANGE_NAME = "OfficeDatesHolyDays!A3:G9"

    def get_testament(self, passage):

        try:
            passage = scriptures.extract(passage)[0]
            return passage[5]
        except:
            return "-"

    def parse_passage(self, passage):

        try:
            passage = scriptures.extract(passage)[0]
            return scriptures.reference_to_string(*passage)
        except:
            return None

    def parse_abbreviated_passage(self, original_passage, verses):

        verses = verses.replace(",", ", ")
        if verses:
            return "{}:{}".format(original_passage, verses)
        return None

    def get_abbreviated_passage(self, original_passage, verses=None):

        if not verses:
            return None
        verses = verses.split(",")
        passage = ""
        for verse in verses:
            passage = passage + self.get_passage("{}:{}".format(original_passage, verse))
        return passage

    def get_passage(self, passage):

        passage = self.parse_passage(passage)

        try:
            return Passage(passage, source="esv").html
        except PassageNotFoundException:
            try:
                return Passage(passage, source="rsv").html
            except PassageNotFoundException:
                return None

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
            # if row[1] != "13" or row[0] != "6":
            #     continue
            day = StandardOfficeDay.objects.get_or_create(month=row[0], day=row[1])
            day = day[0]
            day.month = row[0]
            day.day = row[1]
            day.holy_day_name = row[2]
            day.mp_psalms = row[3].replace(" ", "")
            day.mp_reading_1 = self.parse_passage(row[4])
            day.mp_reading_1_testament = self.get_testament(row[4])
            day.mp_reading_1_text = self.get_passage(row[4])
            day.mp_reading_1_abbreviated = self.parse_abbreviated_passage(day.mp_reading_1, row[5])
            day.mp_reading_1_abbreviated_text = self.get_abbreviated_passage(day.mp_reading_1, row[5])
            day.mp_reading_2 = self.parse_passage(row[6])
            day.mp_reading_2_testament = self.get_testament(row[6])
            day.mp_reading_2_text = self.get_passage(row[6])
            day.ep_psalms = row[7].replace(" ", "")
            day.ep_reading_1 = self.parse_passage(row[8])
            day.ep_reading_1_testament = self.get_testament(row[8])
            day.ep_reading_1_text = self.get_passage(row[8])
            day.ep_reading_1_abbreviated = self.parse_abbreviated_passage(day.ep_reading_1, row[9])
            day.ep_reading_1_abbreviated_text = self.get_abbreviated_passage(day.ep_reading_1, row[9])
            day.ep_reading_2 = self.parse_passage(row[10])
            day.ep_reading_2_testament = self.get_testament(row[10])
            day.ep_reading_2_text = self.get_passage(row[10])
            day.save()


        try:
            result = sheet.values().get(spreadsheetId=self.SHEET_ID, range=self.HOLY_DAY_RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            print("Worksheet for Holy Days not found")
            return
        for row in result.get("values", []):
            commemoration = Commemoration.objects.filter(calendar__abbreviation="ACNA_BCP2019", name=row[0]).first()
            day = HolyDayOfficeDay.objects.get_or_create(commemoration_id=commemoration.pk)[0]
            day.holy_day_name = row[0]
            day.mp_psalms = row[1].replace(" ", "")
            day.mp_reading_1 = self.parse_passage(row[2])
            day.mp_reading_1_testament = self.get_testament(row[2])
            day.mp_reading_1_text = self.get_passage(row[2])
            day.mp_reading_2 = self.parse_passage(row[3])
            day.mp_reading_2_testament = self.get_testament(row[3])
            day.mp_reading_2_text = self.get_passage(row[3])
            day.ep_psalms = row[4].replace(" ", "")
            day.ep_reading_1 = self.parse_passage(row[5])
            day.ep_reading_1_text = self.get_passage(row[5])
            day.ep_reading_1_testament = self.get_testament(row[5])
            day.ep_reading_2 = self.parse_passage(row[6])
            day.ep_reading_2_testament = self.get_testament(row[6])
            day.ep_reading_2_text = self.get_passage(row[6])
            day.save()

        print("All done")

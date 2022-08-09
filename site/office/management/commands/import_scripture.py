import scriptures
from django.core.management.base import BaseCommand

from bible import Passage
from bible.sources import PassageNotFoundException
from churchcal.models import MassReading
from office.models import OfficeDay, Scripture

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "OfficeDates!A3:K368"

    HOLY_DAY_RANGE_NAME = "OfficeDatesHolyDays!A3:G9"

    def parse_passage(self, passage):

        try:
            passage = scriptures.extract(passage)[0]
            return scriptures.reference_to_string(*passage)
        except:
            return None

    def break_apart_passages(self, original_passage):
        parts = original_passage.split(":")
        if len(parts) < 2:
            return [original_passage]
        chapter, verses = parts[0], parts[1]
        verses = verses.split(",")
        verses = [verse.strip() for verse in verses]
        passages = [f"{chapter}:{verse}" for verse in verses]
        return passages

    def get_passages(self, passage, translation="esv"):
        final = []
        passages = self.break_apart_passages(passage)
        for passage in passages:
            passage = self.parse_passage(passage)
            try:
                result = Passage(passage, source=translation).html
                final.append(result.strip())
            except PassageNotFoundException:
                return "-"
        return " ".join(final)

    def handle(self, *args, **options):

        days = OfficeDay.objects.all()
        translations = ["esv", "rsv", "kjv"]
        texts = [
            "mp_reading_1",
            "mp_reading_2",
            "ep_reading_1",
            "ep_reading_2",
            "mp_reading_1_abbreviated",
            "ep_reading_1_abbreviated",
        ]

        for day in days:
            for text in texts:
                passage = getattr(day, text)
                if passage:
                    scripture = Scripture.objects.get_or_create(passage=passage)[0]
                    for translation in translations:
                        existing = getattr(scripture, translation)
                        if not existing:
                            setattr(scripture, translation, self.get_passages(passage, translation))
                    scripture.save()

        mass_readings = MassReading.objects.all()
        texts = ["long_citation", "short_citation"]
        for reading in mass_readings:
            for text in texts:
                passage = getattr(reading, text)
                if passage:
                    scripture = Scripture.objects.get_or_create(passage=passage)[0]
                    for translation in translations:
                        existing = getattr(scripture, translation)
                        if not existing:
                            setattr(scripture, translation, self.get_passages(passage, translation))
                    scripture.save()

        needed_for_apocrypha = Scripture.objects.filter(kjv="-").all()
        for scripture in needed_for_apocrypha:
            scripture.kjv = self.get_passages(scripture.passage, "av")
            scripture.save()

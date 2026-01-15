import re

import scriptures
from django.core.management.base import BaseCommand

from bible.passage import Passage
from bible.sources import PassageNotFoundException
from churchcal.models import MassReading
from office.models import OfficeDay, Scripture

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    def parse_passage(self, passage):
        try:
            passage = scriptures.extract(passage)[0]
            return scriptures.reference_to_string(*passage)
        except:
            return None

    def break_apart_passages(self, original_passage):
        if "," not in original_passage:
            return [original_passage]
        book = re.sub(r"[^A-Za-z ]", "", original_passage)
        book = re.sub(r" +", " ", book.strip())
        chapter_verse = re.sub(r"[^0-9-,:]", "", original_passage)
        passages = chapter_verse.split(",")
        citations = []
        chapter = None
        for passage in passages:
            passage = passage.strip()
            if not passage:
                continue

            count = passage.count(":")
            if count > 1:
                citations.append(f"{book} {passage}")
            else:
                if ":" in passage:
                    try:
                        chapter, verses = passage.split(":")
                    except ValueError as e:
                        print("ERROR", original_passage)
                        raise (e)
                else:
                    verses = passage
                if chapter:
                    citations.append(f"{book} {chapter}:{verses}")
                else:
                    citations.append(f"{book} {verses}")
        return citations

    def get_passages(self, passage, translation="esv"):
        final = []
        passages = self.break_apart_passages(passage)
        for passage in passages:
            if "Psalms" not in passage:
                passage = self.parse_passage(passage)
            try:
                result = Passage(passage, source=translation).html
                final.append(result.strip())
            except PassageNotFoundException:
                return "-"
        return " ".join(final)

    def handle(self, *args, **options):
        days = OfficeDay.objects.all()
        translations = ["esv", "rsv", "kjv", "nrsvce", "nabre", "niv", "nasb", "coverdale", "renewed_coverdale", "nvi"]
        translations = ["nvi"]
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
                            text = self.get_passages(passage, translation)
                            setattr(scripture, translation, text)
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

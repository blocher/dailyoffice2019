import operator
import re
from functools import reduce

import scriptures
from django.db.models import Q

from bible import Passage
from bible.sources import PassageNotFoundException
from churchcal.management.commands.import_base import Command as ImportCommemorationsBaseCommand
from churchcal.models import MassReading, Proper, Commemoration, Common
from psalter.utils import get_psalms, parse_single_psalm


class Command(ImportCommemorationsBaseCommand):
    help = "Imports Mass Readings"

    RANGE_NAME = "Mass Readings!A1:G1051"

    def format_reading(self, book, passage):
        if book == "Canticle":
            canticle_class = self.get_canticle_class(passage)
            return canticle_class.citation

        passage = "{} {}".format(book, passage)

        if book == "Ps":
            return passage.replace("Ps", "Psalms")
        references = scriptures.extract(passage)
        if not references:
            return passage
        result = []
        for i, reference in enumerate(references):
            print(reference)
            string = scriptures.reference_to_string(*reference)
            print(string)
            if i == 0:
                result.append(string)
            elif reference[1] == references[i - 1][1] and reference[1] == reference[3]:
                result.append("{}-{}".format(reference[2], reference[4]))
            elif reference[1] != references[i - 1][1] and reference[1] == reference[3]:
                result.append("{}:{}-{}".format(reference[1], reference[2], reference[4]))
            elif reference[1] != reference[3]:
                result.append("{}:{}-{}:{}".format(reference[1], reference[2], reference[3], reference[4]))

        return ", ".join(result)

    def get_book(self, book, passage):

        if book == "Canticle":
            return "-"

        passage = "{} {}".format(book, passage)

        try:
            return scriptures.extract(passage)[0][0]
        except IndexError:
            return "-"

    def get_testament(self, book, passage):

        if book == "Canticle":
            return "NA"

        passage = "{} {}".format(book, passage)

        try:
            return scriptures.extract(passage)[0][5]
        except IndexError:
            return "NA"

    def get_reading_type(self, book, passage):
        if book == "Canticle":
            return "psalm"
        passage = "{} {}".format(book, passage)
        try:
            reference = scriptures.extract(passage)[0]
            book = reference[0]
            testament = reference[5]
            if book in ("Matthew", "Mark", "Luke", "John"):
                return "gospel"
            if book == "Psalms":
                return "psalm"
            if testament == "NT":
                return "epistle"
            return "prophecy"
        except IndexError:
            return "unknown"

    def handle_odd_commemoration(self, code):

        codes = {
            "AllSaints": "All Saints’ Day",
            "AllSaintsSunday": "All Saints' Sunday",
            "Andrew": "Andrew the Apostle",
            "Ascension": "Ascension Day",
            "CanadaDay": "Canada Day (Canada)",
            "Christmas": "The Nativity of our Lord Jesus Christ: Christmas Day",
            "Easter": "Easter Day",
            "EasterEve": "Easter Day",
            "EasterVII": "The Sunday after the Ascension",
            "Epiphany": "The Epiphany: The Manifestation of Christ to the Gentiles",
            "EpiphanyPaenultima": "The Second to Last Sunday of Epiphany: World Mission Sunday, or Sexagesima",
            "EpiphanyUltima": "The Last Sunday of Epiphany: Transfiguration, or Quinquagesima",
            "James": "James the Elder, Apostle",
            "John": "John, Apostle and Evangelist",
            "JohnTheBaptist": "The Beheading of John the Baptist",
            "Joseph": "Joseph, Husband of the Virgin Mary and Guardian of Jesus",
            "Mark": "Mark the Evangelist",
            "Mary": "The Virgin Mary, Mother of our Lord Jesus Christ",
            "Michael": "Holy Michael and All Angels",
            "MemorialDay": "Memorial Day (United States)",
            "RemembranceDay": "Remembrance Day (Canada)",
            "Paul": "Peter and Paul, Apostles",
            "Pentecost": "The Day of Pentecost",
            "Peter": "Confession of Peter the Apostle",
            "ThanksgivingUS": "Thanksgiving Day (United States)",
            "ThanksgivingCanada": "Thanksgiving Day (Canada)",
            "Thomas": "Thomas the Apostle",
            "Transfiguration": "The Transfiguration of Our Lord Jesus Christ",
            "TrinitySunday": "Trinity Sunday",
        }

        try:
            name = codes[code]
        except AttributeError:
            return None

        if name:
            try:
                return Commemoration.objects.filter(calendar=self.calendar).get(name=name)
            except Commemoration.DoesNotExist:
                return None

    def get_common(self, code):
        return Common.objects.filter(abbreviation=code).first()

    def get_proper(self, code):
        if "Proper" in code:
            number = code.replace("Proper", "")
            return Proper.objects.filter(calendar=self.calendar).get(number=number)
        return None

    def decode_roman_numeral(self, roman):
        """Calculate the numeric value of a Roman numeral (in capital letters)"""
        try:
            trans = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
            values = [trans[r] for r in roman]
            return sum(val if val >= next_val else -val for val, next_val in zip(values[:-1], values[1:])) + values[-1]
        except (KeyError, IndexError):
            return None

    def number_to_ordinal(self, number):
        ordinals = {
            1: "First",
            2: "Second",
            3: "Third",
            4: "Fourth",
            5: "Fifth",
            6: "Sixth",
            7: "Seventh",
            8: "Eighth",
            9: "Ninth",
            10: "Tenth",
        }

        try:
            return ordinals[number]
        except KeyError:
            return None

    def get_numbered_commemoration(self, code, season):
        if season not in code:
            return None
        code = code.replace(season, "")
        if code:
            number = self.decode_roman_numeral(code)
            if number:
                ordinal = self.number_to_ordinal(number)
                if ordinal:
                    commemoration = (
                        Commemoration.objects.filter(calendar=self.calendar, name__icontains=ordinal)
                        .filter(name__icontains=season)
                        .first()
                    )
                    if commemoration:
                        return commemoration
        return None

    def get_commemoration(self, code):
        original_code = code
        proper = self.get_proper(code)
        if proper:
            return None
        for season in ["Advent", "Easter", "Christmas", "Epiphany", "Lent", "Easter"]:
            numbered_commemoration = self.get_numbered_commemoration(code, season)
            if numbered_commemoration:
                return numbered_commemoration

        ordinals = ("First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth")
        code = re.sub("([A-Z])", " \g<0>", code).strip().split(" ")
        try:
            res = (
                Commemoration.objects.filter(calendar=self.calendar)
                .filter(reduce(operator.and_, (Q(name__icontains=x) for x in code)))
                .exclude(reduce(operator.and_, (Q(name__icontains=x) for x in ordinals)))
                .get()
            )
            if res:
                return res
        except (Commemoration.MultipleObjectsReturned, Commemoration.DoesNotExist):
            pass

        res = self.handle_odd_commemoration(original_code)
        if res:
            return res
        return None

    def parse_passage(self, passage):
        print(passage)
        try:
            return scriptures.reference_to_string(*passage)
        except:
            return None

    def get_passage(self, book, passage, reading_type):

        if book == "Canticle":
            canticle = self.get_canticle_class(passage)
            return "<h3>{}</h3><h4>{}</h4>{}<h5>{}</h5>".format(
                canticle.latin_name, canticle.english_name, canticle().content, canticle.citation
            )

        if reading_type == "psalm":
            passage = passage.replace("Psalms ", "")
            psalm = parse_single_psalm(passage)
            return get_psalms(psalm)

        passage = "{} {}".format(book, passage)

        if book == "Ps":
            return passage.replace("Ps", "Psalms")
        references = scriptures.extract(passage)

        passages = []
        for reference in references:
            passage = scriptures.reference_to_string(*reference)
            try:
                passages.append(Passage(passage, source="esv").html)
            except PassageNotFoundException:
                try:
                    passages.append(Passage(passage, source="rsv").html)
                except PassageNotFoundException:
                    pass

        return "<br>".join(passages)

    def get_canticle_class(self, label):

        mod = __import__("office.canticles", fromlist=[label])
        return getattr(mod, label)

    def import_dates(self):

        MassReading.objects.filter(calendar=self.calendar).delete()
        self.values.pop(0)
        for i, row in enumerate(self.values):
            reading = MassReading()
            reading.calendar = self.calendar
            reading.book = self.get_book(row[4], row[5])
            reading.testament = self.get_testament(row[4], row[5])
            reading.long_citation = self.format_reading(row[4], row[5])
            if len(row) > 6:
                reading.short_citation = self.format_reading(row[4], row[6])
            reading.service = row[1]
            reading.years = row[3].replace(",", "")
            reading.reading_type = self.get_reading_type(row[4], row[5])
            reading.common = self.get_common(row[0])
            reading.proper = self.get_proper(row[0]) if not reading.common else None
            reading.commemoration = (
                self.get_commemoration(row[0]) if not reading.common and not reading.proper else None
            )
            reading.abbreviation = row[0]
            reading.reading_number = row[2]
            reading.order = i

            reading.long_text = self.get_passage(row[4], row[5], reading.reading_type)
            if reading.short_citation:
                reading.short_text = self.get_passage(row[4], row[5], reading.reading_type)

            reading.save()

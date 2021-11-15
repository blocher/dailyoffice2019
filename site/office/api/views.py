import csv
import os
from distutils.util import strtobool
from urllib.parse import quote

from bs4 import BeautifulSoup
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateResponseMixin
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from office.api.serializers import UpdateNoticeSerializer
from office.canticles import DefaultCanticles, BCP1979CanticleTable, REC2011CanticleTable
from office.models import UpdateNotice, HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay
from office.utils import passage_to_citation


class UpdateNoticeView(TemplateResponseMixin, ListAPIView):
    queryset = UpdateNotice.objects.all()
    serializer_class = UpdateNoticeSerializer

    # def get_queryset(self):
    #     queryset = UpdateNotice.objects.order_by("-version", "-created")
    #     mode = self.request.path.split('/').pop()
    #     if mode == 'web':
    #         queryset = queryset.filter(web_mode=True)
    #     if mode == 'app':
    #         queryset = queryset.filter(app_mode=True)
    #     return queryset.all()


class Settings(dict):

    DEFAULT_SETTINGS = {
        "psalter": "60",
        "reading_cycle": "1",
        "reading_length": "full",
        "reading_audio": "off",
        "canticle_rotation": "default",
        "theme": "theme-auto",
        "lectionary": "daily-office-readings",
        "confession": "long-on-fast",
        "absolution": "lay",
        "morning_prayer_invitatory": "invitatory_traditional",
        "reading_headings": "off",
        "language_style": "traditional",
        "national_holidays": "all",
        "suffrages": "rotating",
        "collects": "rotating",
        "pandemic_prayers": "pandemic_yes",
        "mp_great_litany": "mp_litany_off",
        "ep_great_litany": "ep_litany_off",
        "general_thanksgiving": "on",
        "chrysostom": "on",
        "grace": "rotating",
        "o_antiphons": "literal",
    }

    def __init__(self, request):
        settings = self._get_settings(request)
        super().__init__(**settings)

    def _get_settings(self, request):
        settings = self.DEFAULT_SETTINGS.copy()
        specified_settings = {k: v for (k, v) in request.query_params.items() if k in settings.keys()}
        for k, v in settings.items():
            if k in specified_settings.keys():
                settings[k] = specified_settings[k]
        return settings


# heading
# subheading
# citation
# html
# leader
# congregation
# rubric


def file_to_lines(filename):
    def process_row(row):
        result = {"content": row[0]}
        if len(row) > 1 and row[1]:
            result["line_type"] = row[1]
        if len(row) > 2:
            if not row[2]:
                result["indented"] = False
            else:
                result["indented"] = bool(strtobool(row[2].lower()))
        return result

    filename = "{}.csv".format(filename.replace(".csv", ""))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open("{}/texts/{}".format(dir_path, filename), encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL, skipinitialspace=True)
        return [Line(**process_row(row)) for row in reader]


class Line(dict):
    def __init__(self, content, line_type="congregation", indented=False, *args, **kwargs):
        super().__init__(content=content, line_type=line_type, indented=indented, *args, **kwargs)


class Module(object):
    def __init__(self, office):
        self.office = office

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def strip_line(self, line):
        line["content"] = line["content"].strip()
        line["line_type"] = line["line_type"].strip()
        return line

    def get_formatted_lines(self):
        lines = [self.strip_line(line) for line in self.get_lines()]
        lines = [line for line in lines if line and line.get("content")]
        lines = [self.mark_html_safe(line) for line in lines]
        return lines

    def get_lines(self):
        raise NotImplementedError("You must implement this method.")

    @staticmethod
    def mark_html_safe(line):
        if not isinstance(line, dict):
            return line
        if line.get("line_type") == "html":
            line["content"] = mark_safe(line["content"])
        return line

    @cached_property
    def json(self):
        lines = self.get_formatted_lines()
        return {"name": self.get_name(), "lines": lines}


class MPOpeningSentence(Module):
    name = "Opening Sentence"

    def get_sentence(self):

        if "Thanksgiving Day" in self.office.date.primary.name:
            return {
                "sentence": "Honor the Lord with your wealth and with the firstfruits of all your produce; then your barns will be filled with plenty, and your vats will be bursting with wine.",
                "citation": "PROVERBS 3:9-10",
            }

        if self.office.date.season.name == "Holy Week":

            return {
                "sentence": "Is it nothing to you, all you who pass by? Look and see if there is any sorrow like my sorrow, which was brought upon me, which the Lord inflicted on the day of his fierce anger.",
                "citation": "LAMENTATIONS 1:12",
            }

        if (
            self.office.date.season.name == "Lent"
            or self.office.date.primary.rank.name == "EMBER_DAY"
            or self.office.date.primary.rank.name == "ROGATION_DAY"
        ):

            if self.office.date.date.weekday() in [6, 2]:  # Sunday, Wednesday
                return {"sentence": "Repent, for the kingdom of heaven is at hand.", "citation": "MATTHEW 3:2"}

            if self.office.date.date.weekday() in [0, 3, 5]:  # Monday, Thursday, Saturday
                return {
                    "sentence": "Turn your face from my sins, and blot out all my misdeeds.",
                    "citation": "PSALM 51:9",
                }

            return {
                "sentence": "If anyone would come after me, let him deny himself and take up his cross and follow me.",
                "citation": "MARK 8:34",
            }

        if self.office.date.season.name == "Advent":

            return {
                "sentence": "In the wilderness prepare the way of the Lord; make straight in the desert a highway for our God.",
                "citation": "ISAIAH 40:3",
            }

        if self.office.date.season.name == "Christmastide":
            return {
                "sentence": "Fear not, for behold, I bring you good news of great joy that will be for all the people. For unto you is born this day in the city of David a Savior, who is Christ the Lord.",
                "citation": "LUKE 2:10-11",
            }

        if self.office.date.season.name == "Epiphanytide":
            return {
                "sentence": "From the rising of the sun to its setting my name will be great among the nations, and in every place incense will be offered to my name, and a pure offering. For my name will be great among the nations, says the Lord of hosts.",
                "citation": "MALACHI 1:11",
            }

        if (
            "Ascension" in self.office.date.primary.name
            or len(self.office.date.all) > 1
            and "Ascension" in self.office.date.all[1].name
        ):
            return {
                "sentence": "Since then we have a great high priest who has passed through the heavens, Jesus, the Son of God, let us hold fast our confession. Let us then with confidence draw near to the throne of grace, that we may receive mercy and find grace to help in time of need.",
                "citation": "HEBREWS 4:14, 16",
            }

        if self.office.date.primary.name == "The Day of Pentecost":

            return {
                "sentence": "You will receive power when the Holy Spirit has come upon you, and you will be my witnesses in Jerusalem and in all Judea and Samaria, and to the end of the earth.",
                "citation": "ACTS 1:8",
            }

        if self.office.date.primary.name == "Trinity Sunday":
            return {
                "sentence": "Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!",
                "citation": "REVELATION 4:8",
            }

        if self.office.date.season.name == "Eastertide":
            return {
                "sentence": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God.",
                "citation": "COLOSSIANS 3:1",
            }

        if self.office.date.date.weekday() == 6:
            return {
                "sentence": "Grace to you and peace from God our Father and the Lord Jesus Christ.",
                "citation": "PHILIPPIANS 1:2",
            }

        if self.office.date.date.weekday() == 0:
            return {
                "sentence": "I was glad when they said unto me, “We will go into the house of the Lord.”",
                "citation": "PSALM 122:1",
            }

        if self.office.date.date.weekday() == 1:
            return {
                "sentence": "Let the words of my mouth and the meditation of my heart be always acceptable in your sight, O Lord, my rock and my redeemer.",
                "citation": "PSALM 19:14",
            }

        if self.office.date.date.weekday() == 2:
            return {
                "sentence": "The Lord is in his holy temple; let all the earth keep silence before him.",
                "citation": "HABAKKUK 2:20",
            }

        if self.office.date.date.weekday() == 3:
            return {
                "sentence": "O send out your light and your truth, that they may lead me, and bring me to your holy hill, and to your dwelling.",
                "citation": "PSALM 43:3",
            }

        if self.office.date.date.weekday() == 4:
            return {
                "sentence": "Thus says the One who is high and lifted up, who inhabits eternity, whose name is Holy: “I dwell in the high and holy place, and also with him who is of a contrite and lowly spirit, to revive the spirit of the lowly, and to revive the heart of the contrite.”",
                "citation": "ISAIAH 57:15",
            }

        if self.office.date.date.weekday() == 5:
            return {
                "sentence": "The hour is coming, and is now here, when the true worshipers will worship the Father in spirit and truth, for the Father is seeking such people to worship him.",
                "citation": "JOHN 4:23",
            }

    def get_lines(self):
        sentence = self.get_sentence()
        return [
            Line("Opening Sentence", "heading"),
            Line(sentence["sentence"], "leader"),
            Line(sentence["citation"], "citation"),
        ]


class Office(object):
    def __init__(self, request, year, month, day):
        from churchcal.calculations import get_calendar_date

        self.settings = Settings(request)

        self.date = get_calendar_date("{}-{}-{}".format(year, month, day))

        try:
            self.office_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except HolyDayOfficeDay.DoesNotExist:
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)

    def get_modules(self):
        raise NotImplementedError("You must implement this method.")


class Confession(Module):

    name = "Confession of Sin"

    def get_intro_lines(self):
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return file_to_lines("confession_intro_long")
        return file_to_lines("confession_intro_short")

    def get_body_lines(self):
        return file_to_lines("confession_body")

    def get_absolution_lines(self):
        lay = self.office.settings["absolution"] == "lay"
        if lay:
            return file_to_lines("confession_absolution_lay")
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return file_to_lines("confession_absolution_long")
        return file_to_lines("confession_absolution_short")

    def get_lines(self):
        return (
            [Line("Confession of Sin", "heading")]
            + [Line("The Officiant says to the People", "rubric")]
            + self.get_intro_lines()
            + self.get_body_lines()
            + self.get_absolution_lines()
        )


class Preces(Module):

    name = "Preces"

    def get_lines(self):
        return file_to_lines("preces")


class MPInvitatory(Module):

    name = "Invitatory"

    @cached_property
    def antiphon(self):

        if "Presentation" in self.office.date.primary.name or "Annunciation" in self.office.date.primary.name:
            return {
                "first_line": "The Word was made flesh and dwelt among us:",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "The Day of Pentecost":
            return {
                "first_line": "Alleluia. The Spirit of the Lord renews the face of the earth:",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "Trinity Sunday":
            return {"first_line": "Father, Son, and Holy Spirit, one God:", "second_line": "O come, let us adore him."}

        if self.office.date.primary.name == "Easter Day":
            return {"first_line": "Alleluia. The Lord is risen indeed:", "second_line": "O come, let us adore him."}

        if (
            "Ascension" in self.office.date.primary.name
            or len(self.office.date.all) > 1
            and "Ascension" in self.office.date.all[1].name
        ):
            return {
                "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "The Transfiguration of Our Lord Jesus Christ":
            return {"first_line": "The Lord has shown forth his glory:", "second_line": "O come, let us adore him."}

        if self.office.date.primary.name == "All Saints’ Day":
            return {"first_line": "The Lord is glorious in his saints:", "second_line": "O come, let us adore him."}

        if self.office.date.primary.rank.name == "HOLY_DAY" and self.office.date.primary.name not in (
            "The Circumcision and Holy Name of our Lord Jesus Christ",
            "The Visitation of the Virgin Mary to Elizabeth and Zechariah",
            "Holy Cross Day",
            "The Holy Innocents",
        ):
            return {"first_line": "The Lord is glorious in his saints:", "second_line": "O come, let us adore him."}

        if self.office.date.season.name == "Lent" or self.office.date.season.name == "Holy Week":

            return {
                "first_line": "The Lord is full of compassion and mercy:",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.season.name == "Advent":
            return {"first_line": "Our King and Savior now draws near:", "second_line": "O come, let us adore him."}

        if self.office.date.season.name == "Christmastide":
            return {"first_line": "Alleluia, to us a child is born:", "second_line": "O come, let us adore him."}

        if self.office.date.season.name == "Epiphanytide":
            return {"first_line": "The Lord has shown forth his glory:", "second_line": "O come, let us adore him."}

        if self.office.date.season.name == "Eastertide":
            for commemoration in self.office.date.all:
                if "Ascension Day" in commemoration.name:
                    return {
                        "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                        "second_line": "O come, let us adore him.",
                    }

            return {"first_line": "Alleluia. The Lord is risen indeed:", "second_line": "O come, let us adore him."}

        if self.office.date.date.weekday() in [0, 3, 6]:
            return {
                "first_line": "The earth is the Lord’s for he made it: ",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.date.weekday() in [1, 4]:
            return {
                "first_line": "Worship the Lord in the beauty of holiness:",
                "second_line": "O come, let us adore him.",
            }

        if self.office.date.date.weekday() in [2, 5]:
            return {"first_line": "The mercy of the Lord is everlasting: ", "second_line": "O come, let us adore him."}

    def rotating(self):
        if "Easter Day" in self.office.date.primary.name or "Easter Week" in self.office.date.primary.name:
            return ("pascha_nostrum", "pascha_nostrum")

        if self.office.date.season.name == "Eastertide":
            if self.office.date.date.timetuple().tm_yday % 3 == 0:
                return ("pascha_nostrum", "pascha_nostrum")

        if self.office.date.date.timetuple().tm_yday % 2 == 0:
            thirty_day = "jubilate"
            sixty_day = "jubilate"
            if "100" in self.office.office_readings.mp_psalms.split(","):
                sixty_day = "venite"

            if "100" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = "venite"
        else:
            thirty_day = "venite"
            sixty_day = "venite"
            if "95" in self.office.office_readings.mp_psalms.split(","):
                sixty_day = "jubilate"

            if "95" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = "jubilate"

        return (thirty_day, sixty_day)

    def venite_most_days(self):
        if "Easter Day" in self.office.date.primary.name or "Easter Week" in self.office.date.primary.name:
            return ("pascha_nostrum", "pascha_nostrum")

        thirty_day = "venite"
        sixty_day = "venite"

        if "95" in self.office.office_readings.mp_psalms.split(","):
            sixty_day = "jubilate"

        if "95" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
            thirty_day = "jubilate"

        return (thirty_day, sixty_day)

    def jubilate_on_sundays_and_feasts(self):
        if "Easter Day" in self.office.date.primary.name or "Easter Week" in self.office.date.primary.name:
            return ("pascha_nostrum", "pascha_nostrum")

        if self.office.date.season.name == "Eastertide" and self.office.date.primary.rank.name in (
            "PRINCIPAL_FEAST",
            "SUNDAY",
            "HOLY_DAY",
        ):
            return ("pascha_nostrum", "pascha_nostrum")

        if self.office.date.primary.rank.name in ("PRINCIPAL_FEAST", "SUNDAY", "HOLY_DAY"):
            thirty_day = "jubilate"
            sixty_day = "jubilate"

            if "100" in self.office.office_readings.mp_psalms.split(","):
                sixty_day = "venite"
            if "100" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = "venite"
            return (thirty_day, sixty_day)

        thirty_day = "venite"
        sixty_day = "venite"

        if "95" in self.office.office_readings.mp_psalms.split(","):
            sixty_day = "jubilate"

        if "95" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
            thirty_day = "jubilate"

        return (thirty_day, sixty_day)

    def celebratory_always(self):

        if self.office.date.season.name == "Eastertide":
            return ("pascha_nostrum", "pascha_nostrum")

        thirty_day = "jubilate"
        sixty_day = "jubilate"

        if "100" in self.office.office_readings.mp_psalms.split(","):
            sixty_day = "venite"
        if "100" in self.office.thirty_day_psalter_day.mp_psalms.split(","):
            thirty_day = "venite"
        return (thirty_day, sixty_day)

    def get_canticle_filename(self):
        setting = self.office.settings["morning_prayer_invitatory"]
        canticles = self.venite_most_days()
        if setting == "invitatory_jubilate_on_feasts":
            canticles = self.jubilate_on_sundays_and_feasts()
        if setting == "invitatory_rotating":
            canticles = self.rotating()
        if setting == "celebratory_always":
            canticles = self.celebratory_always()

        canticle = canticles[1]
        if self.office.settings["psalter"] == "30":
            canticle = canticles[0]

        lent = self.office.date.season.name == "Lent" or self.office.date.season.name == "Holy Week"
        if canticle == "venite" and lent:
            canticle = "venite_lent"

        return canticle

    def get_lines(self):

        filename = self.get_canticle_filename()
        if filename != "pascha_nostrum":
            return (
                [Line(self.antiphon["first_line"], "leader"), Line(self.antiphon["second_line"])]
                + file_to_lines(filename)
                + [Line(self.antiphon["first_line"], "leader"), Line(self.antiphon["second_line"])]
            )
        return file_to_lines(filename)


class MPPsalms(Module):

    name = "Psalms"

    @staticmethod
    def heading(citations):
        return "The Psalm{} Appointed".format("s" if len(citations) > 1 else "")

    def mass(self):
        pass

    def thirty_days(self):
        from psalter.utils import get_psalms

        psalms = self.office.thirty_day_psalter_day.mp_psalms
        citations = psalms.split(",")
        heading = self.heading(citations)
        psalms = get_psalms(psalms, api=True)

        return [Line(heading, "heading"), Line("Thirty Day Cycle", "subheading")] + psalms

    def sixty_days(self):
        from psalter.utils import get_psalms

        psalms = self.office.office_readings.mp_psalms.split("or")
        if len(psalms) > 1:
            if (self.office.date.date.year % 2) == 0:
                psalms = psalms[0]
            else:
                psalms = psalms[1]
        else:
            psalms = psalms[0]

        citations = psalms.split(",")
        heading = self.heading(citations)
        psalms = get_psalms(psalms, api=True)

        return [Line(heading, "heading"), Line("Sixty Day Cycle", "subheading")] + psalms

    def mass_psalms(self):
        from psalter.utils import get_psalms

        mass_psalm = None
        for reading in self.office.date.mass_readings:
            if reading.reading_type == "psalm":
                mass_psalm = reading.long_citation.replace("Psalms", "").replace("Psalm", "").strip()
                break
        if not mass_psalm:
            return None

        heading = self.heading(mass_psalm)
        psalms = get_psalms(mass_psalm, api=True)
        return [Line(heading, "heading"), Line("Sunday & Holy Day Psalms", "subheading")] + psalms

    def get_lines(self):
        setting = self.office.settings["psalter"]
        lectionary = self.office.settings["lectionary"]
        if lectionary == "mass-readings":
            mass_psalms = self.mass_psalms()
            if mass_psalms:
                return mass_psalms

        if setting == "60":
            return self.sixty_days()
        return self.thirty_days()


class ReadingModule(Module):
    def remove_headings_if_needed(self, text):
        reading_headings = self.office.settings["reading_headings"] == "on"
        if reading_headings:
            return text

        soup = BeautifulSoup(text, "html5lib")
        for h3 in soup.find_all("h3", {"class": "reading-heading"}):
            h3.decompose()
        return str(soup)

    def audio(self, passage, testament):
        if testament == "DC":
            return None
        reading_audio = self.office.settings["reading_audio"] == "on"
        if not reading_audio:
            return None
        passage = quote(passage)
        return '<iframe src="https://www.esv.org/audio-player/{}" style="border: 0; width: 100%; height: 109px;"></iframe>'.format(
            passage
        )

    @staticmethod
    def closing(testament):
        return "The Word of the Lord." if testament != "DC" else "Here ends the Reading."

    @staticmethod
    def closing_response(testament):
        return "Thanks be to God." if testament != "DC" else None

    @cached_property
    def has_mass_reading(self):
        return self.office.date.primary.rank.precedence_rank <= 4

    def get_mass_reading_lines(self, reading):
        text = self.remove_headings_if_needed(reading.long_text)
        lines = [
            Line(reading.long_citation, "subheading"),
            Line(self.audio(reading.long_citation, reading.testament), "html"),
            Line(passage_to_citation(reading.long_citation), "leader"),
            Line(text, "html", "html"),
            Line(self.closing(reading.testament), "leader"),
            Line(self.closing_response(reading.testament), "congregation"),
        ]
        return [line for line in lines if line and line["content"]]

    def get_reading(self, field, abbreviated=False):

        subheading = getattr(self.office.office_readings, field)
        passage = getattr(self.office.office_readings, field)
        citation = passage_to_citation(getattr(self.office.office_readings, field))
        text = getattr(self.office.office_readings, "{}_text".format(field))
        closing = self.closing(getattr(self.office.office_readings, "{}_testament".format(field)))
        closing_response = self.closing_response(getattr(self.office.office_readings, "{}_testament".format(field)))
        testament = getattr(self.office.office_readings, "{}_testament".format(field))

        if abbreviated:
            has_abbreviated = (
                True
                if hasattr(self.office.office_readings, "{}_abbreviated".format(field))
                and getattr(self.office.office_readings, "{}_abbreviated".format(field))
                else False
            )
            if has_abbreviated:
                subheading = getattr(self.office.office_readings, "{}_abbreviated".format(field))
                passage = getattr(self.office.office_readings, "{}_abbreviated".format(field))
                citation = passage_to_citation(getattr(self.office.office_readings, "{}_abbreviated".format(field)))
                text = getattr(self.office.office_readings, "{}_abbreviated_text".format(field))

        text = self.remove_headings_if_needed(text)

        lines = [
            Line(subheading, "subheading"),
            Line(self.audio(passage, testament), "html"),
            Line(citation, "leader"),
            Line(text, "html", "leader"),
            Line(closing, "leader"),
            Line(closing_response, "congregation"),
        ]
        return [line for line in lines if line and line["content"]]

    def get_mass_reading(self, number):
        if not self.has_mass_reading:
            return []
        for reading in self.office.date.mass_readings:
            if reading.reading_number == number:
                return self.get_mass_reading_lines(reading)
        return []

    def abbreviated_mass_reading(self, number):
        if not self.has_mass_reading:
            return []

        for reading in self.office.date.mass_readings:
            if reading.reading_number == number:
                if not reading.short_citation:
                    return self.get_mass_reading(number)
                return self.get_mass_reading_lines(reading)
        return []


class MPFirstReading(ReadingModule):

    name = "First Reading"

    def get_lines(self):
        reading_cycle = self.office.settings["reading_cycle"]
        reading_length = self.office.settings["reading_length"]
        lectionary = self.office.settings["lectionary"]

        if lectionary == "mass-readings" and self.has_mass_reading:
            return (
                self.get_abbreviated_mass_reading(1) if reading_length == "abbreviated" else self.get_mass_reading(1)
            )

        abbreviated = reading_length == "abbreviated"
        if int(reading_cycle) == 2:
            has_alternate_reading = self.office.date.date.year % 2 == 0
            if has_alternate_reading:
                return self.get_reading("ep_reading_1", abbreviated)

        return self.get_reading("mp_reading_1", abbreviated)


class CanticleModule(Module):
    def rubric(self):
        return Line("The following Canticle is sung or said, all standing", line_type="rubric")

    def gloria_lines(self, data):
        if not data.gloria:
            return []
        return [
            Line(
                "Glory be to the Father, and to the Son, and to the Holy Spirit; *",
                line_type="congregation",
                indented=False,
            ),
            Line("as it was in the beginning, is now, and ever shall be,", line_type="congregation", indented=True),
            Line("world without end. Amen.", line_type="congregation", indented=True),
        ]

    def get_canticle(self, data):
        return (
            [
                Line(data.latin_name, "heading"),
                Line(data.english_name, "subheading"),
                self.rubric(),
            ]
            + file_to_lines(data.template.replace("html", "csv"))
            + [
                Line(data.citation, "citation"),
            ]
            + self.gloria_lines(data)
        )


class MPFirstCanticle(CanticleModule):

    name = "First Canticle"

    def get_lines(self):

        rotation = self.office.settings["canticle_rotation"]

        if rotation == "1979":
            data = BCP1979CanticleTable().get_mp_canticle_1(self.office.date)
        elif rotation == "2011":
            data = REC2011CanticleTable().get_mp_canticle_1(self.office.date)
        else:
            data = DefaultCanticles().get_mp_canticle_1(self.office.date)
        return self.get_canticle(data)


class MorningPrayer(Office):
    def get_modules(self):
        return [
            MPOpeningSentence(self),
            Confession(self),
            Preces(self),
            MPInvitatory(self),
            MPPsalms(self),
            MPFirstReading(self),
            MPFirstCanticle(self),
        ]


class OfficeAPIView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        raise NotImplementedError("You must implement this method.")


class OfficeSerializer(serializers.Serializer):
    calendar_day = DaySerializer(source="date")
    modules = serializers.SerializerMethodField()

    def get_modules(self, obj):
        return {"data": [module.json for module in obj.get_modules()]}


class MorningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = MorningPrayer(request, year, month, day)
        serializer = OfficeSerializer(office)
        return Response(serializer.data)

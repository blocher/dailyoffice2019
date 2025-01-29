import csv
import datetime
import json
import os
from collections import defaultdict
from urllib.parse import quote

import mailchimp_marketing as MailchimpMarketing
from distutils.util import strtobool
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Prefetch
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateResponseMixin
from mailchimp_marketing.api_client import ApiClientError
from rest_framework import serializers, mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_church_year
from office.api.serializers import UpdateNoticeSerializer
from office.api.views import Module, Line
from office.api.views.ep import EPOpeningSentence
from office.canticles import DefaultCanticles, BCP1979CanticleTable, REC2011CanticleTable, EP2, EP1, S8
from office.models import (
    UpdateNotice,
    HolyDayOfficeDay,
    StandardOfficeDay,
    ThirtyDayPsalterDay,
    Setting,
    SettingOption,
    Collect,
    Scripture,
)
from office.utils import passage_to_citation, get_client_ip, generate_uuid_from_string
from psalter.utils import get_psalms


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


class Collects:
    pass


class Settings(dict):
    def __init__(self, request):
        settings = self._get_settings(request)
        settings["extra_collects"] = self._get_extra_collects(request)
        super().__init__(**settings)

    def _default_settings(self):
        settings = (
            Setting.objects.order_by("site", "setting_type", "order")
            .prefetch_related(
                Prefetch("settingoption_set", queryset=SettingOption.objects.order_by("order"), to_attr="options")
            )
            .all()
        )
        defaults = {setting.name: setting.options[0].value for setting in settings}
        return defaults

    def _get_extra_collects(self, request):
        try:
            extra_collects = request.query_params.get("extra_collects", "")
            if not extra_collects:
                return []
            extra_collects = extra_collects.split(",")
            if not extra_collects:
                return []
            extra_collects = Collect.objects.filter(pk__in=extra_collects).all()
        except:
            return []
        return extra_collects

    def _get_settings(self, request):
        settings = self._default_settings().copy()
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
# leader_dialogue
# congregation_dialogue


def file_to_lines(filename):
    def process_row(row):
        result = {"content": row[0]}
        if len(row) > 1 and row[1]:
            result["line_type"] = row[1]
        result["indented"] = False
        if len(row) > 2:
            if row[2].lower() == "true":
                result["indented"] = "indent"
            else:
                result["indented"] = row[2]

        if len(row) > 3:
            if not row[3]:
                result["extra_space_before"] = False
            else:
                result["extra_space_before"] = bool(strtobool(row[3].lower()))
        return result

    filename = "{}.csv".format(filename.replace(".csv", ""))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open("{}/../texts/{}".format(dir_path, filename), encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL, skipinitialspace=True)
        return [Line(**process_row(row)) for row in reader]


class MPOpeningSentence(Module):
    name = "Opening Sentence"

    def get_sentence(self):
        if "Thanksgiving Day" in self.office.date.primary.name:
            return {
                "sentence": "Honor the Lord with your wealth and with the firstfruits of all your produce; then your barns will be filled with plenty, and your vats will be bursting with wine.",
                "traditional": "Honor the Lord with thy substance, and with the firstfruits of all thine increase: So shall thy barns be filled with plenty, and thy presses shall burst out with new wine.",
                "citation": "PROVERBS 3:9-10",
            }

        if self.office.date.season.name == "Holy Week":
            return {
                "sentence": "Is it nothing to you, all you who pass by? Look and see if there is any sorrow like my sorrow, which was brought upon me, which the Lord inflicted on the day of his fierce anger.",
                "traditional": "Is it nothing to you, all ye that pass by? Behold, and see if there be any sorrow like unto my sorrow, which is done unto me, wherewith the Lord hath afflicted me in the day of his fierce anger.",
                "citation": "LAMENTATIONS 1:12",
            }

        if (
            self.office.date.season.name == "Lent"
            or self.office.date.primary.rank.name == "EMBER_DAY"
            or self.office.date.primary.rank.name == "ROGATION_DAY"
        ):
            if self.office.date.date.weekday() in [6, 2]:  # Sunday, Wednesday
                return {
                    "sentence": "Repent, for the kingdom of heaven is at hand.",
                    "traditional": "Repent ye: for the kingdom of heaven is at hand.",
                    "citation": "MATTHEW 3:2",
                }

            if self.office.date.date.weekday() in [0, 3, 5]:  # Monday, Thursday, Saturday
                return {
                    "sentence": "Turn your face from my sins, and blot out all my misdeeds.",
                    "traditional": "Turn thy face from my sins, and put out all my misdeeds.",
                    "citation": "PSALM 51:9",
                }

            return {
                "sentence": "If anyone would come after me, let him deny himself and take up his cross and follow me.",
                "traditional": "Whosoever will come after me, let him deny himself, and take up his cross, and follow me.",
                "citation": "MARK 8:34",
            }

        if self.office.date.season.name == "Advent":
            return {
                "sentence": "In the wilderness prepare the way of the Lord; make straight in the desert a highway for our God.",
                "traditional": "Prepare ye the way of the Lord, make straight in the desert a highway for our God.",
                "citation": "ISAIAH 40:3",
            }

        if self.office.date.season.name == "Christmastide":
            return {
                "sentence": "Fear not, for behold, I bring you good news of great joy that will be for all the people. For unto you is born this day in the city of David a Savior, who is Christ the Lord.",
                "traditional": "Fear not: for, behold, I bring you good tidings of great joy, which shall be to all people. For unto you is born this day in the city of David a Savior, which is Christ the Lord.",
                "citation": "LUKE 2:10-11",
            }

        if self.office.date.season.name == "Epiphanytide":
            return {
                "sentence": "From the rising of the sun to its setting my name will be great among the nations, and in every place incense will be offered to my name, and a pure offering. For my name will be great among the nations, says the Lord of hosts.",
                "traditional": "For from the rising of the sun even unto the going down of the same my name shall be great among the Gentiles; and in every place incense shall be offered unto my name, and a pure offering: for my name shall be great among the heathen, saith the Lord of hosts.",
                "citation": "MALACHI 1:11",
            }

        if (
            "Ascension" in self.office.date.primary.name
            or len(self.office.date.all) > 1
            and "Ascension" in self.office.date.all[1].name
        ):
            return {
                "sentence": "Since then we have a great high priest who has passed through the heavens, Jesus, the Son of God, let us hold fast our confession. Let us then with confidence draw near to the throne of grace, that we may receive mercy and find grace to help in time of need.",
                "traditional": "Seeing then that we have a great high priest, that is passed into the heavens, Jesus the Son of God, let us hold fast our profession. Let us therefore come boldly unto the throne of grace, that we may obtain mercy, and find grace to help in time of need.",
                "citation": "HEBREWS 4:14, 16",
            }

        if self.office.date.primary.name == "The Day of Pentecost":
            return {
                "sentence": "You will receive power when the Holy Spirit has come upon you, and you will be my witnesses in Jerusalem and in all Judea and Samaria, and to the end of the earth.",
                "traditional": "Ye shall receive power, after that the Holy Ghost is come upon you: and ye shall be witnesses unto me both in Jerusalem, and in all Judaea, and in Samaria, and unto the uttermost part of the earth.",
                "citation": "ACTS 1:8",
            }

        if self.office.date.primary.name == "Trinity Sunday":
            return {
                "sentence": "Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!",
                "traditional": "Holy, holy, holy, is the Lord God Almighty, which was, and is, and is to come.",
                "citation": "REVELATION 4:8",
            }

        if self.office.date.season.name == "Eastertide":
            return {
                "sentence": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God.",
                "traditional": "If ye then be risen with Christ, seek those things which are above, where Christ sitteth on the right hand of God.",
                "citation": "COLOSSIANS 3:1",
            }

        if self.office.date.date.weekday() == 6:
            return {
                "sentence": "Grace to you and peace from God our Father and the Lord Jesus Christ.",
                "traditional": "Grace be unto you and peace, from God our Father, and from the Lord Jesus Christ.",
                "citation": "PHILIPPIANS 1:2",
            }

        if self.office.date.date.weekday() == 0:
            return {
                "sentence": "I was glad when they said unto me, “We will go into the house of the Lord.",
                "traditional": "I was glad when they said unto me, We will go into the house ofthe Lord.",
                "citation": "PSALM 122:1",
            }

        if self.office.date.date.weekday() == 1:
            return {
                "sentence": "Let the words of my mouth and the meditation of my heart be always acceptable in your sight, O Lord, my rock and my redeemer.",
                "traditional": "Let the words of my mouth, and the meditation of my heart, be alway acceptable in your sight, O Lord, my strength and my redeemer.",
                "citation": "PSALM 19:14",
            }

        if self.office.date.date.weekday() == 2:
            return {
                "sentence": "The Lord is in his holy temple; let all the earth keep silence before him.",
                "traditional": "The Lord is in his holy temple: let all the earth keep silence before him.",
                "citation": "HABAKKUK 2:20",
            }

        if self.office.date.date.weekday() == 3:
            return {
                "sentence": "O send out your light and your truth, that they may lead me, and bring me to your holy hill, and to your dwelling.",
                "traditional": "O send out thy light and thy truth, that they may lead me, and bring me unto thy holy hill, and to thy dwelling",
                "citation": "PSALM 43:3",
            }

        if self.office.date.date.weekday() == 4:
            return {
                "sentence": "Thus says the One who is high and lifted up, who inhabits eternity, whose name is Holy: “I dwell in the high and holy place, and also with him who is of a contrite and lowly spirit, to revive the spirit of the lowly, and to revive the heart of the contrite.”",
                "traditional": "Thus saith the high and lofty One that inhabiteth eternity, whose name is Holy; I dwell in the high and holy place, with him also that is of a contrite and humble spirit, to revive the spirit of the humble, and to revive the heart of the contrite ones.",
                "citation": "ISAIAH 57:15",
            }

        if self.office.date.date.weekday() == 5:
            return {
                "sentence": "The hour is coming, and is now here, when the true worshipers will worship the Father in spirit and truth, for the Father is seeking such people to worship him.",
                "traditional": "The hour cometh, and now is, when the true worshipers shall worship the Father in spirit and in truth: for the Father seeketh such to worship him.",
                "citation": "JOHN 4:23",
            }

    def get_lines(self):
        sentence = self.get_sentence()
        style = self.office.settings["language_style"]
        return [
            Line("Opening Sentence", "heading"),
            Line(sentence["traditional"] if style == "traditional" else sentence["sentence"], "leader"),
            Line(sentence["citation"], "citation"),
        ]


class Office(object):
    tag = "office"

    def __init__(self, request, year, month, day):
        from churchcal.calculations import get_calendar_date

        self.settings = Settings(request)

        self.date = get_calendar_date("{}-{}-{}".format(year, month, day))

        try:
            self.office_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except (HolyDayOfficeDay.DoesNotExist, ValueError):
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)

    @cached_property
    def readings(self):
        passages = Scripture.objects.filter(
            passage__in=[
                self.office_readings.mp_reading_1,
                self.office_readings.mp_reading_1_abbreviated,
                self.office_readings.mp_reading_2,
                self.office_readings.ep_reading_1,
                self.office_readings.ep_reading_1_abbreviated,
                self.office_readings.ep_reading_2,
            ]
        ).all()
        return {passage.passage: passage for passage in passages if passage}

    def get_modules(self):
        raise NotImplementedError("You must implement this method.")


class Confession(Module):
    name = "Confession of Sin"

    def get_intro_lines(self):
        language_style = self.office.settings["language_style"]
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return (
                file_to_lines("confession_intro_long_traditional") + [Line("", "spacer")]
                if language_style == "traditional"
                else file_to_lines("confession_intro_long") + [Line("", "spacer")]
            )
        return file_to_lines("confession_intro_short") + [Line("", "spacer")]

    def get_body_lines(self):
        language_style = self.office.settings["language_style"]
        return (
            file_to_lines("confession_body_traditional")
            if language_style == "traditional"
            else file_to_lines("confession_body")
        )

    def get_absolution_lines(self):
        language_style = self.office.settings["language_style"]
        lay = self.office.settings["absolution"] == "lay"
        if lay:
            return (
                file_to_lines("confession_absolution_lay_traditional")
                if language_style == "traditional"
                else file_to_lines("confession_absolution_lay")
            )
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return (
                file_to_lines("confession_absolution_long_traditional")
                if language_style == "traditional"
                else file_to_lines("confession_absolution_long")
            )
        return (
            file_to_lines("confession_absolution_short_traditional")
            if language_style == "traditional"
            else file_to_lines("confession_absolution_short")
        )

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
        language_style = self.office.settings["language_style"]
        file = "preces_traditional" if language_style == "traditional" else "preces"
        return file_to_lines(file)


class MPInvitatory(Module):
    name = "Invitatory"

    @cached_property
    def antiphon(self):
        if "Presentation" in self.office.date.primary.name or "Annunciation" in self.office.date.primary.name:
            return {
                "first_line": "The Word was made flesh and dwelt among us:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Word was made flesh and dwelt among us: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "The Day of Pentecost":
            return {
                "first_line": "Alleluia. The Spirit of the Lord renews the face of the earth:",
                "second_line": "O come, let us adore him. Alleluia.",
                "first_line_traditional": "Alleluia. The Spirit of the Lord filleth the world: *",
                "second_line_traditional": "O come, let us adore him. Alleluia.",
            }

        if self.office.date.primary.name == "Trinity Sunday":
            return {
                "first_line": "Father, Son, and Holy Spirit, one God:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "Father, Son, and Holy Ghost, one God: * ",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "Easter Day":
            return {
                "first_line": "Alleluia. The Lord is risen indeed:",
                "second_line": "O come, let us adore him. Alleluia.",
                "first_line_traditional": "Alleluia. The Lord is risen indeed: *",
                "second_line_traditional": "O come, let us adore him. Alleluia.",
            }

        if (
            "Ascension" in self.office.date.primary.name
            or len(self.office.date.all) > 1
            and "Ascension" in self.office.date.all[1].name
        ):
            return {
                "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                "second_line": "O come, let us adore him. Alleluia.",
                "first_line_traditional": "Alleluia. Christ the Lord ascendeth into heaven: *",
                "second_line_traditional": "O come, let us adore him. Alleluia.",
            }

        if self.office.date.primary.name == "The Transfiguration of Our Lord Jesus Christ":
            return {
                "first_line": "The Lord has shown forth his glory:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Lord hath manifested forth his glory:",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.primary.name == "All Saints’ Day":
            return {
                "first_line": "The Lord is glorious in his saints:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Lord hath manifested forth his glory: * ",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.primary.rank.name == "HOLY_DAY" and self.office.date.primary.name not in (
            "The Circumcision and Holy Name of our Lord Jesus Christ",
            "The Visitation of the Virgin Mary to Elizabeth and Zechariah",
            "Holy Cross Day",
            "The Holy Innocents",
        ):
            return {
                "first_line": "The Lord is glorious in his saints:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Lord is glorious in his saints: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.season.name == "Lent" or self.office.date.season.name == "Holy Week":
            return {
                "first_line": "The Lord is full of compassion and mercy:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Lord is full of compassion and mercy: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.season.name == "Advent":
            return {
                "first_line": "Our King and Savior now draws near:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "Our King and Savior draweth nigh: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.season.name == "Christmastide":
            return {
                "first_line": "Alleluia, to us a child is born:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "Alleluia, unto us a child is born: *",
                "second_line_traditional": "O come, let us adore him. Alleluia.",
            }

        if self.office.date.season.name == "Epiphanytide":
            return {
                "first_line": "The Lord has shown forth his glory:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The Lord hath manifested forth his glory: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.season.name == "Eastertide":
            for commemoration in self.office.date.all:
                if "Ascension Day" in commemoration.name:
                    return {
                        "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                        "second_line": "O come, let us adore him.",
                        "first_line_traditional": "Alleluia. Christ the Lord ascendeth into heaven: *",
                        "second_line_traditional": "O come, let us adore him. Alleluia.",
                    }

            return {
                "first_line": "Alleluia. The Lord is risen indeed:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "Alleluia. The Lord is risen indeed: *",
                "second_line_traditional": "O come, let us adore him. Alleluia.",
            }

        if self.office.date.date.weekday() in [0, 3, 6]:
            return {
                "first_line": "The earth is the Lord’s for he made it: ",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The earth is the Lord’s for he made it: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.date.weekday() in [1, 4]:
            return {
                "first_line": "Worship the Lord in the beauty of holiness:",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "Worship the Lord in the beauty of holiness: *",
                "second_line_traditional": "O come, let us adore him.",
            }

        if self.office.date.date.weekday() in [2, 5]:
            return {
                "first_line": "The mercy of the Lord is everlasting: ",
                "second_line": "O come, let us adore him.",
                "first_line_traditional": "The mercy of the Lord is everlasting: *",
                "second_line_traditional": "O come, let us adore him.",
            }

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
        language_style = self.office.settings["language_style"]
        if language_style == "traditional":
            filename += "_traditional"
        if filename != "pascha_nostrum":
            first_line_field = "first_line_traditional" if language_style == "traditional" else "first_line"
            second_line_field = "second_line_traditional" if language_style == "traditional" else "second_line"
            canticle = file_to_lines(filename)
            canticle_heading = canticle[:3]
            canticle_body = canticle[3:]
            return (
                canticle_heading
                + [Line(self.antiphon[first_line_field], "leader"), Line(self.antiphon[second_line_field])]
                + canticle_body
                + [Line(self.antiphon[first_line_field], "leader"), Line(self.antiphon[second_line_field])]
            )
        return file_to_lines(filename)


class EPInvitatory(Module):
    def get_lines(self):
        language_style = self.office.settings["language_style"]
        file = "phos_hilaron_traditional" if language_style == "traditional" else "phos_hilaron"
        return file_to_lines(file)


class ReadingModule(Module):
    def remove_headings_if_needed(self, text):
        reading_headings = self.office.settings["reading_headings"] == "on"
        if reading_headings:
            return text

        return Scripture.no_headings(text)

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
        translation = self.office.settings["bible_translation"]
        abbreviated = self.office.settings["reading_length"] == "abbreviated"
        if abbreviated or not reading.short_text:
            text = Scripture.objects.get(passage=reading.long_citation)
            citation = reading.long_citation
        else:
            text = Scripture.objects.get(passage=reading.short_citation)
            citation = reading.short_citation

        text = getattr(text, translation)
        text = self.remove_headings_if_needed(text)
        text = GenericDailyOfficeSerializer.handle_html(text, html=True, no_generate=True)

        lines = [
            Line(citation, "subheading"),
            Line(self.audio(citation, reading.testament), "html"),
            Line(passage_to_citation(citation), "leader"),
            Line("", "spacer"),
            Line(text, "html", "leader"),
            Line("", "spacer"),
            Line(self.closing(reading.testament), "leader"),
            Line(self.closing_response(reading.testament), "congregation"),
        ]
        return [line for line in lines if line and (line["content"] or line["line_type"] == "spacer")]

    def get_reading(self, field, abbreviated=False, translation="esv", text_only=False):
        subheading = getattr(self.office.office_readings, field)
        passage = getattr(self.office.office_readings, field)
        citation = passage_to_citation(getattr(self.office.office_readings, field))
        text_obj = self.office.readings[passage]
        text = getattr(text_obj, translation)
        if text in ["-", "<html><head></head><body>-</body></html>", ""]:
            text = getattr(text_obj, "nrsvce")
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
                text = self.office.readings[passage]
                text = getattr(text, translation)
                if text in ["-", "<html><head></head><body>-</body></html>"]:
                    text = getattr(text_obj, "nrsvce")

        text = self.remove_headings_if_needed(text)

        text = GenericDailyOfficeSerializer.handle_html(
            text, html=True, no_generate=True, id=f"{self.get_safe_name()}_ad0aad27-4e5d-5ce3-8947-2bef1e5a5586"
        )

        if text_only:
            return text

        lines = [
            Line(subheading, "subheading"),
            Line(self.audio(passage, testament), "html"),
            Line(citation, "reader"),
            Line("", "spacer"),
            Line(
                text,
                "html",
            ),
            Line("", "spacer"),
            Line(closing, "reader"),
            Line(closing_response, "congregation"),
        ]
        return [line for line in lines if line and (line["content"] or line["line_type"] == "spacer")]

    def get_mass_reading(self, number):
        if not self.has_mass_reading:
            return []
        number = number + 1 if number > 1 else number
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

    def get_lines_for_reading(self, office="mp", number=1):
        reading_cycle = self.office.settings["reading_cycle"]
        reading_length = self.office.settings["reading_length"]
        lectionary = self.office.settings["lectionary"]
        translation = self.office.settings["bible_translation"]
        if lectionary == "mass-readings" and self.has_mass_reading:
            return (
                self.abbreviated_mass_reading(number)
                if reading_length == "abbreviated"
                else self.get_mass_reading(number)
            )

        if number > 2:
            return None

        abbreviated = reading_length == "abbreviated"
        if int(reading_cycle) == 2:
            office = "ep" if self.office.date.date.year % 2 == 0 else "mp"

        reading_field = "{}_reading_{}".format(office, number)
        return self.get_reading(reading_field, abbreviated, translation)


class MPFirstReading(ReadingModule):
    name = "First Reading"

    def get_lines(self):
        reading_heading = [Line("The First Lesson", line_type="heading")]
        return reading_heading + self.get_lines_for_reading("mp", 1)


class EPFirstReading(ReadingModule):
    name = "First Reading"

    def get_lines(self):
        reading_heading = [Line("The First Lesson", line_type="heading")]
        return reading_heading + self.get_lines_for_reading("ep", 1)


class CanticleModule(Module):
    def get_antiphon(self):
        if self.office.date.date.month != 12:
            return None
        antiphon_style = self.office.settings.get("o_antiphons", "hymn")
        if antiphon_style == "paraphrase":
            antiphon_style = "hymn"
        if antiphon_style == "literal":
            antiphon_style = "english"
        if antiphon_style not in ["latin", "english", "hymn", "none"]:
            antiphon_style = "hymn"
        if antiphon_style == "none":
            return ""
        antiphons = {
            "16": {
                "latin": "O Sapientia, quae ex ore Altissimi prodiisti, attingens a fine usque ad finem, fortiter suaviterque disponens omnia: veni ad docendum nos viam prudentiae.",
                "english": "O Wisdom, who came from the mouth of the Most High, reaching from end to end and ordering all things mightily and sweetly: come, and teach us the way of prudence.",
                "hymn": "O come, thou Wisdom from on high who orderest all things mightily; to us the path of knowledge show, and teach us in her ways to go. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:2-3, 28:29",
            },
            "17": {
                "latin": "O Adonai, et Dux domus Israel, qui Moysi in igne flammae rubi apparuisti, et ei in Sina legem dedisti: veni ad redimendum nos in brachio extento.",
                "english": "O Lord and Ruler of the house of Israel, who appeared to Moses in the flame of the burning bush and gave him the law on Sinai: come, and redeem us with outstretched arms.",
                "hymn": "O come, O come, thou Lord of might, who to thy tribes on Sinai's height in ancient times didst give the law, in cloud, and majesty, and awe. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:4-5, 33:22",
            },
            "18": {
                "latin": "O Radix Jesse, qui stas in signum populorum, super quem continebunt reges os suum, quem Gentes deprecabuntur: veni ad liberandum nos, jam noli tardare.",
                "english": "O Root of Jesse, that stands for an ensign of the people, before whom the kings keep silence and unto whom the Gentiles shall make supplication: come, to deliver us, and tarry not.",
                "hymn": "O come, through Branch of Jesse's tree, free them from Satan's tyranny that trust thy mighty power to save, and give them victory oer' the grave. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:1, 10",
            },
            "19": {
                "latin": "O clavis David, et sceptrum domus Israel: qui aperis, et nemo claudit; claudis, et nemo aperit: veni, et educ vinctum de domo carceris, sedentem in tenebris.",
                "english": "O Key of David, and scepter of the house of Israel, who opens and no man shuts, who shuts and no man opens: come, and lead forth the captive who sits in the shadows from his prison.",
                "hymn": "O come, though Key of David, come, and open wide our heavenly home; make safe the way that leads on high, and close the path to misery. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 9:6, 22:22.",
            },
            "20": {
                "latin": "O Oriens, splendor lucis æternæ, et sol justitiæ: veni, et illumina sedentes in tenebris, et umbra mortis.",
                "english": "O dawn of the east, brightness of light eternal, and sun of justice: come, and enlighten those who sit in darkness and in the shadow of death.",
                "hymn": "O come, thou Dayspring from on high, and cheer us by thy drawing night; disperse the gloomy clouds of night, and death's dark shadow put to flight. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 9:2",
            },
            "21": {
                "latin": "O Rex Gentium, et desideratus earum, lapisque angularis, qui facis utraque unum: veni, et salva hominem, quem de limo formasti.",
                "english": "O King of the gentiles and their desired One, the cornerstone that makes both one: come, and deliver man, whom you formed out of the dust of the earth.",
                "hymn": "O come, Desire of nations, bind in one the hearts of all mankind; bid thou our sad divisions cease, and be thyself our King of Peace. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 2:4, 9:7",
            },
            "22": {
                "latin": "O Emmanuel, Rex et legifer noster, exspectatio gentium, et Salvator earum: veni ad salvandum nos Domine Deus noster.",
                "english": "O Emmanuel, God with us, our King and lawgiver, the expected of the nations and their Savior: come to save us, O Lord our God.",
                "hymn": "O come, O come, Emmanuel, and ransom captive Israel, that mourns in lonley exile here until the Sod of God appear. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 7:14",
            },
            "23": {
                "latin": "O Virgo virginum, quomodo fiet istud? Quia nec primam similem visa es nec habere sequentem. Filiae Jerusalem, quid me admiramini? Divinum est mysterium hoc quod cernitis.",
                "english": "O Virgin of virgins, how shall this be? For neither before you was any like you, nor shall there be after. Daughters of Jerusalem, why do you marvel at me? The thing which you behold is a divine mystery.",
                "hymn": "O Virgin great! How shall this be? For none before nor hence were like to thee; Why, Salem’s daughters, marvel ye? Behold, a heav’nly mystery! Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "",
            },
        }

        index = str(self.office.date.date.day)
        try:
            return antiphons[index][antiphon_style]
        except KeyError:
            return None

    def rubric(self):
        return Line("The following Canticle is sung or said, all standing", line_type="rubric")

    def gloria_lines(self, data, as_psalm=False):
        if as_psalm or not data.gloria:
            return []
        language_style = self.office.settings["language_style"]
        file = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        return file_to_lines(file)

    def get_canticle(self, data, antiphon=False, as_psalm=False):
        # check if data is a tuple
        if isinstance(data, tuple):
            psalter = self.office.settings["psalter"]
            if str(psalter) == "30":
                data = data[0]
            else:
                data = data[1]
        language_style = self.office.settings["language_style"]
        template = data.template.replace("html", "csv")
        if language_style == "traditional":
            template = template.replace(".csv", "_traditional.csv")

        if antiphon:
            antiphon = self.get_antiphon()
            if antiphon:
                return (
                    [
                        Line(data.latin_name, "heading"),
                        Line(data.english_name, "subheading"),
                        self.rubric(),
                    ]
                    + [Line(antiphon, "congregation")]
                    + [Line("", "spacer")]
                    + file_to_lines(template)
                    + [
                        Line(data.citation, "citation"),
                    ]
                    + self.gloria_lines(data, as_psalm=as_psalm)
                    + [Line("", "spacer")]
                    + [Line(antiphon, "congregation")]
                )
        return (
            [
                Line("The Psalms or Canticle Appointed", "heading") if as_psalm else Line(""),
                Line(data.latin_name, "heading" if not as_psalm else "subheading"),
                Line(data.english_name, "subheading"),
                self.rubric(),
            ]
            + file_to_lines(template)
            + [
                Line(data.citation, "citation"),
            ]
            + self.gloria_lines(data, as_psalm=as_psalm)
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


class MPPsalms(CanticleModule, ReadingModule):
    name = "Psalms"
    attribute = "mp_psalms"

    @staticmethod
    def heading(citations):
        return "The Psalm{} Appointed".format("s" if len(citations) > 1 else "")

    def mass(self):
        pass

    def thirty_days(self):
        from psalter.utils import get_psalms

        psalms = getattr(self.office.thirty_day_psalter_day, self.attribute)
        citations = psalms.split(",")
        heading = self.heading(citations)
        language_style = self.office.settings["psalm_translation"]
        psalm_style = self.office.settings["psalm_style"]
        psalms = get_psalms(psalms, api=True, language_style=language_style, headings=psalm_style)

        return [Line(heading, "heading"), Line("Thirty Day Cycle", "subheading")] + psalms

    def sixty_days(self):
        from psalter.utils import get_psalms

        psalms = getattr(self.office.office_readings, self.attribute)
        psalms = psalms.split("or")

        if len(psalms) > 1:
            if (self.office.date.date.year % 2) == 0:
                psalms = psalms[0]
            else:
                psalms = psalms[1]
        else:
            psalms = psalms[0]

        citations = psalms.split(",")
        heading = self.heading(citations)
        language_style = self.office.settings["psalm_translation"]
        psalm_style = self.office.settings["psalm_style"]
        psalms = get_psalms(psalms, api=True, language_style=language_style, headings=psalm_style)

        return [Line(heading, "heading"), Line("Sixty Day Cycle", "subheading")] + psalms

    def mass_psalms(self):
        from psalter.utils import get_psalms

        mass_psalm = None
        for reading in self.office.date.mass_readings:
            if reading.reading_type == "psalm":
                if reading.long_citation == "ISAIAH 12:2-6":
                    return self.get_canticle(S8(), as_psalm=True)
                if reading.long_citation == "LUKE 1:46-55":
                    return self.get_canticle(EP1(), as_psalm=True)
                if "Psalm" not in reading.long_citation:
                    return [Line(reading.long_text, "html")]
                mass_psalm = reading.long_citation.replace("Psalms", "").replace("Psalm", "").strip()
                break
        if not mass_psalm:
            return None

        heading = self.heading(mass_psalm)
        language_style = self.office.settings["psalm_translation"]
        psalm_style = self.office.settings["psalm_style"]
        psalms = get_psalms(mass_psalm, api=True, language_style=language_style, headings=psalm_style)
        return [Line(heading, "heading"), Line("Sunday & Holy Day Psalms", "subheading")] + psalms

    def get_psalm_lines(self):
        setting = self.office.settings["psalter"]
        lectionary = self.office.settings["lectionary"]
        if lectionary == "mass-readings" and self.has_mass_reading:
            mass_psalms = self.mass_psalms()
            if mass_psalms:
                return mass_psalms

        if setting == "60":
            return self.sixty_days()
        return self.thirty_days()

    def gloria_patri(self):
        language_style = self.office.settings["language_style"]
        file = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        return [Line("", "spacer")] + file_to_lines(file)

    def get_lines(self):
        return self.get_psalm_lines() + self.gloria_patri()


class EPPsalms(MPPsalms):
    attribute = "ep_psalms"


class EPFirstCanticle(CanticleModule):
    name = "First Canticle"

    def get_lines(self):
        rotation = self.office.settings["canticle_rotation"]

        if rotation == "1979":
            cant2 = BCP1979CanticleTable().get_ep_canticle_2(self.office.date)
            data = BCP1979CanticleTable().get_ep_canticle_1(self.office.date)
        elif rotation == "2011":
            cant2 = REC2011CanticleTable().get_ep_canticle_2(self.office.date, self.office.office_readings)
            data = REC2011CanticleTable().get_ep_canticle_1(self.office.date)
        else:
            cant2 = DefaultCanticles().get_ep_canticle_2(self.office.date)
            data = DefaultCanticles().get_ep_canticle_1(self.office.date)
        antiphon = False
        if data.latin_name.lower() == "magnificat":
            antiphon = True
        elif cant2.latin_name.lower() != "magnificat":
            antiphon = True
        return self.get_canticle(data, antiphon=antiphon)


class MPSecondCanticle(CanticleModule):
    name = "Second Canticle"

    def get_lines(self):
        rotation = self.office.settings["canticle_rotation"]

        if rotation == "1979":
            data = BCP1979CanticleTable().get_mp_canticle_2(self.office.date)
        elif rotation == "2011":
            data = REC2011CanticleTable().get_mp_canticle_2(self.office.date)
        else:
            data = DefaultCanticles().get_mp_canticle_2(self.office.date)
        return self.get_canticle(data)


class EPSecondCanticle(CanticleModule):
    name = "Second Canticle"

    def get_lines(self):
        rotation = self.office.settings["canticle_rotation"]
        if rotation == "1979":
            data = BCP1979CanticleTable().get_ep_canticle_2(self.office.date)
        elif rotation == "2011":
            data = REC2011CanticleTable().get_ep_canticle_2(self.office.date, self.office.office_readings)
        else:
            data = DefaultCanticles().get_ep_canticle_2(self.office.date)
        antiphon = False
        if not isinstance(data, tuple) and data.latin_name.lower() == "magnificat":
            antiphon = True
        return self.get_canticle(data, antiphon=antiphon)


class MPSecondReading(ReadingModule):
    name = "Second Reading"

    def get_lines(self):
        reading_heading = [Line("The Second Lesson", line_type="heading")]
        return reading_heading + self.get_lines_for_reading("mp", 2)


class EPSecondReading(ReadingModule):
    name = "Second Reading"

    def get_lines(self):
        reading_heading = [Line("The Second Lesson", line_type="heading")]
        return reading_heading + self.get_lines_for_reading("ep", 2)


class MPThirdReading(ReadingModule):
    name = "Third Reading"

    def get_lines(self):
        if not self.has_mass_reading:
            return None

        reading_heading = [Line("The Third Lesson", line_type="heading")]
        lines = self.get_lines_for_reading("mp", 3)
        if lines:
            return reading_heading + lines
        return None


class EPThirdReading(ReadingModule):
    name = "Third Reading"

    def get_lines(self):
        if not self.has_mass_reading:
            return None

        reading_heading = [Line("The Third Lesson", line_type="heading")]
        lines = self.get_lines_for_reading("ep", 3)
        if lines:
            return reading_heading + lines
        return None


class Creed(Module):
    name = "The Apostle's Creed"

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        file = "creed_traditional" if language_style == "traditional" else "creed"
        return [
            Line("The Apostles' Creed", "heading"),
            Line("Officiant and People together, all standing", "rubric"),
        ] + file_to_lines(file)


class Prayers(Module):
    name = "The Prayers"

    def add_names(self, suffrages):
        names = self.get_names()
        for line in suffrages:
            line["content"] = line["content"].replace("[ ___________ ]", names)
        return suffrages

    def get_names(self):
        names = [
            feast.saint_name
            for feast in self.office.date.all_evening
            if hasattr(feast, "saint_name") and feast.saint_name
        ]
        names = ["the Blessed Virgin Mary"] + names
        num_names = len(names)
        names = ", ".join(names)
        if num_names > 1:
            names = names + ","
        return names

    def get_suffrages_file_name(self):
        language_style = self.office.settings["language_style"]
        if type(self.office) == MorningPrayer:
            return "suffrages_a_traditional" if language_style == "traditional" else "suffrages_a"
        suffrages_style = self.office.settings["suffrages"]
        if suffrages_style == "traditional":
            suffrages_file = "suffrages_a.csv"
        elif suffrages_style == "new":
            suffrages_file = "suffrages_b.csv"
        else:
            if self.office.date.date.timetuple().tm_yday % 2:
                suffrages_file = "suffrages_b.csv"
            else:
                suffrages_file = "suffrages_a.csv"
        return f"{suffrages_file}_traditional" if language_style == "traditional" else suffrages_file

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        our_father_style = self.office.settings["language_style_for_our_father"]
        if language_style == "traditional" or our_father_style == "traditional":
            kyrie_file = "kyrie_traditional.csv"
            pater_file = "pater_traditional.csv"
        else:
            kyrie_file = "kyrie_contemporary.csv"
            pater_file = "pater_contemporary.csv"

        pronoun = "thy" if language_style == "traditional" else "your"
        suffrages = file_to_lines(self.get_suffrages_file_name())
        suffrages = self.add_names(suffrages)
        return (
            [
                Line("The Prayers", "heading"),
                Line("The Lord be with you.", "leader_dialogue", preface="Officiant"),
                Line(f"And with {pronoun} spirit.", "congregation_dialogue", preface="People"),
                Line("Let us pray.", "leader_dialogue", preface="Officiant"),
                Line("The People kneel or stand.", "rubric"),
            ]
            + file_to_lines(kyrie_file)
            + [Line("Officiant and People", "rubric")]
            + file_to_lines(pater_file)
            + suffrages
        )


class MPCollectOfTheDay(Module):
    name = "Collect(s) of the Day"
    attribute = "morning_prayer_collect"
    commemoration_attribute = "all"

    def get_collect(self, commemoration):
        style = self.office.settings["language_style"]
        collect = getattr(commemoration, self.attribute)
        text = collect.traditional_text_no_tags if style == "traditional" else collect.text_no_tags
        text = adapt_christmas_collect(text, commemoration)
        return text

    def get_lines(self):
        collects = [
            [
                Line("Collect of the Day", "heading"),
                Line(commemoration.name_no_tags, "subheading"),
                Line(self.get_collect(commemoration), "leader"),
                Line("Amen.", "congregation"),
            ]
            for commemoration in getattr(self.office.date, self.commemoration_attribute)
            if getattr(commemoration, self.attribute)
        ]
        lines = [line for collect in collects for line in collect]
        return lines


class EPCollectOfTheDay(MPCollectOfTheDay):
    attribute = "evening_prayer_collect"
    commemoration_attribute = "all_evening"


class AdditionalCollects(Module):
    name = "Additional Collects"

    def get_collects(self):
        return {}

    def get_weekly_collect(self):
        lines = []
        weekly_collect = self.pick_weekly_collect()
        weekly_collect["weekly"] = True
        collects = (weekly_collect,) + (self.pick_mission_collect(),) + self.get_extra_collects()
        language_style = self.office.settings["language_style"]
        for collect in collects:
            text = collect["traditional"] if language_style == "traditional" else collect["contemporary"]
            lines.append(Line(collect["title"], "heading"))
            if "weekly" in collect.keys() and collect["weekly"]:
                lines.append(Line(self.office.date.date.strftime("%A"), "subheading"))
            lines.append(Line(text, "leader"))
            lines.append(Line("Amen.", "congregation"))
        return lines

    def get_fixed_collect(self):
        lines = []
        language_style = self.office.settings["language_style"]

        for collect in self.pick_fixed_collects() + (self.pick_mission_collect(),) + self.get_extra_collects():
            text = collect["traditional"] if language_style == "traditional" else collect["contemporary"]
            lines.append(Line(collect["title"], "heading"))
            lines.append(Line(text, "leader"))
            lines.append(Line("Amen.", "congregation"))

        return lines

    def get_lines(self):
        collect_rotation = self.office.settings["collects"]
        if collect_rotation == "fixed":
            return self.get_fixed_collect()
        return self.get_weekly_collect()

    @cached_property
    def all_possible_collects(self):
        collects = Collect.objects.filter(tags__name=self.tag_name).distinct().all()
        results = {}
        mission_collects = []
        for collect in collects:
            key = collect.title.lower().replace("'", "")
            collect = {
                "title": collect.title,
                "contemporary": collect.text_no_tags,
                "traditional": collect.traditional_text_no_tags,
                "created": collect.created,
            }
            if collect["title"] == "A Prayer for Mission":
                mission_collects.append(collect)
            results[key] = collect
        return results, mission_collects

    @cached_property
    def possible_collects(self):
        results, mission_collects = self.all_possible_collects
        return results

    @cached_property
    def possible_mission_collects(self):
        results, mission_collects = self.all_possible_collects
        return mission_collects

    def pick_mission_collect(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        collect_number = day_of_year % 3
        return self.possible_mission_collects[collect_number - 1]

    def get_extra_collects(self):
        extra_collects = self.office.settings["extra_collects"]
        if extra_collects:
            extra_collects = (
                {
                    "title": extra_collect.title,
                    "contemporary": extra_collect.text_no_tags,
                    "traditional": extra_collect.traditional_text_no_tags,
                }
                for extra_collect in extra_collects
            )
            return tuple(extra_collects)
        return ()


class MPAdditionalCollects(AdditionalCollects):
    tag_name = "Morning Prayer"

    def pick_fixed_collects(self):
        return (self.possible_collects["a collect for peace"], self.possible_collects["a collect for grace"])

    def pick_weekly_collect(self):
        day = self.office.date.date.weekday()
        if day == 0:
            return self.possible_collects["a collect for the renewal of life"]
        if day == 1:
            return self.possible_collects["a collect for peace"]
        if day == 2:
            return self.possible_collects["a collect for grace"]
        if day == 3:
            return self.possible_collects["a collect for guidance"]
        if day == 4:
            return self.possible_collects["a collect for endurance"]
        if day == 5:
            return self.possible_collects["a collect for sabbath rest"]
        if day == 6:
            return self.possible_collects["a collect for strength to await christs return"]


class EPAdditionalCollects(AdditionalCollects):
    tag_name = "Evening Prayer"

    def pick_fixed_collects(self):
        return (
            self.possible_collects["a collect for peace"],
            self.possible_collects["a collect for aid against perils"],
        )

    def pick_weekly_collect(self):
        day = self.office.date.date.weekday()
        if day == 0:
            return self.possible_collects["a collect for peace"]
        if day == 1:
            return self.possible_collects["a collect for aid against perils"]
        if day == 2:
            return self.possible_collects["a collect for protection"]
        if day == 3:
            return self.possible_collects["a collect for the presence of christ"]
        if day == 4:
            return self.possible_collects["a collect for faith"]
        if day == 5:
            return self.possible_collects["a collect for the eve of worship"]
        if day == 6:
            return self.possible_collects["a collect for resurrection hope"]


class ShowGreatLitanyMixin(object):
    @property
    def show_great_litany(self):
        if self.office_name == "evening_prayer":
            setting = self.office.settings["ep_great_litany"]
        else:
            setting = self.office.settings["mp_great_litany"]
        if setting in ["mp_litany_off", "ep_litany_off"]:
            return False
        if setting in ["mp_litany_everyday", "ep_litany_everyday"]:
            return True
        if setting in ["mp_litany_w_f_s", "ep_litany_w_f_s"]:
            return self.office.date.date.weekday() in [2, 4, 6]
        return False


class Intercessions(Module):
    name = "Intercessions, Thanksgivings, and Praise"

    def get_lines(self):
        return [
            Line("Intercessions, Thanksgivings, and Praise", "heading"),
            Line("The Officiant may invite the People to offer intercessions and thanksgivings.", "rubric"),
            Line("A hymn or anthem may be sung.", "rubric"),
        ]


class FinalPrayers(Module):
    name = "Final Prayers"

    def get_lines(self):
        general_thanksgiving = self.office.settings["general_thanksgiving"]
        chrysostom = self.office.settings["chrysostom"]

        lines = []

        language_style = self.office.settings["language_style"]
        file = "general_thanksgiving_traditional" if language_style == "traditional" else "general_thanksgiving"

        if general_thanksgiving == "on":
            lines = (
                lines
                + [
                    Line("The General Thanksgiving", "heading"),
                    Line("Officiant and People", "rubric"),
                ]
                + file_to_lines(file)
            )

        language_style = self.office.settings["language_style"]
        file = "chrysostom_traditional" if language_style == "traditional" else "chrysostom"

        if chrysostom == "on":
            lines = (
                lines
                + [
                    Line("A Prayer of St. John Chrysostom", "heading"),
                ]
                + file_to_lines(file)
            )

        return lines


class Dismissal(Module):
    name = "Dismissal"

    def get_fixed_grace(self):
        return {
            "officiant": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Spirit, be with us all evermore.",
            "traditional": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Ghost, be with us all evermore.",
            "people": "Amen.",
            "citation": "2 CORINTHIANS 13:14",
        }

    def get_grace(self):
        if self.office.date.date.weekday() in (6, 2, 5):
            return {
                "officiant": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Spirit, be with us all evermore.",
                "traditional": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Ghost, be with us all evermore.",
                "people": "Amen.",
                "citation": "2 CORINTHIANS 13:14",
            }
        if self.office.date.date.weekday() in (0, 3):
            return {
                "officiant": "May the God of hope fill us with all joy and peace in believing through the power of the Holy Spirit. ",
                "traditional": "May the God of hope fill us with all joy and peace in believing through the power of the Holy Ghost.",
                "people": "Amen.",
                "citation": "ROMANS 15:13",
            }

        if self.office.date.date.weekday() in (1, 4):
            return {
                "officiant": "Glory to God whose power, working in us, can do infinitely more than we can ask or imagine: Glory to him from generation to generation in the Church, and in Christ Jesus for ever and ever.",
                "traditional": "Glory to God whose power, working in us, can do infinitely more than we can ask or imagine: Glory to him from generation to generation in the Church, and in Christ Jesus for ever and ever.",
                "people": "Amen.",
                "citation": "EPHESIANS 3:20-21",
            }

    def get_lines(self):
        grace_rotation = self.office.settings["grace"]

        easter = self.office.date.season.name == "Eastertide"

        officiant = "Let us bless the Lord."
        people = "Thanks be to God."

        if easter:
            officiant = "Alleluia, alleluia. {}".format(officiant)
            people = "Alleluia, alleluia. {} ".format(people)

        lines = [
            Line("Dismissal and Grace", "heading"),
            Line(officiant, "leader_dialogue"),
            Line(people, "congregation_dialogue"),
        ]

        if grace_rotation == "fixed":
            grace = self.get_fixed_grace()
        else:
            grace = self.get_grace()

        language_style = self.office.settings["language_style"]
        part = "traditional" if language_style == "traditional" else "officiant"

        return (
            lines
            + [Line("", "spacer")]
            + [
                Line(grace[part], "leader"),
                Line("Amen.", "congregation"),
                Line(grace["citation"], "citation"),
            ]
        )


class GreatLitany(ShowGreatLitanyMixin, Module):
    office_name = "office"

    def get_names(self):
        feasts = self.office.date.all_evening if self.office_name == "evening_prayer" else self.office.date.all
        names = [feast.saint_name for feast in feasts if hasattr(feast, "saint_name") and feast.saint_name]
        names = ["the Blessed Virgin Mary"] + names
        names = ", ".join(names)
        return f"{names} and "

    def get_leaders(self):
        setting = self.office.settings["national_holidays"]
        if setting == "us":
            return "your servant Donald Trump, the President of the United States of America, "
        if setting == "canada":
            return "your servants His Majesty King Charles, the Sovereign, and Justin Trudeau, the Prime Minister of Canada, "
        return "your servant Donald Trump, the President of the United States of America, your servants His Majesty King Charles, the Sovereign, and Justin Trudeau, the Prime Minister of Canada, Claudia Sheinbaum Pardo, the president of Mexico, "

    def get_lines(self):
        if self.show_great_litany:
            style = self.office.settings["language_style"]
            kyrie = (
                file_to_lines("kyrie_contemporary") if style == "contemporary" else file_to_lines("kyrie_traditional")
            )
            pater = (
                file_to_lines("pater_contemporary") if style == "contemporary" else file_to_lines("pater_traditional")
            )
            template = "great_litany_traditional" if style == "traditional" else "great_litany"
            supplication_template = "supplication_traditional" if style == "traditional" else "supplication"
            lines = (
                file_to_lines(template)
                + [Line("", "spacer")]
                + kyrie
                + [Line("", "spacer")]
                + pater
                + [Line("", "spacer")]
                + file_to_lines(supplication_template)
            )
            for line in lines:
                line["content"] = line["content"].replace("[_____________ and] ", self.get_names())
                line["content"] = line["content"].replace("{{ names }}", self.get_names())
                line["content"] = line["content"].replace("{{ leaders }}", self.get_leaders())
                line["content"] = line["content"].replace(
                    "thy servant N., the President/Sovereign/Prime Minister, ", self.get_leaders()
                )
                line["content"] = line["content"].replace(
                    "your servant N, the President/Sovereign/Prime Minister, ", self.get_leaders()
                )
            return lines
        return None


class MPGreatLitany(GreatLitany):
    office_name = "morning_prayer"


class EPGreatLitany(GreatLitany):
    office_name = "evening_prayer"


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
            MPSecondReading(self),
            MPSecondCanticle(self),
            MPThirdReading(self),
            Creed(self),
            Prayers(self),
            MPCollectOfTheDay(self),
            MPAdditionalCollects(self),
            MPGreatLitany(self),
            Intercessions(self),
            FinalPrayers(self),
            Dismissal(self),
        ]


class FamilyRubricSection(Module):
    name = "Rubrics"

    def get_lines(self):
        return [
            Line(
                "These devotions follow the basic structure of the Daily Office of the Church and are particularly appropriate for families with young children.",
                "rubric",
            ),
            Line(
                "The Reading and the Collect may be read by one person, and the other parts said in unison, or in some other convenient manner.",
                "rubric",
            ),
        ]


class FamilyMorningOpeningSentence(Module):
    name = "Opening Sentence"

    def get_lines(self):
        setting = self.office.settings["family-opening-sentence"]
        language_style = self.office.settings["language_style"]
        if language_style == "traditional":
            line = "O Lord, open thou my lips, and my mouth shall show forth thy praise."
        else:
            line = "O Lord, open my lips, and my mouth shall show forth your praise."
        if setting == "family-opening-sentence-fixed":
            return [
                Line("Opening Sentence", "heading"),
                Line(line, "leader"),
                Line("Psalm 51:15", "citation"),
            ]
        else:
            return MPOpeningSentence(self.office).get_lines()


class FamilyMiddayOpeningSentence(Module):
    name = "Opening Sentence"

    def get_lines(self):
        setting = self.office.settings["family-opening-sentence"]
        if setting == "family-opening-sentence-fixed":
            text = "Blessed be the God and Father of our Lord Jesus Christ, who has blessed us in Christ with every spiritual blessing in the heavenly places."
            language_style = self.office.settings["language_style"]
            if language_style == "traditional":
                text = "Blessed be the God and Father of our Lord Jesus Christ, who hath blessed us with all spiritual blessings in heavenly places in Christ."
            return [
                Line("Opening Sentence", "heading"),
                Line(
                    text,
                    "leader",
                ),
                Line("Ephesians 1:3", "citation"),
            ]
        else:
            return MPOpeningSentence(self.office).get_lines()


class FamilyEarlyEveningHymn(Module):
    name = "Hymn"

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        filename = "phos_hilaron_traditional" if language_style == "traditional" else "phos_hilaron"
        return file_to_lines(filename)


class FamilyCloseOfDayHymn(Module):
    name = "Hymn"

    def get_lines(self):
        canticle = CanticleModule(self.office).get_canticle(EP2)
        canticle = [line for line in canticle if line["line_type"] != "rubric"]
        return canticle


class FamilyCloseOfDayClosingSentence(Module):
    name = "Closing Sentence"

    def get_lines(self):
        return [
            Line("Closing Sentence", "heading"),
            Line(
                "The almighty and merciful Lord, Father, Son, and Holy Spirit, bless us and keep us, this night and evermore.",
                "leader",
            ),
            Line("Amen.", "congregation"),
        ]


class FamilyEarlyEveningOpeningSentence(Module):
    name = "Opening Sentence"

    def get_lines(self):
        setting = self.office.settings["family-opening-sentence"]
        language_style = self.office.settings["language_style"]
        text = "How excellent is your mercy, O God! The children of men shall take refuge under the shadow of your wings. For with you is the well of life, and in your light shall we see light."
        if language_style == "traditional":
            text = "How excellent is thy mercy, O God! The children of men shall put their trust under the shadow of thy wings. For with thee is the well of life, and in thy light shall we see light."
        if setting == "family-opening-sentence-fixed":
            return [
                Line("Opening Sentence", "heading"),
                Line(
                    text,
                    "leader",
                ),
                Line("Psalm 36:7, 9", "citation"),
            ]
        else:
            return EPOpeningSentence(self.office).get_lines()


class FamilyCloseOfDayOpeningSentence(Module):
    name = "Opening Sentence"

    def get_lines(self):
        setting = self.office.settings["family-opening-sentence"]
        language_style = self.office.settings["language_style"]
        text = "I will lay me down in peace, and take my rest; for you, LORD, only, make me dwell in safety."
        if language_style == "traditional":
            text = "I will lay me down in peace, and take my rest; for it is thou, Lord, only, that makest me dwell in safety"
        if setting == "family-opening-sentence-fixed":
            return [
                Line("Opening Sentence", "heading"),
                Line(
                    text,
                    "leader",
                ),
                Line("Psalm 4:8", "citation"),
            ]
        else:
            return EPOpeningSentence(self.office).get_lines()


class FamilyMorningPsalm(Module):
    name = "Psalm"

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        gloria_patri = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        psalm_style = self.office.settings["psalm_style"]
        return (
            get_psalms("51:10-12", api=True, language_style=language_style, headings=psalm_style)
            + [Line("", "spacer")]
            + file_to_lines(gloria_patri)
        )


class FamilyMiddayPsalm(Module):
    name = "Psalm"

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        gloria_patri = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        psalm_style = self.office.settings["psalm_style"]
        return (
            get_psalms("113:1-4", api=True, language_style=language_style, headings=psalm_style)
            + [Line("", "spacer")]
            + file_to_lines(gloria_patri)
        )


class FamilyCloseOfDayPsalm(Module):
    name = "Psalm"

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        gloria_patri = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        psalm_style = self.office.settings["psalm_style"]
        return (
            get_psalms("134", api=True, language_style=language_style, headings=psalm_style)
            + [Line("", "spacer")]
            + file_to_lines(gloria_patri)
        )


class FamilyReadingModule(ReadingModule):
    name = "Reading"

    def get_lines(self):
        setting = self.office.settings["family_readings"]
        audio_setting = self.office.settings["family_reading_audio"]
        if setting == "long":
            scripture = self.get_long()
            audio = self.audio(scripture["passage"], "NT")
            return [
                Line("A Reading from Holy Scripture", "heading"),
                Line(scripture["passage"], "subheading"),
                Line(audio, "html") if audio and audio_setting == "on" else Line("", "html"),
                Line(
                    GenericDailyOfficeSerializer.handle_html(
                        self.remove_headings_if_needed(scripture["text"]),
                        html=True,
                        no_generate=True,
                        id=f"{self.get_safe_name()}_ad0aad27-4e5d-5ce3-8947-2bef1e5a5586",
                    ),
                    "html",
                ),
                Line("A period of silence may follow.", "rubric"),
            ]
        scripture = self.get_scripture()
        language_style = self.office.settings["language_style"]
        passage = scripture["traditional"] if language_style == "traditional" else scripture["sentence"]
        audio = self.audio(scripture["citation"], "NT")
        return [
            Line("A Reading from Holy Scripture", "heading"),
            Line(scripture["citation"], "subheading"),
            Line(audio, "html") if audio and audio_setting == "on" else Line("", "html"),
            Line(
                GenericDailyOfficeSerializer.handle_html(
                    passage,
                    html=True,
                    no_generate=True,
                    id=f"{self.get_safe_name()}_ad0aad27-4e5d-5ce3-8947-2bef1e5a5586",
                ),
                "html",
            ),
            Line("A period of silence may follow.", "rubric"),
        ]


class FamilyMorningScripture(FamilyReadingModule):
    name = "Reading"

    def get_long(self):
        translation = self.office.settings["bible_translation"]
        return {
            "passage": (
                self.office.office_readings.mp_reading_1_abbreviated
                if self.office.office_readings.mp_reading_1_abbreviated
                else self.office.office_readings.mp_reading_1
            ),
            "text": self.get_reading("mp_reading_1", True, translation, text_only=True),
            "testament": self.office.office_readings.mp_reading_1_testament,
        }

    def get_scripture(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        number = day_of_year % 3

        scriptures = [
            {
                "sentence": "Blessed be the God and Father of our Lord Jesus Christ! According to his great mercy, he has caused us to be born again to a living hope through the resurrection of Jesus Christ from the dead.",
                "traditional": "Blessed be the God and Father of our Lord Jesus Christ, which according to his abundant mercy hath begotten us again unto a lively hope by the resurrection of Jesus Christ from the dead.",
                "citation": "1 PETER 1:3",
            },
            {
                "sentence": "Give thanks to the Father, who has qualified you to share in the inheritance of the saints in light. He has delivered us from the domain of darkness and transferred us to the kingdom of his beloved Son, in whom we have redemption, the forgiveness of sins.",
                "traditional": "Give thanks unto the Father, who hath made us meet to be partakers of the inheritance of the saints in light: Who hath delivered us from the power of darkness, and hath translated us into the kingdom of his dear Son: In whom we have redemption through his blood, even the forgiveness of sins.",
                "citation": "COLOSSIANS 1:12-14",
            },
            {
                "sentence": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God. Set your minds on things that are above, not on things that are on earth. For you have died, and your life is hidden with Christ in God. When Christ who is your life appears, then you also will appear with him in glory.",
                "traditional": "If ye then be risen with Christ, seek those things which are above, where Christ sitteth on the right hand of God. Set your affection on things above, not on things on the earth. For ye are dead, and your life is hid with Christ in God. When Christ, who is our life, shall appear, then shall ye also appear with him in glory.",
                "citation": "COLOSSIANS 3:1-4",
            },
        ]

        return scriptures[number]


class FamilyMiddayScripture(FamilyReadingModule):
    name = "Reading"

    def get_long(self):
        translation = self.office.settings["bible_translation"]
        return {
            "passage": self.office.office_readings.mp_reading_2,
            "text": self.get_reading("mp_reading_2", True, translation, text_only=True),
            "testament": self.office.office_readings.mp_reading_2_testament,
        }

    def get_scripture(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        number = day_of_year % 2

        scriptures = [
            {
                "sentence": "Abide in me, and I in you. As the branch cannot bear fruit by itself, unless it abides in the vine, neither can you, unless you abide in me. I am the vine; you are the branches. Whoever abides in me and I in him, he it is that bears much fruit, for apart from me you can do nothing.",
                "traditional": "Abide in me, and I in you. As the branch cannot bear fruit of itself, except it abide in the vine; no more can ye, except ye abide in me. I am the vine, ye are the branches: He that abideth in me, and I in him, the same bringeth forth much fruit: for without me ye can do nothing.",
                "citation": "JOHN 15:4-5",
            },
            {
                "sentence": "Do not be anxious about anything, but in everything by prayer and supplication with thanksgiving let your requests be made known to God. And the peace of God, which surpasses all understanding, will guard your hearts and your minds in Christ Jesus.",
                "traditional": "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God. And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus.",
                "citation": "PHILIPPIANS 4:6-7",
            },
        ]

        return scriptures[number]


class FamilyEarlyEveningScripture(FamilyReadingModule):
    name = "Reading"

    def get_long(self):
        translation = self.office.settings["bible_translation"]
        return {
            "passage": (
                self.office.office_readings.ep_reading_1_abbreviated
                if self.office.office_readings.ep_reading_1_abbreviated
                else self.office.office_readings.ep_reading_1
            ),
            "text": self.get_reading("ep_reading_1", True, translation, text_only=True),
            "testament": self.office.office_readings.ep_reading_1_testament,
        }

    def get_scripture(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        number = day_of_year % 3

        scriptures = [
            {
                "sentence": "For what we proclaim is not ourselves, but Jesus Christ as Lord, with ourselves as your servants for Jesus’ sake. For God, who said, “Let light shine out of darkness,” has shone in our hearts, to give the light of the knowledge of the glory of God in the face of Jesus Christ.",
                "traditional": "For we preach not ourselves, but Christ Jesus the Lord; and ourselves your servants for Jesus’ sake. For God, who commanded the light to shine out of darkness, hath shined in our hearts, to give the light of the knowledge of the glory of God in the face of Jesus Christ.",
                "citation": "2 CORINTHIANS 4:5-6",
            },
            {
                "sentence": "Jesus spoke to them, saying, “I am the light of the world. Whoever follows me will not walk in darkness, but will have the light of life.”",
                "traditional": "Then spake Jesus again unto them, saying, I am the light of the world: he that followeth me shall not walk in darkness, but shall have the light of life.",
                "citation": "JOHN 8:12",
            },
            {
                "sentence": "Jesus said, “Behold, I stand at the door and knock. If anyone hears my voice and opens the door, I will come in to him and eat with him, and he with me.”",
                "traditional": "Jesus said, Behold, I stand at the door, and knock: if any man hear my voice, and open the door, I will come in to him, and will sup with him, and he with me. ",
                "citation": "REVELATION 3:20",
            },
        ]

        return scriptures[number]


class FamilyCloseOfDayScripture(FamilyReadingModule):
    name = "Reading"

    def get_long(self):
        translation = self.office.settings["bible_translation"]
        return {
            "passage": self.office.office_readings.ep_reading_2,
            "text": self.get_reading("ep_reading_2", True, translation, text_only=True),
            "testament": self.office.office_readings.ep_reading_2_testament,
        }

    def get_scripture(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        number = day_of_year % 2

        scriptures = [
            {
                "sentence": "You keep them in perfect peace whose minds are stayed on you, because they trust in you. Trust in the LORD for ever, for the LORD God is an everlasting rock.",
                "traditional": "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee. Trust ye in the Lord for ever: for the Lord God is everlasting strength. ",
                "citation": "ISAIAH 26:3-4",
            },
            {
                "sentence": "Now may the God of peace himself sanctify you completely, and may your whole spirit and soul and body be kept blameless at the coming of our Lord Jesus Christ.",
                "traditional": "May the very God of peace sanctify you wholly; and I pray God your whole spirit and soul and body be preserved blameless unto the coming of our Lord Jesus Christ.",
                "citation": "1 THESSALONIANS 5:23",
            },
        ]

        return scriptures[number]


class FamilyIntercessions(Module):
    def get_lines(self):
        return [
            Line("Intercessions", "heading"),
            Line("Prayers may be offered for ourselves and others.", "rubric"),
        ]


class FamilyCloseOfDayIntercessions(Module):
    def get_lines(self):
        return [
            Line("Intercessions", "heading"),
            Line(
                "Prayers may be offered for ourselves and others. It is appropriate that prayers of thanksgiving for the blessings of the day, and penitence for our sins, be included.",
                "rubric",
            ),
        ]


class FamilyPraise(Module):
    def get_lines(self):
        return [
            Line("Praise", "heading"),
            Line("A hymn or canticle may be used.", "rubric"),
        ]


class FamilyCredo(Module):
    def get_lines(self):
        creed = self.office.settings["family-creed"]

        if creed == "family-creed-yes":
            language_style = self.office.settings["language_style"]
            file = "creed_traditional" if language_style == "traditional" else "creed"
            return [
                Line("The Apostles' Creed", "heading"),
            ] + file_to_lines(file)
        return []


class FamilyPater(Module):
    def get_lines(self):
        style = self.office.settings["language_style"]
        pater_style = self.office.settings["language_style_for_our_father"]
        filename = "pater_contemporary"
        if style == "traditional" or pater_style == "traditional":
            filename = "pater_traditional"
        return [
            Line("The Lord's Prayer", "heading"),
        ] + file_to_lines(filename)


class FamilyMorningCollect(Module):
    def get_lines(self):
        collect_type = self.office.settings["family_collect"]
        if collect_type == "day_of_week":
            lines = MPAdditionalCollects(self.office).get_weekly_collect()
        elif collect_type == "day_of_year":
            lines = MPCollectOfTheDay(self.office).get_lines()
            lines = [Line("The Collect", "heading")] + lines[1:4]
        else:
            text = "O Lord, our heavenly Father, almighty and everlasting God, you have brought us safely to the beginning of this day: Defend us by your mighty power, that we may not fall into sin nor run into any danger; and that, guided by your Spirit, we may do what is righteous in your sight; through Jesus Christ our Lord."
            language_style = self.office.settings["language_style"]
            if language_style == "traditional":
                text = "O Lord, our heavenly Father, Almighty and everlasting God, who hast safely brought us to the beginning of this day; Defend us in the same with thy mighty power; and grant that this day we fall into no sin, neither run into any kind of danger; but that all our doings, being ordered by thy governance, may be righteous in thy sight; through Jesus Christ our Lord."
            lines = [
                Line("The Collect", "heading"),
                Line("In the Morning", "subheading"),
                Line(
                    text,
                    "leader",
                ),
                Line("Amen.", "congregation"),
            ]
        return lines


class FamilyMiddayCollect(Module):
    def get_lines(self):
        collect_type = self.office.settings["family_collect"]
        if collect_type == "day_of_week":
            lines = [
                Line("The Collects", "heading"),
                Line("At Midday", "subheading"),
            ] + MiddayPrayers(self.office).get_collect_lines()
        elif collect_type == "day_of_year":
            lines = MPCollectOfTheDay(self.office).get_lines()
            lines = [Line("The Collect", "heading")] + lines[1:4]
        else:
            lines = [
                Line("The Collect", "heading"),
                Line("At Midday", "subheading"),
                Line(
                    "Blessed Savior, at this hour you hung upon the Cross, stretching out your loving arms: Grant that all the peoples of the earth may look to you and be saved; for your tender mercies’ sake.",
                    "leader",
                ),
                Line("Amen.", "congregation"),
            ]
        return lines


class FamilyEarlyEveningCollect(Module):
    def get_lines(self):
        collect_type = self.office.settings["family_collect"]
        if collect_type == "day_of_week":
            lines = EPAdditionalCollects(self.office).get_weekly_collect()
        elif collect_type == "day_of_year":
            lines = EPCollectOfTheDay(self.office).get_lines()
            lines = [Line("The Collect", "heading")] + lines[1:4]
        else:
            lines = [
                Line("The Collect", "heading"),
                Line("At Early Evening", "subheading"),
                Line(
                    "Lord Jesus, stay with us, for evening is at hand and the day is past; be our companion in the way, kindle our hearts, and awaken hope, that we may know you as you are revealed in Scripture and the breaking of bread. Grant this for the sake of your love.",
                    "leader",
                ),
                Line("Amen.", "congregation"),
            ]
        return lines


class FamilyCloseOfDayCollect(Module):
    def get_lines(self):
        collect_type = self.office.settings["family_collect"]
        if collect_type == "day_of_week":
            lines = EPAdditionalCollects(self.office).get_weekly_collect()
        elif collect_type == "day_of_year":
            lines = EPCollectOfTheDay(self.office).get_lines()
            lines = [Line("The Collect", "heading")] + lines[1:4]
        else:
            lines = [
                Line("The Collect", "heading"),
                Line("At the Close of Day", "subheading"),
                Line(
                    "Visit this place, O Lord, and drive far from it all snares of the enemy; let your holy angels dwell with us to preserve us in peace; and let your blessing be upon us always; through Jesus Christ our Lord.",
                    "leader",
                ),
                Line("Amen.", "congregation"),
            ]
        return lines


class FamilyMorningPrayer(Office):
    def get_modules(self):
        return [
            FamilyRubricSection(self),
            FamilyMorningOpeningSentence(self),
            FamilyMorningPsalm(self),
            FamilyMorningScripture(self),
            FamilyPraise(self),
            FamilyCredo(self),
            FamilyIntercessions(self),
            FamilyPater(self),
            FamilyMorningCollect(self),
        ]


class FamilyMiddayPrayer(Office):
    def get_modules(self):
        return [
            FamilyRubricSection(self),
            FamilyMiddayOpeningSentence(self),
            FamilyMiddayPsalm(self),
            FamilyMiddayScripture(self),
            FamilyIntercessions(self),
            FamilyPater(self),
            FamilyMiddayCollect(self),
        ]


class FamilyEarlyEveningPrayer(Office):
    def get_modules(self):
        return [
            FamilyRubricSection(self),
            FamilyEarlyEveningOpeningSentence(self),
            FamilyEarlyEveningHymn(self),
            FamilyEarlyEveningScripture(self),
            FamilyPraise(self),
            FamilyCredo(self),
            FamilyIntercessions(self),
            FamilyPater(self),
            FamilyEarlyEveningCollect(self),
        ]


class FamilyCloseOfDayPrayer(Office):
    def get_modules(self):
        return [
            FamilyRubricSection(self),
            FamilyCloseOfDayOpeningSentence(self),
            FamilyCloseOfDayPsalm(self),
            FamilyCloseOfDayScripture(self),
            FamilyPraise(self),
            FamilyCredo(self),
            FamilyCloseOfDayIntercessions(self),
            FamilyPater(self),
            FamilyCloseOfDayCollect(self),
            FamilyCloseOfDayHymn(self),
            FamilyCloseOfDayClosingSentence(self),
        ]


class EveningPrayer(Office):
    def get_modules(self):
        return [
            EPOpeningSentence(self),
            Confession(self),
            Preces(self),
            EPInvitatory(self),
            EPPsalms(self),
            EPFirstReading(self),
            EPFirstCanticle(self),
            EPSecondReading(self),
            EPSecondCanticle(self),
            EPThirdReading(self),
            Creed(self),
            Prayers(self),
            EPCollectOfTheDay(self),
            EPAdditionalCollects(self),
            EPGreatLitany(self),
            Intercessions(self),
            FinalPrayers(self),
            Dismissal(self),
        ]


class MiddayInvitatory(Module):
    name = "Invitatory"

    @property
    def alleluia(self):
        alleluia = (
            self.office.date.evening_season.name != "Lent" and self.office.date.evening_season.name != "Holy Week"
        )
        return "Alleluia." if alleluia else ""

    def add_alleluia(self, line):
        line["content"] = line["content"].replace("{{ alleluia }}", self.alleluia)
        return line

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        file_name = "midday_invitatory_traditional" if language_style == "traditional" else "midday_invitatory"
        lines = file_to_lines(file_name)
        return [self.add_alleluia((line)) for line in lines]


class MiddayPsalms(Module):
    name = "Psalms"

    def get_lines(self):
        psalms = "119:105-112,121,124,126"
        language_style = self.office.settings["language_style"]
        file_name = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        psalm_style = self.office.settings["psalm_style"]
        lines = file_to_lines(file_name)
        psalms = get_psalms(psalms, api=True, language_style=language_style, headings=psalm_style)

        return [Line("The Psalms", "heading")] + psalms + lines


class MiddayScripture(Module):
    name = "Scripture"

    def get_scripture(self):
        if self.office.date.date.weekday() in [0, 3, 6]:
            return {
                "sentence": "Jesus said, “Now is the judgment of this world; now will the ruler of this world be cast out. And I, when I am lifted up from the earth, will draw all people to myself.”",
                "traditional": "Jesus said, “Now is the judgment of this world: now shall the prince of this world be cast out. And I, if I be lifted up from the earth, will draw all men unto me.”",
                "citation": "JOHN 12:31-32",
            }

        if self.office.date.date.weekday() in [1, 4]:
            return {
                "sentence": "If anyone is in Christ, he is a new creation. The old has passed away; behold, the new has come. All this is from God, who through Christ reconciled us to himself and gave us the ministry of reconciliation.",
                "traditional": "If any man be in Christ, he is a new creature: old things are passed away; behold, all things are become new. And all things are of God, who hath reconciled us to himself by Jesus Christ, and hath given to us the ministry of reconciliation.",
                "citation": "2 CORINTHIANS 5:17-18",
            }

        if self.office.date.date.weekday() in [2, 5]:
            return {
                "sentence": "From the rising of the sun to its setting my name will be great among the nations, and in every place incense will be offered to my name, and a pure offering. For my name will be great among the nations, says the Lord of Hosts.",
                "traditional": "From the rising of the sun even unto the going down of the same my name shall be great among the Gentiles; and in every place incense shall be offered unto my name, and a pure offering: for my name shall be great among the heathen, saith the Lord of hosts.",
                "citation": "MALACHI 1:11",
            }

    def get_lines(self):
        scripture = self.get_scripture()
        language_style = self.office.settings["language_style"]
        field = "traditional" if language_style == "traditional" else "sentence"
        return [
            Line("The Reading", "heading"),
            Line(scripture[field], "leader"),
            Line(scripture["citation"], "citation"),
            Line("The Word of the Lord", "leader_dialogue"),
            Line("Thanks be to God.", "congregation_dialogue"),
            Line("A meditation, silent or spoken, may follow.", "rubric"),
        ]


class MiddayPrayers(Module):
    name = "Prayers"

    collects = [
        (
            (
                "Blessed Savior, at this hour you hung upon the Cross, stretching out your loving arms: Grant that all the peoples of the earth may look to you and be saved; for your tender mercies’ sake.",
                "Blessed Savior, who at this hour didst hang upon the cross stretching out thy loving arms: Grant that all the peoples of the earth may look unto thee and be saved; for thy tender mercies’ sake.",
            )
        ),
        (
            (
                "Almighty Savior, who at mid-day called your servant Saint Paul to be an apostle to the Gentiles: We pray you to illumine the world with the radiance of your glory, that all nations may come and worship you; for you live and reign with the Father and the Holy Spirit, one God, for ever and ever.",
                "Almighty Savior, who at mid-day didst call thy servant Saint Paul to be an apostle to the Gentiles: We pray thee to illumine the world with the radiance of thy glory, that all nations may come and worship thee; for thou livest and reignest with the Father and the Holy Spirit, one God, world without end. ",
            )
        ),
        (
            (
                "Father of all mercies, you revealed your boundless compassion to your apostle Saint Peter in a three-fold vision: Forgive our unbelief, we pray, and so strengthen our hearts and enkindle our zeal, that we may fervently desire the salvation of all people, and diligently labor in the extension of your kingdom; through him who gave himself for the life of the world, your Son our Savior Jesus Christ.",
                "Father of all mercies, thou hast revealed thy boundless compassion to thine apostle Saint Peter in a three-fold vision: Forgive our unbelief, we pray, and so strengthen our hearts and enkindle our zeal, that we may fervently desire the salvation of all people, and diligently labor in the extension of thy kingdom; through him who gave himself for the life of the world, thy Son our Savior Jesus Christ. ",
            )
        ),
        (
            (
                "Pour your grace into our hearts, O Lord, that we who have known the incarnation of your Son Jesus Christ, announced by an angel to the Virgin Mary, may by his Cross and passion be brought to the glory of his resurrection; who lives and reigns with you, in the unity of the Holy Spirit, one God, now and for ever.",
                "We beseech thee, O Lord, pour thy grace into our hearts; that as we have known the incarnation of thy Son Jesus Christ announced by the message of an angel to the Virgin Mary, so by his cross and passion we may be brought unto the glory of his resurrection; through the same Christ our Lord.",
            )
        ),
    ]

    def get_collects(self):
        day_of_year = self.office.date.date.timetuple().tm_yday
        collect_number = day_of_year % 3 + 1

        if self.office.date.primary.name in ["Conversion of Paul the Apostle"]:
            return self.collects[0], self.collects[1]

        if self.office.date.primary.name in ["Peter and Paul, Apostles"]:
            return self.collects[0], self.collects[1], self.collects[2]

        if self.office.date.primary.name in ["Confession of Peter the Apostle"]:
            return self.collects[0], self.collects[2]

        if self.office.date.primary.name in [
            "The Annunciation of our Lord Jesus Christ to the Virgin Mary",
            "The Virgin Mary, Mother of our Lord Jesus Christ",
            "The Visitation of the Virgin Mary to Elizabeth and Zechariah",
            "The Presentation of Our Lord Jesus Christ in the Temple",
        ]:
            return self.collects[0], self.collects[3]

        return self.collects[0], self.collects[collect_number]

    def get_collect_lines(self):
        language_style = self.office.settings["language_style"]
        collects = self.get_collects()
        lines = []
        for collect in collects:
            text = collect[1] if language_style == "traditional" else collect[0]
            lines.append(Line("", "spacer"))
            lines.append(Line(text, "leader"))
            lines.append(Line("Amen.", "congregation"))
        return lines

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        pater_style = self.office.settings["language_style_for_our_father"]
        kyrie_file = (
            "kyrie_traditional"
            if language_style == "traditional" or pater_style == "traditional"
            else "kyrie_contemporary"
        )
        pater_file = (
            "pater_traditional"
            if language_style == "traditional" or pater_style == "traditional"
            else "pater_contemporary"
        )
        kyrie = file_to_lines(kyrie_file)
        pater = file_to_lines(pater_file)
        suffrages_1_file_name = (
            "midday_suffrages_1_traditional" if language_style == "traditional" else "midday_suffrages_1"
        )
        suffrages_2_file_name = (
            "midday_suffrages_2_traditional" if language_style == "traditional" else "midday_suffrages_2"
        )
        suffrages_1 = file_to_lines(suffrages_1_file_name)
        suffrages_2 = file_to_lines(suffrages_2_file_name)
        return (
            [
                Line("The Prayers", "heading"),
            ]
            + suffrages_1
            + [
                Line("", "spacer"),
            ]
            + kyrie
            + [Line("Officiant and People", "rubric")]
            + pater
            + [
                Line("", "spacer"),
            ]
            + suffrages_2
            + self.get_collect_lines()
        )


class MiddayAdditonalCollects(AdditionalCollects):
    def get_lines(self):
        extra_collects = self.get_extra_collects()
        collects = tuple([list(extra_collect.values()) for extra_collect in extra_collects])
        lines = []
        style = self.office.settings["language_style"]
        for collect in collects:
            leader_part = collect[2] if style == "traditional" else collect[1]
            lines.append(Line("", "spacer"))
            lines.append(Line(collect[0], "subheading"))
            lines.append(Line(leader_part, "leader"))
            lines.append(Line("Amen.", "congregation"))
        return lines


class MiddayConclusion(Module):
    name = "Conclusion"

    @property
    def alleluia(self):
        alleluia = self.office.date.season.name == "Eastertide"
        return "Alleluia. Alleluia." if alleluia else ""

    def add_alleluia(self, line):
        line["content"] = line["content"].replace("{{ alleluia }}", self.alleluia)
        return line

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        file_name = "midday_conclusion_traditional" if language_style == "traditional" else "midday_conclusion"
        lines = file_to_lines(file_name)
        return [self.add_alleluia((line)) for line in lines]


class MiddayPrayer(Office):
    def get_modules(self):
        return [
            MiddayInvitatory(self),
            MiddayPsalms(self),
            MiddayScripture(self),
            MiddayPrayers(self),
            MiddayAdditonalCollects(self),
            MiddayConclusion(self),
        ]


class ComplineOpeningSentence(Module):
    name = "Opening Sentence"

    # heading
    # subheading
    # citation
    # html
    # leader
    # congregation
    # rubric
    # leader_dialogue
    # congregation_dialogue

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        final_line = (
            "Who hath made heaven and earth." if language_style == "traditional" else "The maker of heaven and earth."
        )
        return [
            Line("Opening Sentence", "heading"),
            Line("The Officiant begins:", "rubric"),
            Line("The Lord Almighty grant us a peaceful night and a perfect end.", "leader_dialogue"),
            Line("Amen.", "congregation_dialogue"),
            Line("Our help is in the Name of the Lord;", "leader_dialogue"),
            Line(final_line, "congregation_dialogue"),
        ]


class ComplineConfession(Module):
    name = "Confession"

    # heading
    # subheading
    # citation
    # html
    # leader
    # congregation
    # rubric
    # leader_dialogue
    # congregation_dialogue

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        file_name = "confession_compline_traditional" if language_style == "traditional" else "confession_compline"
        return (
            [
                Line("Confession of Sin", "heading"),
                Line("The Officiant continues", "rubric"),
                Line("Let us humbly confess our sins unto Almighty God.", "leader_dialogue"),
                Line("Silence may be kept. The Officiant and People then say", "rubric"),
            ]
            + file_to_lines(file_name)
            + [
                Line("The Officiant alone says", "rubric"),
                Line(
                    "May almighty God grant us forgiveness of all our sins, and the grace and comfort of the Holy Spirit. ",
                    "leader",
                ),
                Line("Amen.", "congregation"),
            ]
        )


class ComplineInvitatory(Module):
    name = "Invitatory"

    # heading
    # subheading
    # citation
    # html
    # leader
    # congregation
    # rubric
    # leader_dialogue
    # congregation_dialogue

    @property
    def alleluia(self):
        alleluia = self.office.date.evening_season.name not in ["Lent", "Holy Week"]
        return " Alleluia." if alleluia else ""

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        ghost = "Ghost" if language_style == "traditional" else "Spirit"
        return [
            Line("Invitatory", "heading"),
            Line("O God, make speed to save us;", "leader_dialogue"),
            Line("O Lord, make haste to help us.", "congregation_dialogue"),
            Line(f"Glory be to the Father, and to the Son, and to the Holy {ghost};", "leader_dialogue"),
            Line(
                "As it was in the beginning, is now, and ever shall be, world without end. Amen.{}".format(
                    self.alleluia
                ),
                "congregation_dialogue",
            ),
        ]


class ComplinePsalms(Module):
    name = "Psalms"

    def gloria_patri(self):
        language_style = self.office.settings["language_style"]
        file = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        return [Line("", "spacer")] + file_to_lines(file)

    def get_lines(self):
        psalms = "4,31:1-6,91,134"
        language_style = self.office.settings["language_style"]
        psalm_style = self.office.settings["psalm_style"]
        psalms = get_psalms(psalms, api=True, language_style=language_style, headings=psalm_style)

        return [Line("The Psalms", "heading")] + psalms + self.gloria_patri()


class ComplineScripture(Module):
    name = "Scripture"

    def get_scripture(self):
        if self.office.date.date.weekday() in [0, 4]:
            return {
                "sentence": "You, O Lord, are in the midst of us, and we are called by your name; do not leave us.",
                "traditional": "Thou, O Lord, art in the midst of us, and we are called by thy Name. Leave us not, O Lord our God.",
                "citation": "JEREMIAH 14:9",
            }

        if self.office.date.date.weekday() in [1, 5]:
            return {
                "sentence": "Come to me, all who labor and are heavy laden, and I will give you rest. Take my yoke upon you, and learn from me, for I am gentle and lowly in heart, and you will find rest for your souls. For my yoke is easy, and my burden is light.",
                "traditional": "Come unto me, all ye that labor and are heavy laden, and I will give you rest. Take my yoke upon you, and learn of me; for I am meek and lowly in heart; and ye shall find rest unto your souls. For my yoke is easy, and my burden is light. ",
                "citation": "MATTHEW 11:28-30",
            }

        if self.office.date.date.weekday() in [2, 6]:
            return {
                "sentence": "Now may the God of peace who brought again from the dead our Lord Jesus, the great shepherd of the sheep, by the blood of the eternal covenant, equip you with everything good that you may do his will, working in us that which is pleasing in his sight, through Jesus Christ, to whom be glory forever and ever. Amen.",
                "traditional": "Now the God of peace, that brought again from the dead our Lord Jesus, that great Shepherd of the sheep, through the blood of the everlasting covenant, make you perfect in every good work to do his will, working in you that which is well pleasing in his sight; through Jesus Christ, to whom be glory for ever and ever. Amen.",
                "citation": "HEBREWS 13:20-21",
            }

        if self.office.date.date.weekday() in [3]:
            return {
                "sentence": "Be sober-minded; be watchful. Your adversary the devil prowls around like a roaring lion, seeking someone to devour. Resist him, firm in your faith.",
                "traditional": "Be sober, be vigilant, because your adversary the devil, as a roaring lion, walketh about, seeking whom he may devour: whom resist, steadfast in the faith.",
                "citation": "1 PETER 5:8-9",
            }

    def get_lines(self):
        scripture = self.get_scripture()
        return [
            Line("The Reading", "heading"),
            Line(scripture["sentence"], "leader"),
            Line(scripture["citation"], "citation"),
            Line("The Word of the Lord", "leader_dialogue"),
            Line("Thanks be to God.", "congregation_dialogue"),
        ]


class ComplinePrayers(AdditionalCollects):
    name = "Prayers"

    collects = [
        (
            "A Collect for Evening",
            "Visit this place, O Lord, and drive far from it all snares of the enemy; let your holy angels dwell with us to preserve us in peace; and let your blessing be upon us always; through Jesus Christ our Lord.",
            "Visit this place, we beseech thee, O Lord, and drive from it all the snares of the enemy; let thy holy angels dwell herein to preserve us in peace; and may thy blessing be upon us evermore; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Aid Against Peril",
            "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ.",
            "Lighten our darkness, we beseech thee, O Lord; and by thy great mercy defend us from all perils and dangers of this night; for the love of thine only Son, our Savior Jesus Christ.",
        ),
        (
            "A Collect for Evening",
            "Be present, O merciful God, and protect us through the hours of this night, so that we who are wearied by the changes and chances of this life may rest in your eternal changelessness; through Jesus Christ our Lord.",
            "Be present, O merciful God, and protect us through the hours of this night, so that we who are wearied by the changes and chances of this life may rest in thine eternal changelessness; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Evening",
            "Look down, O Lord, from your heavenly throne, illumine this night with your celestial brightness, and from the children of light banish the deeds of darkness; through Jesus Christ our Lord.",
            "Look down, O Lord, from thy heavenly throne, illumine the darkness of this night with thy celestial brightness, and from the children of light banish the deeds of darkness; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Saturdays",
            "We give you thanks, O God, for revealing your Son Jesus Christ to us by the light of his resurrection: Grant that as we sing your glory at the close of this day, our joy may abound in the morning as we celebrate the Paschal mystery; through Jesus Christ our Lord.",
            "We give thee thanks, O God, for revealing thy Son Jesus Christ to us by the light of his resurrection: Grant that as we sing thy glory at the close of this day, our joy may abound in the morning as we celebrate the Paschal mystery; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Mission",
            "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give your angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for your love’s sake.",
            "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give thine angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for thy love’s sake.",
        ),
        (
            "A Collect for Evening",
            "O God, your unfailing providence sustains the world we live in and the life we live: Watch over those, both night and day, who work while others sleep, and grant that we may never forget that our common life depends upon each other’s toil; through Jesus Christ our Lord.",
            "O God, whose unfailing providence sustaineth the world we live in and the life we live: Watch over those, both night and day, who work while others sleep, and grant that we may never forget that our common life depends upon each other’s toil; through Jesus Christ our Lord.",
        ),
    ]

    def get_collects(self):
        if self.office.date.date.weekday() in [6]:  # Sunday
            return self.collects[0], self.collects[1], self.collects[5]

        if self.office.date.date.weekday() in [0]:  # Monday
            return self.collects[2], self.collects[3], self.collects[5]

        if self.office.date.date.weekday() in [1]:  # Tuesday
            return self.collects[0], self.collects[2], self.collects[5]

        if self.office.date.date.weekday() in [2]:  # Wednesday
            return self.collects[1], self.collects[3], self.collects[6]

        if self.office.date.date.weekday() in [3]:  # Thursday
            return self.collects[0], self.collects[3], self.collects[5]

        if self.office.date.date.weekday() in [4]:  # Friday
            return self.collects[1], self.collects[2], self.collects[6]

        if self.office.date.date.weekday() in [5]:  # Saturday
            return self.collects[2], self.collects[4], self.collects[5]

    def get_collect_lines(self):
        extra_collects = self.get_extra_collects()
        extra_collects = tuple([list(extra_collect.values()) for extra_collect in extra_collects])
        collects = self.get_collects() + extra_collects
        lines = []
        style = self.office.settings["language_style"]
        for collect in collects:
            leader_part = collect[2] if style == "traditional" else collect[1]
            lines.append(Line("", "spacer"))
            lines.append(Line(collect[0], "subheading"))
            lines.append(Line(leader_part, "leader"))
            lines.append(Line("Amen.", "congregation"))
        return lines

    def get_lines(self):
        style = self.office.settings["language_style"]
        our_father_style = self.office.settings["language_style_for_our_father"]
        if style == "traditional" or our_father_style == "traditional":
            kyrie_file = "kyrie_traditional"
            pater_file = "pater_traditional"
        else:
            kyrie_file = "kyrie_contemporary"
            pater_file = "pater_contemporary"
        kyrie = file_to_lines(kyrie_file)
        pater = file_to_lines(pater_file)
        dialogue = [
            Line("The Prayers", "heading"),
            Line("Into your hands, O Lord, I commend my spirit;", "leader_dialogue"),
            Line("For you have redeemed me, O Lord, O God of truth.", "congregation_dialogue"),
            Line("Keep me, O Lord, as the apple of your eye;", "leader_dialogue"),
            Line("Hide me under the shadow of your wings.", "congregation_dialogue"),
            Line("", "spacer"),
        ]
        traditional_dialogue = [
            Line("The Prayers", "heading"),
            Line("Into thy hands, O Lord, I commend my spirit;", "leader_dialogue"),
            Line("For thou hast redeemed me, O Lord, thou God of truth.", "congregation_dialogue"),
            Line("Keep me, O Lord, as the apple of thine eye;", "leader_dialogue"),
            Line("Hide me under the shadow of thy wings.", "congregation_dialogue"),
            Line("", "spacer"),
        ]

        dialogue_2 = [
            Line("", "spacer"),
            Line("O Lord, hear our prayer", "leader_dialogue"),
            Line("And let our cry come to you.", "congregation_dialogue"),
            Line("Let us pray.", "leader_dialogue"),
        ]
        traditional_dialogue_2 = [
            Line("", "spacer"),
            Line("O Lord, hear our prayer;", "leader_dialogue"),
            Line("And let our cry come unto thee.", "congregation_dialogue"),
            Line("Let us pray.", "leader_dialogue"),
        ]
        return (
            (traditional_dialogue if style == "traditional" else dialogue)
            + kyrie
            + [Line("Officiant and People", "rubric")]
            + pater
            + (traditional_dialogue_2 if style == "traditional" else dialogue_2)
            + self.get_collect_lines()
        )


class ComplineCanticle(Module):
    @property
    def antiphon(self):
        return "Guide us waking, O Lord, and guard us sleeping; that awake we may watch with Christ, and asleep we may rest in peace.{}".format(
            self.alleluia
        )

    @property
    def alleluia(self):
        alleluia = self.office.date.evening_season.name == "Eastertide"
        return " Alleluia, alleluia, alleluia." if alleluia else ""

    def get_lines(self):
        language_style = self.office.settings["language_style"]
        filename = "ep2_traditional" if language_style == "traditional" else "ep2"
        canticle = file_to_lines(filename)
        gloria_patri_filename = "gloria_patri_traditional" if language_style == "traditional" else "gloria_patri"
        return (
            [
                Line("Nunc Dimittis", "heading"),
                Line("The Song of Simeon", "subheading"),
                Line(
                    "The Officiant and People say or sing the Song of Simeon with this Antiphon, all standing",
                    "rubric",
                ),
                Line(self.antiphon, "congregation"),
                Line("", "spacer"),
            ]
            + canticle
            + file_to_lines(gloria_patri_filename)
            + [Line("", "spacer"), Line(self.antiphon, "congregation")]
        )
        return file_to_lines(filename)


class ComplineConclusion(Module):
    name = "Conclusion"

    def get_lines(self):
        return [
            Line("The Dismissal", "heading"),
            Line("Let us bless the Lord.", "leader_dialogue"),
            Line("Thanks be to God.", "congregation_dialogue"),
            Line("The Officiant concludes with the following", "rubric"),
            Line(
                "The almighty and merciful Lord, Father, Son, and Holy Spirit, bless us and keep us, this night and evermore.",
                "leader_dialogue",
            ),
            Line("Amen.", "congregation_dialogue"),
        ]


class Compline(Office):
    def get_modules(self):
        return [
            ComplineOpeningSentence(self),
            ComplineConfession(self),
            ComplineInvitatory(self),
            ComplinePsalms(self),
            ComplineScripture(self),
            ComplinePrayers(self),
            ComplineCanticle(self),
            ComplineConclusion(self),
        ]


class Readings(Module):
    def __init__(self, request, year, month, day, translation="esv", psalms="contemporary", style="whole_verse"):
        from churchcal.calculations import get_calendar_date

        self.settings = Settings(request)

        self.date = get_calendar_date("{}-{}-{}".format(year, month, day))
        self.mass_year = get_church_year("{}-{}-{}".format(year, month, day)).mass_year
        self.translation = translation
        self.psalms = psalms
        self.style = style

        try:
            self.holy_day_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except (HolyDayOfficeDay.DoesNotExist, ValueError):
            self.holy_day_readings = None

        self.standard_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)


class OfficeAPIView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        raise NotImplementedError("You must implement this method.")


class GenericDailyOfficeSerializer(serializers.Serializer):
    modules = serializers.SerializerMethodField()

    def get_modules(self, obj):
        modules = [module.json for module in obj.get_modules()]
        modules = [module for module in modules if module and module["lines"]]
        return modules

    @staticmethod
    def get_line_audio_file(line, no_generate=False):
        content = line["content"]
        line_type = line["line_type"]
        if "leader" in line_type:
            voice_type = "onyx"
        elif "congregation" in line_type:
            voice_type = "ash"
        elif "html" in line_type:
            voice_type = "echo"
        elif "reader" in line_type:
            voice_type = "echo"
        else:
            return
        content = content.replace("LORD", "Lord")
        content = content.replace("Lᴏʀᴅ", "Lord")
        audio_id = generate_uuid_from_string(f"{line_type} {voice_type} {content}")
        filename = f"{audio_id}.mp3"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        domain = Site.objects.get_current().domain
        path = settings.MEDIA_URL + filename
        file_url = f"https://{domain}{path}"
        if no_generate:
            return file_url
        if exists:
            return file_url
        try:
            from pathlib import Path
            from openai import OpenAI

            client = OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_type,
                input=content,
            )
            response.stream_to_file(file_path)
        except Exception as e:
            return
        print(file_url)
        return file_url

    @staticmethod
    def handle_html(line, html=False, no_generate=False, id=None):
        import re
        from bs4 import BeautifulSoup

        lines = []
        audio_files = []

        sentences = re.split(r"(?<=[.!?])", line)
        for sentence in sentences:
            soup = BeautifulSoup(sentence, "html.parser")
            plain_text = soup.get_text()
            text_without_verses = re.sub(r"(\b\d+\b\s)", "", plain_text)
            url = GenericDailyOfficeSerializer.get_line_audio_file(
                Line(text_without_verses, "reader"), no_generate=no_generate
            )
            if url:
                uuid_match = re.search(r"/uploads/([0-9a-fA-F-]+)\.mp3", url)
                if uuid_match:
                    uuid = uuid_match.group(1)
                if id is not None:
                    id = re.sub(r"_[^_]+$", f"_{uuid}", id)
                lines.append(f"<span data-line-id='{id}'></span>{sentence}")
                audio_files.append({"line_id": id, "url": url})
        result = "".join(lines)

        if html:
            result = result.replace("--end of footnotes-->", "").replace("--end of crossrefs-->", "")
            result = result.strip()
            return result

        return audio_files

    def get_audio(self, obj):
        if hasattr(obj.settings, "bible_translation") and obj.settings.bible_translation not in ["esv", "kjv"]:
            return []
        modules = self.get_modules(obj)
        tracks = []
        headings = []
        for module in modules:
            for i, line in enumerate(module["lines"]):
                if line["line_type"] in ["heading"]:
                    j = i
                    look_ahead_line = module["lines"][j + 1] if j + 1 < len(module["lines"]) else None
                    while j + 1 < len(module["lines"]) and look_ahead_line["line_type"] not in [
                        "reader",
                        "leader",
                        "congregation",
                        "leader_dialogue",
                        "congregation_dialogue",
                        "html",
                    ]:
                        look_ahead_line = module["lines"][j + 1]
                        j = j + 1
                    print(type(look_ahead_line))
                    headings.append({"heading": line["content"], "next_id": look_ahead_line["id"]})

                if line["line_type"] == "html":
                    temp_id = "_".join([line["id"].split("_")[0], line["id"].split("_")[-1]])
                    tracks = tracks + self.handle_html(line["content"], id=temp_id)
                elif line["line_type"] in ["reader"]:
                    tracks = tracks + [{"line_id": line["id"], "url": self.get_line_audio_file(line)}]
                elif line["line_type"] in [
                    "reader",
                    "leader",
                    "congregation",
                    "leader_dialogue",
                    "congregation_dialogue",
                ]:
                    tracks = tracks + [
                        {"line_id": line["id"], "module": module["name"], "url": self.get_line_audio_file(line)}
                    ]
        tracks = [track for track in tracks if track]
        headings = [heading for heading in headings if heading]
        print(headings)
        return {"tracks": tracks, "headings": headings}


class OfficeSerializer(GenericDailyOfficeSerializer):
    calendar_day = DaySerializer(source="date")
    modules = serializers.SerializerMethodField()


class OfficeAudioSerializer(GenericDailyOfficeSerializer):
    audio = serializers.SerializerMethodField()


def reading_format(name, citation, text, testament, cycle=None, reading_number=None):
    return {
        "name": name,
        "citation": citation.replace(",", ", "),
        "text": text,
        "testament": testament,
        "cycle": cycle,
        "reading_number": reading_number,
    }


def morning_prayer_30_day_psalms(obj):
    count = len(obj.thirty_day_psalter_day.mp_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.thirty_day_psalter_day.mp_psalms.replace(",", ", ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.thirty_day_psalter_day.mp_psalms,
            simplified_citations=True,
            language_style=obj.psalms,
            headings=obj.style,
        ),
        testament="OT",
        cycle="30",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def evening_prayer_30_day_psalms(obj):
    count = len(obj.thirty_day_psalter_day.ep_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.thirty_day_psalter_day.ep_psalms.replace(",", ", ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.thirty_day_psalter_day.ep_psalms,
            simplified_citations=True,
            language_style=obj.psalms,
            headings=obj.style,
        ),
        testament="OT",
        cycle="30",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_morning_prayer_60_day_psalms(obj):
    count = len(obj.standard_readings.mp_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.standard_readings.mp_psalms.replace(",", ", ").replace("or", " or Psalm ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.standard_readings.mp_psalms, simplified_citations=True, language_style=obj.psalms, headings=obj.style
        ),
        testament="OT",
        cycle="60",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_evening_prayer_60_day_psalms(obj):
    count = len(obj.standard_readings.ep_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.standard_readings.ep_psalms.replace(",", ", ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.standard_readings.ep_psalms, simplified_citations=True, language_style=obj.psalms, headings=obj.style
        ),
        testament="OT",
        cycle="60",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_morning_prayer_60_day_psalms(obj):
    count = len(obj.holy_day_readings.mp_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.holy_day_readings.mp_psalms.replace(",", ", ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.holy_day_readings.mp_psalms, simplified_citations=True, language_style=obj.psalms, headings=obj.style
        ),
        testament="OT",
        cycle="60",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_evening_prayer_60_day_psalms(obj):
    count = len(obj.holy_day_readings.ep_psalms.split(","))
    plural = "s" if count > 1 else ""
    name = f"The Psalm{plural}"
    citation = obj.holy_day_readings.ep_psalms.replace(",", ", ")
    citation = f"Psalm{plural} {citation}"
    psalm_style = obj.settings["psalm_style"]
    full = reading_format(
        name=name,
        citation=citation,
        text=get_psalms(
            obj.holy_day_readings.ep_psalms, simplified_citations=True, language_style=obj.psalms, headings=obj.style
        ),
        testament="OT",
        cycle="60",
        reading_number=0,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_morning_prayer_reading_1(obj):
    full = reading_format(
        name="The First Lesson",
        citation=obj.holy_day_readings.mp_reading_1,
        text=obj.holy_day_readings.passage_to_text("mp_reading_1", obj.translation),
        testament=obj.holy_day_readings.mp_reading_1_testament,
        reading_number=1,
    )
    abbreviated = full
    if obj.holy_day_readings.mp_reading_1_abbreviated:
        abbreviated = reading_format(
            name="The First Lesson",
            citation=obj.holy_day_readings.mp_reading_1_abbreviated,
            text=obj.holy_day_readings.passage_to_text("mp_reading_1_abrreviated", obj.translation),
            testament=obj.holy_day_readings.mp_reading_1_testament,
            reading_number=1,
        )
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_morning_prayer_reading_2(obj):
    full = reading_format(
        name="The Second Lesson",
        citation=obj.holy_day_readings.mp_reading_2,
        text=obj.holy_day_readings.passage_to_text("mp_reading_2", obj.translation),
        testament=obj.holy_day_readings.mp_reading_2_testament,
        reading_number=2,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_evening_prayer_reading_1(obj):
    full = reading_format(
        name="The First Lesson",
        citation=obj.holy_day_readings.ep_reading_1,
        text=obj.holy_day_readings.passage_to_text("ep_reading_1", obj.translation),
        testament=obj.holy_day_readings.ep_reading_1_testament,
        reading_number=1,
    )
    abbreviated = full
    if obj.holy_day_readings.ep_reading_1_abbreviated:
        abbreviated = reading_format(
            name="The First Lesson",
            citation=obj.holy_day_readings.ep_reading_1_abbreviated,
            text=obj.holy_day_readings.passage_to_text("ep_reading_1_abbreviated", obj.translation),
            testament=obj.holy_day_readings.ep_reading_1_testament,
        )
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def holy_day_evening_prayer_reading_2(obj):
    full = reading_format(
        name="The Second Lesson",
        citation=obj.holy_day_readings.ep_reading_2,
        text=obj.holy_day_readings.passage_to_text("ep_reading_2", obj.translation),
        testament=obj.holy_day_readings.ep_reading_2_testament,
        reading_number=2,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_morning_prayer_reading_1(obj):
    full = reading_format(
        name="The First Lesson",
        citation=obj.standard_readings.mp_reading_1,
        text=obj.standard_readings.passage_to_text("mp_reading_1", obj.translation),
        testament=obj.standard_readings.mp_reading_1_testament,
        reading_number=1,
    )
    abbreviated = full
    if obj.standard_readings.mp_reading_1_abbreviated:
        abbreviated = reading_format(
            name="The First Lesson",
            citation=obj.standard_readings.mp_reading_1_abbreviated,
            text=obj.standard_readings.passage_to_text("mp_reading_1_abbreviated", obj.translation),
            testament=obj.standard_readings.mp_reading_1_testament,
            reading_number=1,
        )
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_morning_prayer_reading_2(obj):
    full = reading_format(
        name="The Second Lesson",
        citation=obj.standard_readings.mp_reading_2,
        text=obj.standard_readings.passage_to_text("mp_reading_2", obj.translation),
        testament=obj.standard_readings.mp_reading_2_testament,
        reading_number=2,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_evening_prayer_reading_1(obj):
    full = reading_format(
        name="The First Lesson",
        citation=obj.standard_readings.ep_reading_1,
        text=obj.standard_readings.passage_to_text("ep_reading_1", obj.translation),
        testament=obj.standard_readings.ep_reading_1_testament,
        reading_number=1,
    )
    abbreviated = full
    if obj.standard_readings.ep_reading_1_abbreviated:
        abbreviated = reading_format(
            name="The First Lesson",
            citation=obj.standard_readings.ep_reading_1_abbreviated,
            text=obj.standard_readings.passage_to_text("ep_reading_1_abbreviated", obj.translation),
            testament=obj.standard_readings.ep_reading_1_testament,
            reading_number=1,
        )
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def standard_evening_prayer_reading_2(obj):
    full = reading_format(
        name="The Second Lesson",
        citation=obj.standard_readings.ep_reading_2,
        text=obj.standard_readings.passage_to_text("ep_reading_2", obj.translation),
        testament=obj.standard_readings.ep_reading_2_testament,
        reading_number=2,
    )
    abbreviated = full
    return {
        "full": full,
        "abbreviated": abbreviated,
    }


def get_reading_name_from_reading_number(reading):
    reading_number = reading.reading_number
    service = reading.service
    book = reading.book
    testament = reading.testament
    reading_type = reading.reading_type

    if service == "Easter Vigil":
        if reading_type == "epistle":
            return "The Epistle"
        if reading_type == "gospel":
            return "The Gospel"
        if book == "Psalms":
            return "A Psalm"
        if book == "-":
            return "A Canticle"
        return "Vigil Lesson"

    names = {
        1: "The First Lesson",
        2: "The Psalm",
        3: "The Second Lesson",
        4: "The Gospel",
    }
    return names[reading_number]


def adapt_christmas_collect(text, commemoration):
    if "FERIA" in commemoration.rank.name:
        text = text.replace("and to be born [this day] of a pure virgin:", "and to be born of a pure virgin:")
        text = text.replace("and [as at this time] to be born of a pure Virgin:", "and to be born of a pure Virgin:")
    else:
        text = text.replace("and to be born [this day] of a pure virgin:", "and to be born this day of a pure virgin:")
        text = text.replace(
            "and [as at this time] to be born of a pure Virgin:",
            "and as at this time to be born of a pure Virgin:",
        )
    return text


def get_collects_for_readings(service, commemoration, calendar_date, style="contemporary"):
    attr = "traditional_text" if style == "traditional" else "text"
    if calendar_date.proper and commemoration.rank.name in ["FERIA", "SUNDAY"]:
        return [getattr(calendar_date.proper.collect_1, attr)]
    if commemoration.collect_eve:
        if "Vigil" in commemoration.name or "Eve of" in commemoration.name or "Easter Vigil" in service:
            return [getattr(commemoration.collect_eve, attr)]
    if commemoration.collect_1:
        collects = [getattr(commemoration.collect_1, attr)]
        if commemoration.collect_2:
            collects.append(getattr(commemoration.collect_2, attr))
    else:
        collects = [getattr(commemoration.morning_prayer_collect, attr)]
    collects = [adapt_christmas_collect(collect, commemoration) for collect in collects]

    return collects


def service_readings_to_citations(readings):
    groups = defaultdict(list)

    for reading in readings:
        citations = {
            "full": reading["full"]["citation"],
            "abbreviated": reading["abbreviated"]["citation"],
        }
        groups[reading["full"]["reading_number"]].append(citations)

    return groups


def mass_readings(commemoration, mass_year, calendar_date, translation="esv", psalm_style="contemporary"):
    readings = commemoration.get_all_mass_readings_for_year(mass_year)
    passages = []
    for reading in readings:
        passages.append(reading.long_citation)
        if reading.short_citation:
            passages.append(reading.short_citation)
    final_readings = {}
    for reading in readings:
        service_name = reading.service or "-"
        name = get_reading_name_from_reading_number(reading)
        full = reading_format(
            name=name,
            citation=reading.long_citation,
            text=(
                getattr(reading.long_scripture, translation)
                if "psalm" not in reading.long_citation.lower()
                else get_psalms(
                    reading.long_citation.replace("Psalms", ""),
                    simplified_citations=True,
                    language_style=psalm_style,
                    headings="none",
                )
            ),
            testament=reading.testament,
            reading_number=reading.reading_number,
        )
        abbreviated = full
        if reading.short_citation:
            abbreviated = reading_format(
                name=name,
                citation=reading.short_citation,
                text=(
                    getattr(reading.short_scripture, translation)
                    if "psalm" not in reading.short_citation.lower()
                    else get_psalms(
                        reading.short_citation.replace("Psalms", ""),
                        simplified_citations=True,
                        language_style=psalm_style,
                        headings="none",
                    )
                ),
                testament=reading.testament,
            )
        if service_name not in final_readings.keys():
            final_readings[service_name] = []
        final_readings[service_name].append(
            {
                "full": full,
                "abbreviated": abbreviated,
            }
        )
    result = {}
    for service, readings in final_readings.items():
        result[service] = {
            "collects": get_collects_for_readings(service, commemoration, calendar_date),
            "traditional_collects": get_collects_for_readings(
                service, commemoration, calendar_date, style="traditional"
            ),
            "readings": final_readings[service],
            "citations": service_readings_to_citations(final_readings[service]),
            "type": "mass",
        }
    return result


class ReadingsSerializer(serializers.Serializer):
    services = serializers.SerializerMethodField()
    calendarDate = DaySerializer(source="date")

    def get_services(self, obj):
        services = {}
        if obj.holy_day_readings:
            name = obj.holy_day_readings.commemoration.name
            services[f"Morning Prayer ({name})"] = [
                morning_prayer_30_day_psalms(obj),
                holy_day_morning_prayer_60_day_psalms(obj),
                holy_day_morning_prayer_reading_1(obj),
                holy_day_morning_prayer_reading_2(obj),
            ]
            services[f"Evening Prayer ({name})"] = [
                evening_prayer_30_day_psalms(obj),
                holy_day_evening_prayer_60_day_psalms(obj),
                holy_day_evening_prayer_reading_1(obj),
                holy_day_evening_prayer_reading_2(obj),
            ]
            services["Morning Prayer (Sequential)"] = [
                morning_prayer_30_day_psalms(obj),
                standard_morning_prayer_60_day_psalms(obj),
                standard_morning_prayer_reading_1(obj),
                standard_morning_prayer_reading_2(obj),
            ]
            services["Evening Prayer (Sequential)"] = [
                evening_prayer_30_day_psalms(obj),
                standard_evening_prayer_60_day_psalms(obj),
                standard_evening_prayer_reading_1(obj),
                standard_evening_prayer_reading_2(obj),
            ]
        else:
            name = f" ({obj.date.primary.name})" if obj.standard_readings.holy_day_name else ""
            services[f"Morning Prayer{name}"] = [
                morning_prayer_30_day_psalms(obj),
                standard_morning_prayer_60_day_psalms(obj),
                standard_morning_prayer_reading_1(obj),
                standard_morning_prayer_reading_2(obj),
            ]
            services[f"Evening Prayer{name}"] = [
                evening_prayer_30_day_psalms(obj),
                standard_evening_prayer_60_day_psalms(obj),
                standard_evening_prayer_reading_1(obj),
                standard_evening_prayer_reading_2(obj),
            ]
        for key, value in services.items():
            services[key] = {
                "collects": [],
                "traditional_collects": [],
                "readings": value,
                "type": "daily_office",
                "name": key,
            }
        ferias = {}
        non_ferias = {}
        for commemoration in obj.date.morning_and_evening:
            masses = mass_readings(commemoration, obj.mass_year, obj.date, obj.translation, obj.psalms)
            for mass, readings in masses.items():
                name = f"{commemoration.name} ({mass}) " if mass not in ["", "-"] else f"{commemoration.name}"
                if "FERIA" in commemoration.rank.name:
                    ferias[name] = readings
                    ferias[name]["name"] = name
                    ferias[name]["rank"] = commemoration.rank.name
                else:
                    non_ferias[name] = readings
                    non_ferias[name]["name"] = name
                    non_ferias[name]["rank"] = commemoration.rank.name
        services.update(non_ferias)
        services.update(ferias)
        return services


class AudioViewSet(ViewSet):
    permission_classes = [AllowAny]

    @csrf_exempt
    def retrieve(self, request):
        data = json.loads(request.body)
        content = data.get("content", None)
        if not content:
            return Response({"path": ""})
        line_type = data.get("line_type", "leader")
        if "leader" in line_type:
            voice_type = "alloy"
        elif "congregation" in line_type:
            voice_type = "ash"
        elif "html" in line_type:
            voice_type = "echo"
        else:
            return Response({"path": ""})
        audio_id = generate_uuid_from_string(f"{line_type} {voice_type} {content}")
        filename = f"{audio_id}.mp3"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        if exists:
            return Response({"path": file_url})
        try:
            from pathlib import Path
            from openai import OpenAI

            client = OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_type,
                input=content,
            )
            response.stream_to_file(file_path)
        except Exception as e:
            return Response({"error": str(e)})
        return Response({"path": file_url})


class MorningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):

        office = MorningPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class FamilyMorningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = FamilyMorningPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class FamilyMiddayPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = FamilyMiddayPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class FamilyEarlyEveningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = FamilyEarlyEveningPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class FamilyCloseOfDayPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = FamilyCloseOfDayPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class EveningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = EveningPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class MiddayPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = MiddayPrayer(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class ComplineView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = Compline(request, year, month, day)
        if request.GET.get("include_audio_links"):
            serializer = OfficeAudioSerializer(office)
        else:
            serializer = OfficeSerializer(office)
        return Response(serializer.data)


class ReadingsView(OfficeAPIView):
    def get(self, request, year, month, day):
        translation = request.GET.get("translation", "esv")
        psalms = request.GET.get("psalms", "contemporary")
        style = request.GET.get("style", "whole_verse")
        office = Readings(request, year, month, day, translation, psalms, style)
        serializer = ReadingsSerializer(office)
        return Response(serializer.data)


class GreatLitanyAloneModule(Module):
    def __init__(self, style, portion="both", *args, **kwargs):
        self.style = style
        self.portion = portion
        self.name = self.build_name(self.style, self.portion)
        super().__init__(*args, **kwargs)

    @staticmethod
    def build_name(style, portion):
        name = ""
        if portion == "both":
            name += "The Great Litany and the Supplication"
        if portion == "litany":
            name += "The Great Litany (with short ending)"
        if portion == "supplication":
            name += "The Supplication"

        if style == "traditional":
            name += " (Traditional)"

        if style == "contemporary":
            name += " (Contemporary)"

        return name

    def get_lines(self):
        style = self.style
        kyrie = file_to_lines("kyrie_contemporary") if style == "contemporary" else file_to_lines("kyrie_traditional")
        pater = file_to_lines("pater_contemporary") if style == "contemporary" else file_to_lines("pater_traditional")
        template = "great_litany_traditional" if style == "traditional" else "great_litany"
        supplication_template = "supplication_traditional" if style == "traditional" else "supplication"
        supplication_optional_template = (
            "supplication_optional_traditional" if style == "traditional" else "supplication_optional"
        )
        short_ending_template = (
            "great_litany_short_ending_traditional" if style == "traditional" else "great_litany_short_ending"
        )

        if self.portion == "both":
            return (
                file_to_lines(template)
                + [Line("", "spacer")]
                + kyrie
                + [Line("", "spacer")]
                + pater
                + [Line("", "spacer")]
                + file_to_lines(supplication_template)
                + file_to_lines(supplication_optional_template)
            )
        if self.portion == "litany":
            return (
                file_to_lines(template)
                + [Line("", "spacer")]
                + kyrie
                + [Line("", "spacer")]
                + pater
                + [Line("", "spacer")]
                + file_to_lines(short_ending_template)
            )
        if self.portion == "supplication":
            return file_to_lines(supplication_template) + file_to_lines(supplication_optional_template)


class GreatLitanyModuleCollection:
    def get_modules(self):
        return (
            GreatLitanyAloneModule(style="traditional"),
            GreatLitanyAloneModule(style="contemporary"),
            GreatLitanyAloneModule(style="traditional", portion="litany"),
            GreatLitanyAloneModule(style="contemporary", portion="litany"),
            GreatLitanyAloneModule(style="traditional", portion="supplication"),
            GreatLitanyAloneModule(style="contemporary", portion="supplication"),
        )


class GreatLitanyView(OfficeAPIView):
    def get(self, request):
        serializer = GenericDailyOfficeSerializer(GreatLitanyModuleCollection())
        return Response(serializer.data)


class SettingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingOption
        fields = (
            "uuid",
            "name",
            "description",
            "value",
            "order",
            "abbreviation",
        )


class SettingSerializer(serializers.ModelSerializer):
    options = SettingOptionSerializer(many=True, source="settingoption_set")
    site_name = serializers.SerializerMethodField()
    setting_type_name = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        sites = dict(Setting.SETTING_SITES)
        return sites[obj.site]

    def get_setting_type_name(self, obj):
        setting_types = dict(Setting.SETTING_TYPES)
        return setting_types[obj.setting_type]

    class Meta:
        model = Setting
        fields = (
            "uuid",
            "name",
            "title",
            "description",
            "site",
            "site_name",
            "setting_type",
            "setting_type_name",
            "order",
            "setting_string_order",
            "options",
        )


class AvailableSettings(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SettingSerializer
    queryset = (
        Setting.objects.prefetch_related(
            Prefetch("settingoption_set", queryset=SettingOption.objects.order_by("order"))
        )
        .order_by("site", "setting_type", "order")
        .all()
    )


# heading
# subheading
# citation
# html
# leader
# congregation
# rubric
# leader_dialogue
# congregation_dialogue


def heading(content):
    return "<h2>{}</h2>".format(content)


def subheading(content):
    return "<h4>{}</h4>".format(content)


def citation(content):
    return "<h5>{}</h5>".format(content)


def html_content(content):
    return content


def leader(content, indented=False):
    if indented:
        return "<p class='indent'>{}</p>".format(content)
    return "<p class='handing-indent'>{}</p>".format(content)


def congregation(content, indented=False):
    if indented:
        return "<p class='indent'><strong>{}</strong></p>".format(content)
    return "<p class='handing-indent'><strong>{}</strong></p>".format(content)


def rubric(content):
    return "<p><em>{}</em></p>".format(content)


def leader_dialogue(content, indented=False):
    return leader(content, indented)


def congregation_dialogue(content, indented=False):
    return congregation(content, indented)


def line_to_html(line):
    if line["line_type"] == "heading":
        return heading(line["content"])
    if line["line_type"] == "subheading":
        return subheading(line["content"])
    if line["line_type"] == "citation":
        return citation(line["content"])
    if line["line_type"] == "html":
        return html_content(line["content"])
    if line["line_type"] == "leader":
        return leader(line["content"], line["indented"])
    if line["line_type"] == "congregation":
        return congregation(line["content"], line["indented"])
    if line["line_type"] == "rubric":
        return rubric(line["content"])
    if line["line_type"] == "leader_dialogue":
        return leader_dialogue(line["content"], line["indented"])
    if line["line_type"] == "congregation_dialogue":
        return congregation_dialogue(line["content"], line["indented"])
    return line["content"]


def json_modules_to_html(modules, request=None):
    html = ""
    for module in modules:
        for line in module["lines"]:
            html += line_to_html(line)
    return render_to_string("display_base.html", {"content": mark_safe(html)})


class MorningPrayerDisplayView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = MorningPrayer(request, year, month, day)
        serializer = OfficeSerializer(office)
        return HttpResponse(json_modules_to_html(serializer.data["modules"], request), content_type="text/html")


class NoondayPrayerDisplayView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = MorningPrayer(request, year, month, day)
        serializer = OfficeSerializer(office)
        return HttpResponse(json_modules_to_html(serializer.data["modules"], request), content_type="text/html")


class EmailSignupView(OfficeAPIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        email = request.data.get("email")
        if not email:
            raise ValidationError("Please provide a valid email address.", 400)
        try:
            client = MailchimpMarketing.Client()
            client.set_config(
                {
                    "api_key": settings.MAILCHIMP_API_KEY,
                    "server": settings.MAILCHIMP_PREFIX,
                }
            )
            ip = get_client_ip(request)
            time_submitted = datetime.datetime.utcnow().isoformat().split(".")[0] + "Z"
            client.lists.set_list_member(
                settings.MAILCHIMP_LIST_ID,
                email,
                {
                    "email_address": email,
                    "skip_merge_validation": True,
                    "status": "subscribed",
                    "ip_signup": ip,
                    "ip_opt": ip,
                    "timestamp_signup": time_submitted,
                    "timestamp_opt": time_submitted,
                },
            )
        except ApiClientError as e:
            try:
                data = json.loads(e.text)
                if "errors" in data.keys():
                    error = "; ".join(["{}: {}".format(error["field"], error["message"]) for error in data["errors"]])
                else:
                    error = data["detail"]
            except Exception as c:
                raise ValidationError("Unknown error. Please reach out to feedback@dailyofice2019.com", 400)
            raise ValidationError(error, 400)
        except Exception as e:
            print(e)
            raise ValidationError("Unknown error. Please reach out to feedback@dailyofice2019.com", 400)
        return Response({"success": True})

from calendar import monthrange

from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear
from office.models import HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay


class DayView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        date = timezone.now().replace(year=year, month=month, day=day)
        calendar_date = get_calendar_date(date)
        serializer = DaySerializer(calendar_date)
        return Response(serializer.data)


class MonthView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year):
        church_year = cache.get(str(year))
        if not church_year:
            church_year = ChurchYear(year)
            cache.set(str(year), church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year.date.m], many=True)
        return Response(serializer.data)


class YearView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year):
        church_year = cache.get(str(year))
        if not church_year:
            church_year = ChurchYear(year)
            cache.set(str(year), church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year], many=True)
        return Response(serializer.data)


class Settings(object):

    DEFAULT_SETTINGS = {
        "setting_psalter": "60",
        "setting_reading_cycle": "1",
        "setting_reading_length": "full",
        "setting_reading_audio": "off",
        "setting_canticle_rotation": "default",
        "setting_theme": "theme-auto",
        "setting_lectionary": "daily-office-readings",
        "setting_confession": "long-on-fast",
        "setting_absolution": "lay",
        "setting_morning_prayer_invitatory": "invitatory_traditional",
        "setting_reading_headings": "off",
        "setting_language_style": "traditional",
        "setting_national_holidays": "all",
        "setting_suffrages": "rotating",
        "setting_collects": "rotating",
        "setting_pandemic_prayers": "pandemic_yes",
        "setting_mp_great_litany": "mp_litany_off",
        "setting_ep_great_litany": "ep_litany_off",
        "setting_general_thanksgiving": "on",
        "setting_chrysostom": "on",
        "setting_grace": "rotating",
        "setting_o_antiphons": "literal",
    }

    def __init__(self, request):
        self.settings = self._get_settings(request)

    def get_setting(self, name):
        name = name.lower()
        try:
            return self.settings[name]
        except KeyError:
            return False

    def __getitem__(self, key):
        key = key.lower()
        try:
            return self.settings[key]
        except KeyError:
            return False

    def _get_settings(self, request):

        settings = self.DEFAULT_SETTINGS
        specified_settings = {k: v for (k, v) in request.query_params.items() if k in settings.keys()}
        for k, v in settings.items():
            if k in specified_settings.keys():
                settings[k] = specified_settings[k]
        return settings


class Module(object):
    def __init__(self, office):
        self.office = office

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def get_data(self):
        raise NotImplementedError("You must implement this method.")

    @cached_property
    def json(self):
        return {"name": self.get_name(), "data": self.get_data()}


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

    def get_data(self):
        sentence = self.get_sentence()
        return [
            {"type": "heading", "content": "Opening Sentence"},
            {"type": "body", "content": sentence["sentence"]},
            {"type": "citation", "content": sentence["citation"]},
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


class MorningPrayer(Office):
    def get_modules(self):
        return [MPOpeningSentence(self)]


class OfficeAPIView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        raise NotImplementedError("You must implement this method.")


class OfficeSerializer(serializers.Serializer):
    modules = serializers.SerializerMethodField()

    def get_modules(self, obj):
        return {"data": [module.json for module in obj.get_modules()]}


class MorningPrayerView(OfficeAPIView):
    def get(self, request, year, month, day):
        office = MorningPrayer(request, year, month, day)
        serializer = OfficeSerializer(office)
        return Response(serializer.data)

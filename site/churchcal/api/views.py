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

        settings = self.DEFAULT_SETTINGS
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


class Line(dict):
    def __init__(self, content, line_type="congregation", indented=False):
        super().__init__(content=content, line_type=line_type, indented=indented)


class Module(object):
    def __init__(self, office):
        self.office = office

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def get_lines(self):
        raise NotImplementedError("You must implement this method.")

    @cached_property
    def json(self):
        return {"name": self.get_name(), "lines": self.get_lines()}


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
        return [Line("Opening Sentence", "heading"), Line(sentence["sentence"]), Line(sentence["citation"], False)]


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
        print(self.office.settings)
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return [
                Line(
                    "Dearly beloved, the Scriptures teach us to acknowledge our many sins and offenses, not concealing them from our heavenly Father, but confessing them with humble and obedient hearts that we may obtain forgiveness by his infinite goodness and mercy. We ought at all times humbly to acknowledge our sins before Almighty God, but especially when we come together in his presence to give thanks for the great benefits we have received at his hands, to declare his most worthy praise, to hear his holy Word, and to ask, for ourselves and on behalf of others, those things which are necessary for our life and our salvation. Therefore, draw near with me to the throne of heavenly grace.",
                    "leader",
                )
            ]
        return [Line("Let us humbly confess our sins to Almighty God.", "leader")]

    def get_body_lines(self):
        return [
            Line("Almighty and most merciful Father,"),
            Line("we have erred and strayed from your ways like lost sheep.", indented=True),
            Line("We have followed too much the devices and desires"),
            Line("of our own hearts.", indented=True),
            Line("We have offended against your holy laws."),
            Line("We have left undone those things which we ought to have done,"),
            Line("and we have done those things which we ought not", indented=True),
            Line("to have done;", indented=True),
            Line("and apart from your grace, there is no health in us."),
            Line("O Lord, have mercy upon us."),
            Line("Spare all those who confess their faults."),
            Line("Restore all those who are penitent, according to your promises"),
            Line("declared to all people in Christ Jesus our Lord.", indented=True),
            Line("And grant, O most merciful Father, for his sake,"),
            Line("that we may now live a godly, righteous, and sober life,", indented=True),
            Line("to the glory of your holy Name. Amen.", indented=True),
        ]

    def get_absolution_lines(self):
        lay = self.office.settings["absolution"] == "lay"
        if lay:
            return [
                Line("A Deacon or layperson remains kneeling and prays", "rubric"),
                Line(
                    "Grant to your faithful people, merciful Lord, pardon and peace; that we may be cleansed from all our sins, and serve you with a quiet mind; through Jesus Christ our Lord.",
                    "leader",
                ),
                Line("Amen."),
            ]
        setting = self.office.settings["confession"]
        fast = self.office.date.fast_day
        long = (setting == "long") or (setting == "long-on-fast" and fast)
        if long:
            return [
                Line("The Priest alone stands and says", "rubric"),
                Line(
                    "Almighty God, the Father of our Lord Jesus Christ, desires not the death of sinners, but that they may turn from their wickedness and live. He has empowered and commanded his ministers to pronounce to his people, being penitent, the absolution and remission of their sins. He pardons and absolves all who truly repent and genuinely believe his holy Gospel. For this reason, we beseech him to grant us true repentance and his Holy Spirit, that our present deeds may please him, the rest of our lives may be pure and holy, and that at the last we may come to his eternal joy; through Jesus Christ our Lord.",
                    "leader",
                ),
                Line("Amen."),
            ]
        return [
            Line("The Priest alone stands and says", "rubric"),
            Line(
                "The Almighty and merciful Lord grant you absolution and remission of all your sins, true repentance, amendment of life, and the grace and consolation of his Holy Spirit."
            ),
            Line("Amen."),
        ]

    def get_lines(self):
        return (
            [Line("Confession of Sin", "heading")]
            + [Line("The Officiant says to the People", "rubric")]
            + self.get_intro_lines()
            + self.get_body_lines()
            + self.get_absolution_lines(),
        )


class Preces(Module):

    name = "Preces"

    def get_lines(self):
        return [
            Line("The Preces", "heading"),
            Line("All stand.", "rubric"),
            Line("O Lord, open our lips;", "leader"),
            Line("And our mouth shall proclaim your praise."),
            Line("O God, make speed to save us;", "leader"),
            Line("O Lord, make haste to help us."),
            Line("Glory be to the Father, and to the Son, and to the Holy Spirit;", "leader"),
            Line("As it was in the beginning, is now, and ever shall be, world without end. Amen."),
            Line("Praise the Lord.", "leader"),
            Line("The Lord’s Name be praised."),
        ]


class MorningPrayer(Office):
    def get_modules(self):
        return [MPOpeningSentence(self), Confession(self), Preces(self)]


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

import datetime

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.models import HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay


class Office(object):

    name = "Daily Office"
    modules = []

    def get_formatted_date_string(self):
        return "{dt:%A} {dt:%B} {dt.day}, {dt.year}".format(dt=self.date.date)

    def __init__(self, date):
        from churchcal.calculations import get_calendar_date

        self.date = get_calendar_date(date)

        try:
            self.office_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except HolyDayOfficeDay.DoesNotExist:
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)

        primary_feast_name = (
            self.date.primary_evening.name
            if self.name == "Evening Prayer" or self.name == "Compline"
            else self.date.primary.name
        )
        self.title = "{} for {}: {} | The Daily Office according to The Book of Common Prayer (2019)".format(
            self.name, self.get_formatted_date_string(), primary_feast_name
        )

    @cached_property
    def links(self):

        today = self.date.date
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        return {
            "yesterday": {
                "label": yesterday.strftime("%a"),
                "link": reverse(self.office, args=[yesterday.year, yesterday.month, yesterday.day]),
            },
            "tomorrow": {
                "label": tomorrow.strftime("%a"),
                "link": reverse(self.office, args=[tomorrow.year, tomorrow.month, tomorrow.day]),
            },
            "morning_prayer": {
                "label": "Morning",
                "link": reverse("morning_prayer", args=[today.year, today.month, today.day]),
            },
            "midday_prayer": {
                "label": "Midday",
                "link": reverse("midday_prayer", args=[today.year, today.month, today.day]),
            },
            "evening_prayer": {
                "label": "Evening",
                "link": reverse("evening_prayer", args=[today.year, today.month, today.day]),
            },
            "compline": {"label": "Compline", "link": reverse("compline", args=[today.year, today.month, today.day])},
            "family_morning_prayer": {
                "label": "Morning",
                "link": reverse("family_morning_prayer", args=[today.year, today.month, today.day]),
            },
            "family_midday_prayer": {
                "label": "Midday",
                "link": reverse("family_midday_prayer", args=[today.year, today.month, today.day]),
            },
            "family_early_evening_prayer": {
                "label": "Early Evening",
                "link": reverse("family_early_evening_prayer", args=[today.year, today.month, today.day]),
            },
            "family_close_of_day_prayer": {
                "label": "Close of Day",
                "link": reverse("family_close_of_day_prayer", args=[today.year, today.month, today.day]),
            },
            "current": self.office,
            "date": f"{today:%B} {today.day}, {today.year}",
        }


class OfficeSection(object):
    def __init__(self, date, office_readings=None, thirty_day_psalter_day=None, office=None):
        self.date = date
        self.office_readings = office_readings
        self.thirty_day_psalter_day = thirty_day_psalter_day
        self.office = office

    @cached_property
    def data(self):
        raise NotImplementedError


class Confession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin", "fast_day": self.date.fast_day}


class Invitatory(OfficeSection):
    @cached_property
    def data(self):
        return {}


class Creed(OfficeSection):
    @cached_property
    def data(self):
        return {}


class Prayers(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Prayers"}


class Intercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "Intercessions",
            "rubric_1": "The Officiant may invite the People to offer intercessions and thanksgivings.",
            "rubric_2": "A hymn or anthem may be sung.",
        }


class GeneralThanksgiving(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The General Thanksgiving"}


class Chrysostom(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "A PRAYER OF ST. JOHN CHRYSOSTOM"}


class Dismissal(OfficeSection):
    def get_fixed_grace(self):

        return {
            "officiant": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Spirit, be with us all evermore.",
            "people": "Amen.",
            "citation": "2 CORINTHIANS 13:14",
        }

    def get_grace(self):

        if self.date.date.weekday() in (6, 2, 5):
            return {
                "officiant": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Spirit, be with us all evermore.",
                "people": "Amen.",
                "citation": "2 CORINTHIANS 13:14",
            }

        if self.date.date.weekday() in (0, 3):
            return {
                "officiant": "May the God of hope fill us with all joy and peace in believing through the power of the Holy Spirit. ",
                "people": "Amen.",
                "citation": "ROMANS 15:13",
            }

        if self.date.date.weekday() in (1, 4):
            return {
                "officiant": "Glory to God whose power, working in us, can do infinitely more than we can ask or imagine: Glory to him from generation to generation in the Church, and in Christ Jesus for ever and ever.",
                "people": "Amen.",
                "citation": "EPHESIANS 3:20-21",
            }

    @cached_property
    def data(self):

        morning_easter = self.office.office not in ["evening_prayer"] and self.date.season.name == "Eastertide"
        evening_easter = self.office.office in ["evening_prayer"] and self.date.evening_season.name == "Eastertide"

        officiant = "Let us bless the Lord."
        people = "Thanks be to God."

        if morning_easter or evening_easter:

            officiant = "{} Alleluia, alleluia.".format(officiant)
            people = "{} Alleluia, alleluia.".format(people)

        return {
            "heading": "Dismissal",
            "officiant": officiant,
            "people": people,
            "grace": self.get_grace(),
            "fixed_grace": self.get_fixed_grace(),
        }


class FMCreed(OfficeSection):
    @cached_property
    def data(self):
        return {}


class FamilyRubricSection(OfficeSection):
    @cached_property
    def data(self):
        return {
            "rubric": mark_safe(
                "<br>These devotions follow the basic structure of the Daily Office of the Church and are particularly appropriate for families with young children.<br><br>The Reading and the Collect may be read by one person, and the other parts said in unison, or in some other convenient manner."
            )
        }


class FamilyIntercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "title": "Intercessions",
            "rubric": mark_safe(
                "A hymn or canticle may be used.<br><br>Prayers may be offered for ourselves and others."
            ),
        }


class GreatLitany(OfficeSection):
    def get_names(self):
        names = [
            feast.saint_name for feast in self.date.all_evening if hasattr(feast, "saint_name") and feast.saint_name
        ]
        names = ["the Blessed Virgin Mary"] + names
        return ", ".join(names)

    def get_leaders(self):
        parts = [
            '<span class="us">your servant Donald Trump, the President, </span>',
            '<span class="canada">your servants Her Majesty Queen Elizabeth, the Sovereign, and Justin Trudeau, the Prime Minister, </span>'
            '<span class="national_none">your servants, our national leaders, </span>',
        ]
        return mark_safe("".join(parts))

    def get_weekday_class(self):
        if self.office.office == "evening_prayer":
            start = "litany-ep-"
        else:
            start = "litany-mp-"
        if self.date.date.weekday() in (2, 4, 6):
            return start + "wfs"
        return start + "not-wfs"

    @cached_property
    def data(self):
        return {"names": self.get_names(), "leaders": self.get_leaders(), "weekday_class": self.get_weekday_class()}

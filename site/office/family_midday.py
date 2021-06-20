import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.evening_prayer import EPCollectsOfTheDay
from office.midday_prayer import MiddayPrayers
from office.morning_prayer import MPCommemorationListing, MPOpeningSentence
from office.offices import Office, OfficeSection, FamilyRubricSection
from psalter.utils import get_psalms


class FamilyMidday(Office):

    name = "Family Prayer at Midday"
    office = "family_midday_prayer"

    start_time = "12:00 PM"

    family = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Prayer Book: {}".format(
            self.name,
            self.get_formatted_date_string(),
            self.date.primary.name,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=16, second=0)
        self.end_time = self.start_time.replace(minute=59, hour=23, second=59)

    @cached_property
    def modules(self):
        return [
            (FNHeading(self.date), "office/heading.html"),
            (MPCommemorationListing(self.date), "office/commemoration_listing.html"),
            (FamilyRubricSection(self.date, self.office_readings), "office/rubric_section.html"),
            (FNOpeningSentence(self.date, self.office_readings), "office/family_opening_sentence.html"),
            (FNPsalms(self.date, self.office_readings), "office/minor_office_psalms.html"),
            (FNScripture(self.date, self.office_readings), "office/family_scripture.html"),
            (FNIntercessions(self.date, self.office_readings), "office/rubric_section.html"),
            (Pater(self.date, self.office_readings), "office/family_lords_prayer.html"),
            (FPCollect(self.date, self.office_readings), "office/family_collect.html"),
        ]


class FNHeading(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": mark_safe("Family Prayer<br>At Midday"),
            "rubric": mark_safe(
                "These devotions follow the basic structure of the Daily Office of the Church and are particularly appropriate for families with young children.<br><br>The Reading and the Collect may be read by one person, and the other parts said in unison, or in some other convenient manner."
            ),
            "calendar_date": self.date,
        }


class FNOpeningSentence(OfficeSection):
    def get_sentences(self):

        return {
            "seasonal": MPOpeningSentence(self.date, self.office_readings).get_sentence(),
            "fixed": {
                "sentence": "Blessed be the God and Father of our Lord Jesus Christ, who has blessed us in Christ with every spiritual blessing in the heavenly places.",
                "citation": "EPHESIANS 1:3",
            },
        }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentences": self.get_sentences()}


class FNPsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Psalm", "psalms": get_psalms("113:1-4")}


class FNScripture(OfficeSection):
    def get_long(self):
        return {
            "passage": self.office_readings.mp_reading_2,
            "text": self.office_readings.mp_reading_2_text,
            "deuterocanon": self.office_readings.mp_reading_2_testament == "DC",
        }

    def get_scripture(self):

        day_of_year = self.date.date.timetuple().tm_yday
        number = day_of_year % 2

        scriptures = [
            {
                "sentence": "Abide in me, and I in you. As the branch cannot bear fruit by itself, unless it abides in the vine, neither can you, unless you abide in me. I am the vine; you are the branches. Whoever abides in me and I in him, he it is that bears much fruit, for apart from me you can do nothing.",
                "citation": "JOHN 15:4-5",
            },
            {
                "sentence": "Do not be anxious about anything, but in everything by prayer and supplication with thanksgiving let your requests be made known to God. And the peace of God, which surpasses all understanding, will guard your hearts and your minds in Christ Jesus.",
                "citation": "PHILIPPIANS 4:6-7",
            },
        ]

        return scriptures[number]

    @cached_property
    def data(self):
        return {
            "heading": "A READING FROM HOLY SCRIPTURE",
            "long": self.get_long(),
            "brief": self.get_scripture(),
            "hide_closing": True,
        }


class FNIntercessions(OfficeSection):
    @cached_property
    def data(self):
        return {"title": "Intercessions", "rubric": mark_safe("Prayers may be offered for ourselves and others.")}


class Pater(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Lord's Prayer"}


class FPCollect(OfficeSection):
    def get_day_of_week_collect(self):
        collects = MiddayPrayers.collects

        if self.date.date.weekday() in [6]:  # Sunday
            collect = collects[1]

        if self.date.date.weekday() in [0, 5]:  # Monday,  #Saturday
            collect = collects[2]

        if self.date.date.weekday() in [1]:  # Tuesday
            collect = collects[3]

        if self.date.date.weekday() in [2]:  # Wednesday
            collect = collects[0]

        if self.date.date.weekday() in [3]:  # Thursday
            collect = collects[1]

        if self.date.date.weekday() in [4]:  # Friday
            collect = collects[0]

        return (None, None, collect)

    @cached_property
    def data(self):

        day_of_year = next(EPCollectsOfTheDay(self.date, self.office_readings).data["collects"])
        day_of_week = self.get_day_of_week_collect()

        return {
            "heading": "The Collect",
            "time_of_day": "Blessed Savior, at this hour you hung upon the Cross, stretching out your loving arms: Grant that all the peoples of the earth may look to you and be saved; for your tender mercies’ sake.",
            "day_of_year": day_of_year,
            "day_of_week": day_of_week,
        }

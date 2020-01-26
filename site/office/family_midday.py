import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.morning_prayer import MPCommemorationListing
from office.offices import Office, OfficeSection
from psalter.utils import get_psalms


class FamilyMidday(Office):

    name = "Family Prayer at Midday"
    office = "family_midday_prayer"

    start_time = "7:00 AM"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Psalms (30 Day Cycle): {}, Psalms (60 Day Cycle): {}, First Reading: {}, Second Reading: {}, Prayer Book: {}".format(
            "Daily Evening Prayer",
            self.get_formatted_date_string(),
            self.date.primary_evening.name,
            self.thirty_day_psalter_day.mp_psalms.replace(",", " "),
            self.office_readings.mp_psalms.replace(",", " "),
            self.office_readings.mp_reading_1,
            self.office_readings.mp_reading_2,
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
            (FNOpeningSentence(self.date, self.office_readings), "office/opening_sentence.html"),
            (FNPsalms(self.date, self.office_readings), "office/minor_office_psalms.html"),
            (FNScripture(self.date, self.office_readings), "office/minor_office_scripture.html"),
            (Pater(self.date, self.office_readings), "office/family_lords_prayer.html"),
            (FPCollect(self.date, self.office_readings), "office/family_collect.html"),
        ]


class FNHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Family Prayer<br>At Midday"), "calendar_date": self.date}


class FNOpeningSentence(OfficeSection):
    def get_sentence(self):
        return {
            "sentence": "Blessed be the God and Father of our Lord Jesus Christ, who has blessed us in Christ with every spiritual blessing in the heavenly places.",
            "citation": "EPHESIANS 1:3",
        }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentence": self.get_sentence()}


class FNPsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Psalm", "psalms": get_psalms("113:1-4")}


class FNScripture(OfficeSection):
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
        return {"heading": "A READING FROM HOLY SCRIPTURE", "sentence": self.get_scripture(), "hide_closing": True}


class Pater(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Lord's Prayer"}


class FPCollect(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The Collect",
            "collect": "Blessed Savior, at this hour you hung upon the Cross, stretching out your loving arms: Grant that all the peoples of the earth may look to you and be saved; for your tender mercies’ sake.",
        }

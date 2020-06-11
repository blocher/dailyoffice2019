import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.evening_prayer import EPReading1
from office.morning_prayer import MPCommemorationListing, MPCollectsOfTheDay, MPCollects, MPOpeningSentence
from office.offices import Office, OfficeSection, FMCreed, FamilyRubricSection, FamilyIntercessions
from psalter.utils import get_psalms


class FamilyMorning(Office):

    name = "Family Prayer in the Morning"
    office = "family_morning_prayer"

    start_time = "7:00 AM"

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
            (FMHeading(self.date), "office/heading.html"),
            (MPCommemorationListing(self.date), "office/commemoration_listing.html"),
            (FamilyRubricSection(self.date, self.office_readings), "office/rubric_section.html"),
            (FMOpeningSentence(self.date, self.office_readings), "office/family_opening_sentence.html"),
            (FMPsalms(self.date, self.office_readings), "office/minor_office_psalms.html"),
            (FMScripture(self.date, self.office_readings), "office/family_scripture.html"),
            (FMCreed(self.date, self.office_readings), "office/family_creed.html"),
            (FMIntercessions(self.date, self.office_readings), "office/rubric_section.html"),
            (Pater(self.date, self.office_readings), "office/family_lords_prayer.html"),
            (FMCollect(self.date, self.office_readings), "office/family_collect.html"),
        ]


class FMHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Family Prayer<br>In the Morning"), "calendar_date": self.date}


class FMOpeningSentence(OfficeSection):
    def get_sentences(self):

        return {
            "seasonal": MPOpeningSentence(self.date, self.office_readings).get_sentence(),
            "fixed": {
                "sentence": "O Lord, open my lips, and my mouth shall show forth your praise.",
                "citation": "PSALM 51:15",
            },
        }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentences": self.get_sentences()}


class FMPsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Psalm", "psalms": get_psalms("51:10-12")}


class FMScripture(OfficeSection):
    def get_scripture(self):

        day_of_year = self.date.date.timetuple().tm_yday
        number = day_of_year % 3

        scriptures = [
            {
                "sentence": "Blessed be the God and Father of our Lord Jesus Christ! According to his great mercy, he has caused us to be born again to a living hope through the resurrection of Jesus Christ from the dead.",
                "citation": "1 PETER 1:3",
            },
            {
                "sentence": "Give thanks to the Father, who has qualified you to share in the inheritance of the saints in light. He has delivered us from the domain of darkness and transferred us to the kingdom of his beloved Son, in whom we have redemption, the forgiveness of sins.",
                "citation": "COLOSSIANS 1:12-14",
            },
            {
                "sentence": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God. Set your minds on things that are above, not on things that are on earth. For you have died, and your life is hidden with Christ in God. When Christ who is your life appears, then you also will appear with him in glory.",
                "citation": "COLOSSIANS 3:1-4",
            },
        ]

        return scriptures[number]

    @cached_property
    def data(self):
        mp_reading = EPReading1(self.date, self.office_readings)
        return {
            "heading": "A READING FROM HOLY SCRIPTURE",
            "long": mp_reading.data,
            "brief": self.get_scripture(),
            "hide_closing": True,
        }


class FMIntercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "title": "Intercessions",
            "rubric": mark_safe(
                "A hymn or canticle may be used.<br><br>Prayers may be offered for ourselves and others."
            ),
        }


class Pater(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Lord's Prayer"}


class FMCollect(OfficeSection):
    @cached_property
    def data(self):

        day_of_year = next(MPCollectsOfTheDay(self.date, self.office_readings).data["collects"])
        day_of_week = MPCollects(self.date, self.office_readings).data["collect"]

        return {
            "heading": "The Collect",
            "time_of_day": "O Lord, our heavenly Father, almighty and everlasting God, you have brought us safely to the beginning of this day: Defend us by your mighty power, that we may not fall into sin nor run into any danger; and that, guided by your Spirit, we may do what is righteous in your sight; through Jesus Christ our Lord. ",
            "day_of_year": day_of_year,
            "day_of_week": day_of_week,
        }

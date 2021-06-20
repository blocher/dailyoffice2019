import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.evening_prayer import (
    EPInvitatory,
    EPCommemorationListing,
    EPCollects,
    EPCollectsOfTheDay,
    EPOpeningSentence,
)
from office.offices import Office, OfficeSection, FMCreed


class FamilyEarlyEvening(Office):

    name = "Family Prayer in the Early Evening"
    office = "family_early_evening_prayer"

    start_time = "4:00 PM"

    family = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Prayer Book: {}".format(
            self.name,
            self.get_formatted_date_string(),
            self.date.primary_evening.name,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=16, second=0)
        self.end_time = self.start_time.replace(minute=59, hour=23, second=59)

    @cached_property
    def modules(self):
        return [
            (FEEHeading(self.date), "office/heading.html"),
            (EPCommemorationListing(self.date), "office/commemoration_listing.html"),
            (FEERubricSection(self.date, self.office_readings), "office/rubric_section.html"),
            (FEEOpeningSentence(self.date, self.office_readings), "office/family_opening_sentence.html"),
            (EPInvitatory(self.date), "office/evening_prayer/hymn.html"),
            (FEEScripture(self.date, self.office_readings), "office/family_scripture.html"),
            (FMCreed(self.date, self.office_readings), "office/family_creed.html"),
            (FEEIntercessions(self.date, self.office_readings), "office/rubric_section.html"),
            (Pater(self.date, self.office_readings), "office/family_lords_prayer.html"),
            (FPCollect(self.date, self.office_readings), "office/family_collect.html"),
        ]


class FEEHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Family Prayer<br>in the Early Evening"), "calendar_date": self.date}


class FEERubricSection(OfficeSection):
    @cached_property
    def data(self):
        return {
            "rubric": mark_safe(
                "<br>These devotions follow the basic structure of the Daily Office of the Church and are particularly appropriate for families with young children.<br><br>The Reading and the Collect may be read by one person, and the other parts said in unison, or in some other convenient manner.<br><br>This devotion may be used before or after the evening meal."
            )
        }


class FEEOpeningSentence(OfficeSection):
    def get_sentences(self):

        return {
            "seasonal": EPOpeningSentence(self.date, self.office_readings).get_sentence(),
            "fixed": {
                "sentence": mark_safe(
                    "How excellent is your mercy, O God!<br>&nbsp;&nbsp;&nbsp;The children of men shall take refuge under the shadow of your wings.<br>For with you is the well of life,<br>&nbsp;&nbsp;&nbsp;and in your light shall we see light."
                ),
                "citation": "PSALM 36:7, 9",
            },
        }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentences": self.get_sentences()}


class FEEScripture(OfficeSection):
    def get_long(self):
        return {
            "passage": self.office_readings.ep_reading_1_abbreviated
            if self.office_readings.ep_reading_1_abbreviated
            else self.office_readings.ep_reading_1,
            "text": self.office_readings.ep_reading_1_abbreviated_text
            if self.office_readings.ep_reading_1_abbreviated_text
            else self.office_readings.ep_reading_1_text,
            "deuterocanon": self.office_readings.ep_reading_1_testament == "DC",
        }

    def get_scripture(self):

        day_of_year = self.date.date.timetuple().tm_yday
        number = day_of_year % 3

        scriptures = [
            {
                "sentence": "For what we proclaim is not ourselves, but Jesus Christ as Lord, with ourselves as your servants for Jesus’ sake. For God, who said, “Let light shine out of darkness,” has shone in our hearts, to give the light of the knowledge of the glory of God in the face of Jesus Christ.",
                "citation": "2 CORINTHIANS 4:5-6",
            },
            {
                "sentence": "Jesus spoke to them, saying, “I am the light of the world. Whoever follows me will not walk in darkness, but will have the light of life.”",
                "citation": "JOHN 8:12",
            },
            {
                "sentence": "Jesus said, “Behold, I stand at the door and knock. If anyone hears my voice and opens the door, I will come in to him and eat with him, and he with me.”",
                "citation": "REVELATION 3:20",
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


class FEEIntercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "title": "Intercessions",
            "rubric": mark_safe(
                "A hymn or canticle may be used.<br><br>Prayers may be offered for ourselves and others. It is appropriate that prayers of thanksgiving for the blessings of the day, and penitence for our sins, be included."
            ),
        }


class Pater(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Lord's Prayer"}


class FPCollect(OfficeSection):
    @cached_property
    def data(self):

        day_of_year = next(EPCollectsOfTheDay(self.date, self.office_readings).data["collects"])
        day_of_week = EPCollects(self.date, self.office_readings).data["collect"]

        return {
            "heading": "The Collect",
            "time_of_day": "Lord Jesus, stay with us, for evening is at hand and the day is past; be our companion in the way, kindle our hearts, and awaken hope, that we may know you as you are revealed in Scripture and the breaking of bread. Grant this for the sake of your love.",
            "day_of_year": day_of_year,
            "day_of_week": day_of_week,
        }

import re

from django.template.loader import render_to_string
from django.utils.functional import cached_property

from churchcal.calculations import get_calendar_date
from office.models import OfficeDay


class OfficeSection(object):
    def __init__(self, date, office_readings=None):
        self.date = date
        self.office_readings = office_readings

    @cached_property
    def data(self):
        raise NotImplementedError


class EPHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Daily Evening Prayer", "calendar_date": self.date}


class EPCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "This Evening's Commemorations", "commemorations": self.date.all}


class EPOpeningSetence(OfficeSection):
    def get_sentence(self):

        if self.date.season.name == "Advent":

            return {
                "sentence": "Therefore stay awake—for you do not know when the master of the house will come, in the evening, or at midnight, or when the rooster crows, or in the morning—lest he come suddenly and find you asleep.",
                "citation": "MARK 13:35-36",
            }

        if self.date.season.name == "Christmastide":
            return {
                "sentence": "Behold, the dwelling place of God is with man. He will dwell with them, and they will be his people, and God himself will be with them as their God.",
                "citation": "REVELATION 21:3",
            }

        if self.date.season.name == "Epiphanytide":
            return {
                "sentence": "Nations shall come to your light, and kings to the brightness of your rising.",
                "citation": "ISAIAH 60:3",
            }

        if self.date.season.name == "Lent":

            if self.date.date.weekday() == 6 or self.date.date.weekday() == 2:
                return {
                    "sentence": "To the Lord our God belong mercy and forgiveness, for we have rebelled against him.",
                    "citation": "DANIEL 9:9",
                }

            if self.date.date.weekday() == 0 or self.date.date.weekday() == 3:
                return {
                    "sentence": "For I acknowledge my faults, and my sin is ever before me.",
                    "citation": "PSALM 51:3",
                }

            return {
                "sentence": "If we say we have no sin, we deceive ourselves, and the truth is not in us. If we confess our sins, he is faithful and just to forgive us our sins and to cleanse us from all unrighteousness.",
                "citation": "1 JOHN 1:8-9",
            }

        if self.date.season.name == "Lent":

            return {
                "sentence": "All we like sheep have gone astray; we have turned every one to his own way; and the Lord has laid on him the iniquity of us all.",
                "citation": "ISAIAH 53:6",
            }

        if "Ascension" in self.date.primary.name:
            return {
                "sentence": "For Christ has entered, not into holy places made with hands, which are copies of the true things, but into heaven itself, now to appear in the presence of God on our behalf.",
                "citation": "HEBREWS 9:24",
            }

        if self.date.primary.name == "The Day of Pentecost":

            if self.date.date.year % 2 == 0:
                return {
                    "sentence": "The Spirit and the Bride say, “Come.” And let the one who hears say, “Come.” And let the one who is thirsty come; let the one who desires take the water of life without price.",
                    "citation": "REVELATION 22:17",
                }

            return {
                "sentence": "There is a river whose streams make glad the city of God, the holy dwelling place of the Most High.",
                "citation": "PSALM 46:4",
            }

        if self.date.primary.name == "Trinity Sunday":
            return {
                "sentence": "Holy, holy, holy is the Lord of Hosts; the whole earth is full of his glory!",
                "citation": "ISAIAH 6:3",
            }

        if self.date.season.name == "Eastertide":
            return {
                "sentence": "Thanks be to God, who gives us the victory through our Lord Jesus Christ.",
                "citation": "1 CORINTHIANS 15:57",
            }

        if self.date.date.weekday() == 0 or self.date.date.weekday() == 5:
            return {
                "sentence": "Jesus spoke to them, saying, “I am the light of the world. Whoever follows me will not walk in darkness, but will have the light of life.”",
                "citation": "JOHN 8:12",
            }

        if self.date.date.weekday() == 1 or self.date.date.weekday() == 6:
            return {
                "sentence": "Lord, I have loved the habitation of your house and the place where your honor dwells.",
                "citation": "PSALM 26:8",
            }

        if self.date.date.weekday() == 2:
            return {
                "sentence": "Let my prayer be set forth in your sight as incense, and let the lifting up of my hands be an evening sacrifice.",
                "citation": "PSALM 141:2",
            }

        if self.date.date.weekday() == 3:
            return {
                "sentence": "O worship the Lord in the beauty of holiness; let the whole earth stand in awe of him.",
                "citation": "PSALM 96:9",
            }

        if self.date.date.weekday() == 4:
            return {
                "sentence": "I will thank the Lord for giving me counsel; my heart also chastens me in the night season. I have set the Lord always before me; he is at my right hand, therefore I shall not fall.",
                "citation": "PSALM 16:8-9",
            }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentence": self.get_sentence()}


class EPConfession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin", "long_form": self.date.fast_day}


class EPPsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Psalms", "psalms": self.office_readings.ep_psalms_text}


class EPReading1(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The First Lesson",
            "book": re.sub("[^a-zA-Z ]+", "", self.office_readings.ep_reading_1),
            "passage": self.office_readings.ep_reading_1,
            "reading": self.office_readings.ep_reading_1_text,
        }


class EPReading2(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The Second Lesson",
            "book": re.sub("[^a-zA-Z]+", "", self.office_readings.ep_reading_2),
            "passage": self.office_readings.ep_reading_2,
            "reading": self.office_readings.ep_reading_2_text,
        }


class EPInvitatory(OfficeSection):
    @cached_property
    def data(self):
        return {}


class Hymn(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCanticle1(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCanticle2(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCreed(OfficeSection):
    @cached_property
    def data(self):
        return {}


# ==== Offices


class Office(object):

    name = "Daily Office"
    modules = []

    def __init__(self, date):
        self.date = get_calendar_date(date)
        self.office_readings = OfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

    def render(self):
        rendering = ""
        for module, template in self.modules:
            rendering += render_to_string(template, module(self.date).data)
        return rendering


class EveningPrayer(Office):

    name = "Evening Prayer"

    @cached_property
    def modules(self):
        return [
            (EPHeading(self.date), "office/evening_prayer/heading.html"),
            (EPCommemorationListing(self.date), "office/evening_prayer/commemoration_listing.html"),
            (EPOpeningSetence(self.date), "office/evening_prayer/opening_sentence.html"),
            (EPConfession(self.date), "office/evening_prayer/confession.html"),
            (EPInvitatory(self.date), "office/evening_prayer/invitatory.html"),
            (Hymn(self.date), "office/evening_prayer/hymn.html"),
            (EPPsalms(self.date, self.office_readings), "office/evening_prayer/psalms.html"),
            (EPReading1(self.date, self.office_readings), "office/evening_prayer/reading.html"),
            (EPCanticle1(self.date, self.office_readings), "office/evening_prayer/canticle_1.html"),
            (EPReading2(self.date, self.office_readings), "office/evening_prayer/reading.html"),
            (EPCanticle2(self.date, self.office_readings), "office/evening_prayer/canticle_2.html"),
            (EPCreed(self.date, self.office_readings), "office/evening_prayer/creed.html"),
        ]

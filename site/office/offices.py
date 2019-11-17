import datetime

from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from churchcal.calculations import get_calendar_date
from office.models import HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay
from psalter.utils import get_psalms

from office.utils import passage_to_citation


class OfficeSection(object):
    def __init__(self, date, office_readings=None, thirty_day_psalter_day=None, office=None):
        self.date = date
        self.office_readings = office_readings
        self.thirty_day_psalter_day = thirty_day_psalter_day
        self.office=office

    @cached_property
    def data(self):
        raise NotImplementedError


class EPHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Daily<br>Evening Prayer"), "calendar_date": self.date}

class ComplineHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Compline"), "calendar_date": self.date}

class MPHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Daily<br>Morning Prayer"), "calendar_date": self.date}


class MPCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": False,
            "heading": "This Morning's Commemoration{}".format("s" if len(self.date.all) > 1 else ""),
            "commemorations": self.date.all,
        }

class ComplineCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": True,
            "heading": "This Nights's Commemoration{}".format("s" if len(self.date.all) > 1 else ""),
            "commemorations": self.date.all_evening,
        }


class EPCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": True,
            "heading": "This Evening's Commemoration{}".format("s" if len(self.date.all_evening) > 1 else ""),
            "commemorations": self.date.all_evening,
        }


class EPOpeningSentence(OfficeSection):
    def get_sentence(self):

        if "Thanksgiving Day" in self.date.primary.name:
            return {
                "sentence": "The Lord by wisdom founded the earth; by understanding he established the heavens; by his knowledge the deeps broke open, and the clouds drop down the dew.",
                "citation": "PROVERBS 3:19-20",
            }

        if self.date.evening_season.name == "Holy Week":

            return {
                "sentence": "All we like sheep have gone astray; we have turned every one to his own way; and the Lord has laid on him the iniquity of us all.",
                "citation": "ISAIAH 53:6",
            }

        if (
            self.date.evening_season.name == "Lent"
            or self.date.primary.rank.name == "EMBER_DAY"
            or self.date.primary.rank.name == "ROGATION_DAY"
        ):

            if self.date.date.weekday() in [6, 2]:  # Sunday, Wednesday
                return {
                    "sentence": "To the Lord our God belong mercy and forgiveness, for we have rebelled against him.",
                    "citation": "DANIEL 9:9",
                }

            if self.date.date.weekday() in [0, 3, 5]:  # Monday, Thursday, Saturday
                return {
                    "sentence": "For I acknowledge my faults, and my sin is ever before me.",
                    "citation": "PSALM 51:3",
                }

            return {  # Tuesday, Friday
                "sentence": "If we say we have no sin, we deceive ourselves, and the truth is not in us. If we confess our sins, he is faithful and just to forgive us our sins and to cleanse us from all unrighteousness.",
                "citation": "1 JOHN 1:8-9",
            }

        if self.date.evening_season.name == "Advent":

            return {
                "sentence": "Therefore stay awake—for you do not know when the master of the house will come, in the evening, or at midnight, or when the rooster crows, or in the morning—lest he come suddenly and find you asleep.",
                "citation": "MARK 13:35-36",
            }

        if self.date.evening_season.name == "Christmastide":
            return {
                "sentence": "Behold, the dwelling place of God is with man. He will dwell with them, and they will be his people, and God himself will be with them as their God.",
                "citation": "REVELATION 21:3",
            }

        if self.date.evening_season.name == "Epiphanytide":
            return {
                "sentence": "Nations shall come to your light, and kings to the brightness of your rising.",
                "citation": "ISAIAH 60:3",
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

        if self.date.evening_season.name == "Eastertide":
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


class MPOpeningSentence(OfficeSection):
    def get_sentence(self):

        if "Thanksgiving Day" in self.date.primary.name:
            return {
                "sentence": "Honor the Lord with your wealth and with the firstfruits of all your produce; then your barns will be filled with plenty, and your vats will be bursting with wine.",
                "citation": "PROVERBS 3:9-10",
            }

        if self.date.season.name == "Holy Week":

            return {
                "sentence": "Is it nothing to you, all you who pass by? Look and see if there is any sorrow like my sorrow, which was brought upon me, which the Lord inflicted on the day of his fierce anger.",
                "citation": "LAMENTATIONS 1:12",
            }

        if (
            self.date.season.name == "Lent"
            or self.date.primary.rank.name == "EMBER_DAY"
            or self.date.primary.rank.name == "ROGATION_DAY"
        ):

            if self.date.date.weekday() in [6, 2]:  # Sunday, Wednesday
                return {"sentence": "Repent, for the kingdom of heaven is at hand.", "citation": "MATTHEW 3:2"}

            if self.date.date.weekday() in [0, 3, 5]:  # Monday, Thursday, Saturday
                return {
                    "sentence": "Turn your face from my sins, and blot out all my misdeeds.",
                    "citation": "PSALM 51:9",
                }

            return {
                "sentence": "If anyone would come after me, let him deny himself and take up his cross and follow me.",
                "citation": "MARK 8:34",
            }

        if self.date.season.name == "Advent":

            return {
                "sentence": "In the wilderness prepare the way of the Lord; make straight in the desert a highway for our God.",
                "citation": "ISAIAH 40:3",
            }

        if self.date.season.name == "Christmastide":
            return {
                "sentence": "Fear not, for behold, I bring you good news of great joy that will be for all the people. For unto you is born this day in the city of David a Savior, who is Christ the Lord.",
                "citation": "LUKE 2:10-11",
            }

        if self.date.season.name == "Epiphanytide":
            return {
                "sentence": "From the rising of the sun to its setting my name will be great among the nations, and in every place incense will be offered to my name, and a pure offering. For my name will be great among the nations, says the Lord of hosts.",
                "citation": "MALACHI 1:11",
            }

        if "Ascension" in self.date.primary.name:
            return {
                "sentence": "Since then we have a great high priest who has passed through the heavens, Jesus, the Son of God, let us hold fast our confession. Let us then with confidence draw near to the throne of grace, that we may receive mercy and find grace to help in time of need.",
                "citation": "HEBREWS 4:14, 16",
            }

        if self.date.primary.name == "The Day of Pentecost":

            return {
                "sentence": "You will receive power when the Holy Spirit has come upon you, and you will be my witnesses in Jerusalem and in all Judea and Samaria, and to the end of the earth.",
                "citation": "ACTS 1:8",
            }

        if self.date.primary.name == "Trinity Sunday":
            return {
                "sentence": "Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!",
                "citation": "REVELATION 4:8",
            }

        if self.date.season.name == "Eastertide":
            return {
                "sentence": "If then you have been raised with Christ, seek the things that are above, where Christ is, seated at the right hand of God.",
                "citation": "COLOSSIANS 3:1",
            }

        if self.date.date.weekday() == 6:
            return {
                "sentence": "Grace to you and peace from God our Father and the Lord Jesus Christ.",
                "citation": "PHILIPPIANS 1:2",
            }

        if self.date.date.weekday() == 0:
            return {
                "sentence": "I was glad when they said unto me, “We will go into the house of the Lord.”",
                "citation": "PSALM 122:1",
            }

        if self.date.date.weekday() == 1:
            return {
                "sentence": "Let the words of my mouth and the meditation of my heart be always acceptable in your sight, O Lord, my rock and my redeemer.",
                "citation": "PSALM 19:14",
            }

        if self.date.date.weekday() == 2:
            return {
                "sentence": "The Lord is in his holy temple; let all the earth keep silence before him.",
                "citation": "HABAKKUK 2:2",
            }

        if self.date.date.weekday() == 3:
            return {
                "sentence": "O send out your light and your truth, that they may lead me, and bring me to your holy hill, and to your dwelling.",
                "citation": "PSALM 43:3",
            }

        if self.date.date.weekday() == 4:
            return {
                "sentence": "Thus says the One who is high and lifted up, who inhabits eternity, whose name is Holy: “I dwell in the high and holy place, and also with him who is of a contrite and lowly spirit, to revive the spirit of the lowly, and to revive the heart of the contrite.”",
                "citation": "ISAIAH 57:15",
            }

        if self.date.date.weekday() == 5:
            return {
                "sentence": "The hour is coming, and is now here, when the true worshipers will worship the Father in spirit and truth, for the Father is seeking such people to worship him.",
                "citation": "JOHN 4:23",
            }

    @cached_property
    def data(self):
        return {"heading": "Opening Sentence", "sentence": self.get_sentence()}


class ComplineScripture(OfficeSection):
    def get_scripture(self):

        if self.date.date.weekday() in [0, 4]:
            return {
                "sentence": "You, O Lord, are in the midst of us, and we are called by your name; do not leave us.",
                "citation": "JEREMIAH 14:9",
            }

        if self.date.date.weekday() in [1, 5]:
            return {
                "sentence": "Come to me, all who labor and are heavy laden, and I will give you rest. Take my yoke upon you, and learn from me, for I am gentle and lowly in heart, and you will find rest for your souls. For my yoke is easy, and my burden is light.",
                "citation": "MATTHEW 11:28 30",
            }

        if self.date.date.weekday() in [2, 6]:
            return {
                "sentence": "Now may the God of peace who brought again from the dead our Lord Jesus, the great shepherd of the sheep, by the blood of the eternal covenant, equip you with everything good that you may do his will, working in us that which is pleasing in his sight, through Jesus Christ, to whom be glory forever and ever. Amen.",
                "citation": "HEBREWS 13:20-21",
            }

        if self.date.date.weekday() in [3]:
            return {
                "sentence": "Be sober-minded; be watchful. Your adversary the devil prowls around like a roaring lion, seeking someone to devour. Resist him, firm in your faith.",
                "citation": "1 PETER 5:8-9",
            }



    @cached_property
    def data(self):
        return {"heading": "The Reading", "sentence": self.get_scripture()}

class ComplinePrayers(OfficeSection):

    def get_collects(self):

        collects =[
            ("a collect for evening", "Visit this place, O Lord, and drive far from it all snares of the enemy; let your holy angels dwell with us to preserve us in peace; and let your blessing be upon us always; through Jesus Christ our Lord."),
            ("a collect for aid against perils", "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ."),
            ("a collect for evening", "Be present, O merciful God, and protect us through the hours of this night, so that we who are wearied by the changes and chances of this life may rest in your eternal changelessness; through Jesus Christ our Lord."),
            ("a collect for evening", "Look down, O Lord, from your heavenly throne, illumine this night with your celestial brightness, and from the children of light banish the deeds of darkness; through Jesus Christ our Lord."),
            ("a collect for saturdays", "We give you thanks, O God, for revealing your Son Jesus Christ to us by the light of his resurrection: Grant that as we sing your glory at the close of this day, our joy may abound in the morning as we celebrate the Paschal mystery; through Jesus Christ our Lord."),
            ("a collect for mission", "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give your angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for your love’s sake."),
            ("a collect for evening", "O God, your unfailing providence sustains the world we live in and the life we live: Watch over those, both night and day, who work while others sleep, and grant that we may never forget that our common life depends upon each other’s toil; through Jesus Christ our Lord.")
        ]



        if self.date.date.weekday() in [6]: #Sunday
            return collects[0], collects[1], collects[5]

        if self.date.date.weekday() in [0]: #Monday
            return collects[2], collects[3], collects[5]

        if self.date.date.weekday() in [1]: #Tuesday
            return collects[0], collects[2], collects[5]

        if self.date.date.weekday() in [2]: #Wednesday
            return collects[1], collects[3], collects[6]

        if self.date.date.weekday() in [3]: #Thursday
            return collects[0], collects[3], collects[5]

        if self.date.date.weekday() in [4]: #Friday
            return collects[1], collects[2], collects[6]

        if self.date.date.weekday() in [5]: #Saturday
            return collects[2], collects[4], collects[5]

    @cached_property
    def data(self):
        return {"heading": "The Prayers", "collects": self.get_collects()}

class  ComplineCanticle(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Nunc Dimittis", "subheading": "The Song of Simeon", "alleluia": self.date.evening_season.name=="Eastertide"}

class  ComplineConclusion(OfficeSection):
    @cached_property
    def data(self):
        return {}



class Confession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin", "long_form": self.date.fast_day}

class ComplineConfession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin"}

class EPPsalms(OfficeSection):
    @cached_property
    def data(self):
        psalms_60 = self.office_readings.ep_psalms.split("or")
        if len(psalms_60) > 1:
            if (self.date.date.year % 2) == 0:
                psalms_60 = psalms_60[0]
            else:
                psalms_60 = psalms_60[1]
        else:
            psalms_60 = psalms_60[0]

        citations_60 = psalms_60.split(",")

        psalms_30 = self.thirty_day_psalter_day.ep_psalms
        citations_30 = psalms_30.split(",")

        return {
            "heading_60": "The Psalm{} Appointed".format("s" if len(citations_60) > 1 else ""),
            "psalms_60": get_psalms(psalms_60),
            "heading_30": "The Psalm{} Appointed".format("s" if len(citations_30) > 1 else ""),
            "psalms_30": get_psalms(psalms_30),
        }


class MPPsalms(OfficeSection):
    @cached_property
    def data(self):
        psalms_60 = self.office_readings.mp_psalms.split("or")
        if len(psalms_60) > 1:
            if (self.date.date.year % 2) == 0:
                psalms_60 = psalms_60[0]
            else:
                psalms_60 = psalms_60[1]
        else:
            psalms_60 = psalms_60[0]

        citations_60 = psalms_60.split(",")

        psalms_30 = self.thirty_day_psalter_day.mp_psalms
        citations_30 = psalms_30.split(",")

        return {
            "heading_60": "The Psalm{} Appointed".format("s" if len(citations_60) > 1 else ""),
            "psalms_60": get_psalms(psalms_60),
            "heading_30": "The Psalm{} Appointed".format("s" if len(citations_30) > 1 else ""),
            "psalms_30": get_psalms(psalms_30),
        }


class ComplinePsalms(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The Psalms",
            "psalms": get_psalms("4,31:1-6,91,134"),
        }


class EPReading1(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The First Lesson",
            "intro": passage_to_citation(self.office_readings.ep_reading_1),
            "passage": self.office_readings.ep_reading_1.replace("Solomon", "Songs"),
            "reading": self.office_readings.ep_reading_1_text,
            "abbreviated_passage": self.office_readings.ep_reading_1_abbreviated
            if self.office_readings.ep_reading_1_abbreviated
            else self.office_readings.ep_reading_1,
            "abbreviated_reading": self.office_readings.ep_reading_1_abbreviated_text
            if self.office_readings.ep_reading_1_abbreviated_text
            else self.office_readings.ep_reading_1_text,
            "abbreviated_intro": passage_to_citation(
                self.office_readings.ep_reading_1_abbreviated
                if self.office_readings.ep_reading_1_abbreviated
                else self.office_readings.ep_reading_1
            ),
            "has_abbreviated": True if self.office_readings.ep_reading_1_abbreviated_text else False,
            "closing": {
                "reader": "The Word of the Lord."
                if self.office_readings.mp_reading_1_testament != "DC"
                else "Hear ends the Reading.",
                "people": "Thanks be to God." if self.office_readings.mp_reading_1_testament != "DC" else "",
            },
        }


class EPReading2(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The Second Lesson",
            "intro": passage_to_citation(self.office_readings.ep_reading_2),
            "passage": self.office_readings.ep_reading_2,
            "reading": self.office_readings.ep_reading_2_text,
            "abbreviated_intro": passage_to_citation(self.office_readings.ep_reading_2),
            "abbreviated_passage": self.office_readings.ep_reading_2,
            "abbreviated_reading": self.office_readings.ep_reading_2_text,
            "has_abbreviated": False,
            "closing": {"reader": "The Word of the Lord.", "people": "Thanks be to God."},
        }


class MPReading1(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The First Lesson",
            "intro": passage_to_citation(self.office_readings.mp_reading_1),
            "passage": self.office_readings.mp_reading_1,
            "reading": self.office_readings.mp_reading_1_text,
            "abbreviated_passage": self.office_readings.mp_reading_1_abbreviated
            if self.office_readings.mp_reading_1_abbreviated
            else self.office_readings.mp_reading_1,
            "abbreviated_reading": self.office_readings.mp_reading_1_abbreviated_text
            if self.office_readings.mp_reading_1_abbreviated_text
            else self.office_readings.mp_reading_1_text,
            "abbreviated_intro": passage_to_citation(
                self.office_readings.mp_reading_1_abbreviated
                if self.office_readings.mp_reading_1_abbreviated
                else self.office_readings.mp_reading_1
            ),
            "has_abbreviated": True if self.office_readings.mp_reading_1_abbreviated_text else False,
            "closing": {
                "reader": "The Word of the Lord."
                if self.office_readings.ep_reading_1_testament != "DC"
                else "Hear ends the Reading.",
                "people": "Thanks be to God." if self.office_readings.ep_reading_1_testament != "DC" else "",
            },
        }

class MPAlternateReading1(OfficeSection):
    @cached_property
    def data(self):
        if self.date.office_year == 1:
            module = MPReading1(self.date, self.office_readings)
            return module.data

        module = EPReading1(self.date, self.office_readings)
        return module.data

class MPAlternateReading2(OfficeSection):
    @cached_property
    def data(self):
        if self.date.office_year == 1:
            module = MPReading2(self.date, self.office_readings)
            return module.data

        module = EPReading2(self.date, self.office_readings)
        return module.data

class EPAlternateReading1(OfficeSection):
    @cached_property
    def data(self):
        if self.date.office_year == 2:
            module = EPReading1(self.date, self.office_readings)
            return module.data

        module = MPReading1(self.date, self.office_readings)
        return module.data

class EPAlternateReading2(OfficeSection):
    @cached_property
    def data(self):
        if self.date.office_year == 2:
            module = EPReading2(self.date, self.office_readings)
            return module.data

        module = MPReading2(self.date, self.office_readings)
        return module.data

class MPReading2(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "The Second Lesson",
            "intro": passage_to_citation(self.office_readings.mp_reading_2),
            "passage": self.office_readings.mp_reading_2,
            "reading": self.office_readings.mp_reading_2_text,
            "abbreviated_intro": passage_to_citation(self.office_readings.mp_reading_2),
            "abbreviated_passage": self.office_readings.mp_reading_2,
            "abbreviated_reading": self.office_readings.mp_reading_2_text,
            "has_abbreviated": False,
            "closing": {"reader": "The Word of the Lord.", "people": "Thanks be to God."},
        }


class Invitatory(OfficeSection):
    @cached_property
    def data(self):
        return {}

class ComplineOpening(OfficeSection):
    @cached_property
    def data(self):
        return {}

class ComplineInvitatory(OfficeSection):
    @cached_property
    def data(self):
        return {
            'alleluia': self.date.evening_season.name != "Lent" and self.date.evening_season.name != "Holy Week",
            'heading': "Invitatory",
        }


class Hymn(OfficeSection):
    @cached_property
    def data(self):
        return {}


class MPInvitatory(OfficeSection):
    @cached_property
    def antiphon(self):

        if "Presentation" in self.date.primary.name or "Annunciation" in self.date.primary.name:
            return {
                "first_line": "The Word was made flesh and dwelt among us:",
                "second_line": "O come, let us adore him.",
            }

        if self.date.primary.name == "The Day of Pentecost":
            return {
                "first_line": "Alleluia. The Spirit of the Lord renews the face of the earth:",
                "second_line": "O come, let us adore him.",
            }

        if self.date.primary.name == "Trinity Sunday":
            return {"first_line": "Father, Son, and Holy Spirit, one God:", "second_line": "O come, let us adore him."}

        if self.date.primary.name == "Easter Day":
            return {"first_line": "Alleluia. The Lord is risen indeed:", "second_line": "O come, let us adore him."}

        if self.date.primary.name == "Ascension Day":
            return {
                "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                "second_line": "O come, let us adore him.",
            }

        if self.date.primary.name == "The Transfiguration of Our Lord Jesus Christ":
            return {"first_line": "The Lord has shown forth his glory:", "second_line": "O come, let us adore him."}

        if self.date.primary.name == "All Saints’ Day":
            return {"first_line": "The Lord is glorious in his saints:", "second_line": "O come, let us adore him."}

        if self.date.primary.rank.name == "HOLY_DAY" and self.date.primary.name not in (
            "The Circumcision and Holy Name of our Lord Jesus Christ",
            "The Visitation of the Virgin Mary to Elizabeth and Zechariah",
            "Holy Cross Day",
            "The Holy Innocents",
        ):
            return {"first_line": "The Lord is glorious in his saints:", "second_line": "O come, let us adore him."}

        if self.date.season.name == "Lent":
            return {
                "first_line": "The Lord is full of compassion and mercy:",
                "second_line": "O come, let us adore him.",
            }

        if self.date.season.name == "Advent":
            return {"first_line": "Our King and Savior now draws near:", "second_line": "O come, let us adore him."}

        if self.date.season.name == "Christmastide":
            return {"first_line": "Alleluia, to us a child is born:", "second_line": "O come, let us adore him."}

        if self.date.season.name == "Epiphanytide":
            return {"first_line": "The Lord has shown forth his glory:", "second_line": "O come, let us adore him."}

        if self.date.season.name == "Eastertide":
            for commemoration in self.date.all:
                if "Ascension Day" in commemoration.name:
                    return {
                        "first_line": "Alleluia. Christ the Lord has ascended into heaven:",
                        "second_line": "O come, let us adore him.",
                    }

            return {"first_line": "Alleluia. The Lord is risen indeed:", "second_line": "O come, let us adore him."}

        if self.date.date.weekday() in [0, 3, 6]:
            return {
                "first_line": "The earth is the Lord’s for he made it: ",
                "second_line": "O come, let us adore him.",
            }

        if self.date.date.weekday() in [1, 4]:
            return {
                "first_line": "Worship the Lord in the beauty of holiness:",
                "second_line": "O come, let us adore him.",
            }

        if self.date.date.weekday() in [2, 5]:
            return {"first_line": "The mercy of the Lord is everlasting: ", "second_line": "O come, let us adore him."}

    @cached_property
    def data(self):

        pascha_nostrum = {
            "heading": "PASCHA NOSTRUM",
            "subheading": "Christ Our Passover",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/pascha_nostrum.html", {}),
            "citation": mark_safe("1 CORINTHIANS 5:7-8<br>ROMANS 6:9-11<br>1 CORINTHIANS 15:20-22"),
            "antiphon": None,
        }

        jubilate = {
            "heading": "Jubilate",
            "subheading": "Be Joyful",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/jubilate.html", {}),
            "citation": "PSALM 100",
            "antiphon": self.antiphon,
        }

        lent = self.date.season.name == "Lent" or self.date.season.name == "Holy Week"
        venite = {
            "heading": "Venite",
            "subheading": "O Come",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/venite.html", {"lent": lent}),
            "citation": "PSALM 95:1-7, 8-11" if not lent else "PSALM 95",
            "antiphon": self.antiphon,
        }

        if "Easter Day" in self.date.primary.name or "Easter Week" in self.date.primary.name:
            return pascha_nostrum

        if self.date.season.name == "Eastertide" and self.date.primary.rank.name in (
            "PRINCIPAL_FEAST",
            "SUNDAY",
            "HOLY_DAY",
        ):
            return pascha_nostrum

        if self.date.primary.rank.name in ("PRINCIPAL_FEAST", "SUNDAY", "HOLY_DAY"):
            if "100" in self.office_readings.mp_psalms.split(","):
                return venite
            return jubilate

        if "95" in self.office_readings.mp_psalms.split(","):
            return jubilate
        return venite


class MPCanticle1(OfficeSection):
    @cached_property
    def data(self):
        if self.date.season.name in ("Lent", "Holy Week"):
            return {
                "heading": "BENEDICTUS ES, DOMINE",
                "subheading": "A Song of Praise",
                "rubric": "Officiant and People, all standing",
                "content": render_to_string("office/morning_prayer/benedictus_es_domine.html", {}),
                "citation": "SONG OF THE THREE YOUNG MEN, 29-34",
            }

        return {
            "heading": "TE DEUM LAUDAMUS",
            "subheading": "We Praise You, O God",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/te_deum.html", {}),
            "citation": "",
        }


class MPCanticle2(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "BENEDICTUS",
            "subheading": "The Song of Zechariah",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/benedictus.html", {}),
            "citation": "LUKE 1:68-79",
        }


class EPCanticle1(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCanticle2(OfficeSection):
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
        return {}


class Suffrages(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCollectsOfTheDay(OfficeSection):
    @cached_property
    def data(self):
        return {
            "collects": (
                (commemoration.name,
                 commemoration.evening_prayer_collect.replace(" Amen.", ""),
                 commemoration.rank.name)
                for commemoration in self.date.all_evening
                if commemoration.evening_prayer_collect
            )
        }


class MPCollectsOfTheDay(OfficeSection):
    @cached_property
    def data(self):
        return {
            "collects": (
                (commemoration.name,
                commemoration.morning_prayer_collect.replace(" Amen.", ""),
                commemoration.rank.name)
                for commemoration in self.date.all
                if commemoration.morning_prayer_collect
                )
        }


class EPMissionCollect(OfficeSection):
    @cached_property
    def data(self):

        mission_collects = (
            "O God and Father of all, whom the whole heavens adore: Let the whole earth also worship you, all nations obey you, all tongues confess and bless you, and men, women, and children everywhere love you and serve you in peace; through Jesus Christ our Lord.",
            "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give your angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for your love’s sake.",
            "O God, you manifest in your servants the signs of your presence: Send forth upon us the Spirit of love, that in companionship with one another your abounding grace may increase among us; through Jesus Christ our Lord.",
        )

        if self.date.date.weekday() == 0 or self.date.date.weekday() == 3:
            collect = mission_collects[0]
            subheading = "I"
        elif self.date.date.weekday() == 1 or self.date.date.weekday() == 4 or self.date.date.weekday() == 6:
            collect = mission_collects[1]
            subheading = "II"
        elif self.date.date.weekday() == 2 or self.date.date.weekday() == 5:
            collect = mission_collects[1]
            subheading = "III"

        return {"heading": "A Collect for Mission", "collect": collect, "subheading": subheading}


class MPMissionCollect(OfficeSection):
    @cached_property
    def data(self):

        mission_collects = (
            "Almighty and everlasting God, who alone works great marvels: Send down upon our clergy and the congregations committed to their charge the life-giving Spirit of your grace, shower them with the continual dew of your blessing, and ignite in them a zealous love of your Gospel; through Jesus Christ our Lord. ",
            "O God, you have made of one blood all the peoples of the earth, and sent your blessed Son to preach peace to those who are far off and to those who are near: Grant that people everywhere may seek after you and find you; bring the nations into your fold; pour out your Spirit upon all flesh; and hasten the coming of your kingdom; through Jesus Christ our Lord.",
            "Lord Jesus Christ, you stretched out your arms of love on the hard wood of the Cross that everyone might come within the reach of your saving embrace: So clothe us in your Spirit that we, reaching forth our hands in love, may bring those who do not know you to the knowledge and love of you; for the honor of your Name.",
        )

        if self.date.date.weekday() == 0 or self.date.date.weekday() == 3:
            collect = mission_collects[0]
            subheading = "I"
        elif self.date.date.weekday() == 1 or self.date.date.weekday() == 4 or self.date.date.weekday() == 6:
            collect = mission_collects[1]
            subheading = "II"
        elif self.date.date.weekday() == 2 or self.date.date.weekday() == 5:
            collect = mission_collects[1]
            subheading = "III"

        return {"heading": "A Collect for Mission", "collect": collect, "subheading": subheading}


class EPCollects(OfficeSection):
    @cached_property
    def data(self):
        weekly_collects = (
            (
                "A COLLECT FOR PEACE",
                "Monday",
                "O God, the source of all holy desires, all good counsels, and all just works: Give to your servants that peace which the world cannot give, that our hearts may be set to obey your commandments, and that we, being defended from the fear of our enemies, may pass our time in rest and quietness; through the merits of Jesus Christ our Savior.",
            ),
            (
                "A COLLECT FOR AID AGAINST PERILS",
                "Tuesday",
                "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ.",
            ),
            (
                "A COLLECT FOR PROTECTION",
                "Wednesday",
                "O God, the life of all who live, the light of the faithful, the strength of those who labor, and the repose of the dead: We thank you for the blessings of the day that is past, and humbly ask for your protection through the coming night. Bring us in safety to the morning hours; through him who died and rose again for us, your Son our Savior Jesus Christ.",
            ),
            (
                "A COLLECT FOR THE PRESENCE OF CHRIST",
                "Thursday",
                "Lord Jesus, stay with us, for evening is at hand and the day is past; be our companion in the way, kindle our hearts, and awaken hope, that we may know you as you are revealed in Scripture and the breaking of bread. Grant this for the sake of your love.",
            ),
            (
                "A COLLECT FOR FAITH",
                "Friday",
                "Lord Jesus Christ, by your death you took away the sting of death: Grant to us your servants so to follow in faith where you have led the way, that we may at length fall asleep peacefully in you and wake up in your likeness; for your tender mercies’ sake.",
            ),
            (
                "A COLLECT FOR THE EVE OF WORSHIP",
                "Saturday",
                "O God, the source of eternal light: Shed forth your unending day upon us who watch for you, that our lips may praise you, our lives may bless you, and our worship on the morrow give you glory; through Jesus Christ our Lord.",
            ),
            (
                "A COLLECT FOR RESURRECTION HOPE",
                "Sunday",
                "Lord God, whose Son our Savior Jesus Christ triumphed over the powers of death and prepared for us our place in the new Jerusalem: Grant that we, who have this day given thanks for his resurrection, may praise you in that City of which he is the light, and where he lives and reigns for ever and ever.",
            ),
        )

        fixed_collects = (
            (
                "A COLLECT FOR PEACE",
                "O God, the source of all holy desires, all good counsels, and all just works: Give to your servants that peace which the world cannot give, that our hearts may be set to obey your commandments, and that we, being defended from the fear of our enemies, may pass our time in rest and quietness; through the merits of Jesus Christ our Savior.",
            ),
            (
                "A COLLECT FOR AID AGAINST PERILS",
                "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ.",
            ),
        )

        return {"collect": weekly_collects[self.date.date.weekday()], "fixed_collects": fixed_collects}


class MPCollects(OfficeSection):
    @cached_property
    def data(self):
        weekly_collects = (
            (
                "A COLLECT FOR THE RENEWAL OF LIFE",
                "Monday",
                "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ.",
            ),
            (
                "A COLLECT FOR PEACE",
                "Tuesday",
                "O God, the author of peace and lover of concord, to know you is eternal life and to serve you is perfect freedom: Defend us, your humble servants, in all assaults of our enemies; that we, surely trusting in your defense, may not fear the power of any adversaries, through the might of Jesus Christ our Lord. ",
            ),
            (
                "A COLLECT FOR GRACE",
                "Wednesday",
                "O Lord, our heavenly Father, almighty and everlasting God, you have brought us safely to the beginning of this day: Defend us by your mighty power, that we may not fall into sin nor run into any danger; and that, guided by your Spirit, we may do what is righteous in your sight; through Jesus Christ our Lord.",
            ),
            (
                "A COLLECT FOR GUIDANCE",
                "Thursday",
                "Heavenly Father, in you we live and move and have our being: We humbly pray you so to guide and govern us by your Holy Spirit, that in all the cares and occupations of our life we may not forget you, but may remember that we are ever walking in your sight; through Jesus Christ our Lord. ",
            ),
            (
                "A COLLECT FOR ENDURANCE ",
                "Friday",
                "Almighty God, whose most dear Son went not up to joy but first he suffered pain, and entered not into glory before he was crucified: Mercifully grant that we, walking in the way of the Cross, may find it none other than the way of life and peace; through Jesus Christ your Son our Lord.  ",
            ),
            (
                "A COLLECT FOR SABBATH REST",
                "Saturday",
                "Almighty God, who after the creation of the world rested from all your works and sanctified a day of rest for all your creatures: Grant that we, putting away all earthly anxieties, may be duly prepared for the service of your sanctuary, and that our rest here upon earth may be a preparation for the eternal rest promised to your people in heaven; through Jesus Christ our Lord. ",
            ),
            (
                "A COLLECT FOR STRENGTH TO AWAIT CHRIST’S RETURN",
                "Sunday",
                "O God our King, by the resurrection of your Son Jesus Christ on the first day of the week, you conquered sin, put death to flight, and gave us the hope of everlasting life: Redeem all our days by this victory; forgive our sins, banish our fears, make us bold to praise you and to do your will; and steel us to wait for the consummation of your kingdom on the last great Day; through Jesus Christ our Lord. ",
            ),
        )

        fixed_collects = (
            (
                "A COLLECT FOR PEACE",
                "O God, the author of peace and lover of concord, to know you is eternal life and to serve you is perfect freedom: Defend us, your humble servants, in all assaults of our enemies; that we, surely trusting in your defense, may not fear the power of any adversaries, through the might of Jesus Christ our Lord. ",
            ),
            (
                "A COLLECT FOR GRACE",
                "O Lord, our heavenly Father, almighty and everlasting God, you have brought us safely to the beginning of this day: Defend us by your mighty power, that we may not fall into sin nor run into any danger; and that, guided by your Spirit, we may do what is righteous in your sight; through Jesus Christ our Lord.",
            ),
        )

        return {"collect": weekly_collects[self.date.date.weekday()], "fixed_collects": fixed_collects}


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


        return {"heading": "Dismissal", "officiant": officiant, "people": people, "grace": self.get_grace()}



# ==== Offices


class Office(object):

    name = "Daily Office"
    modules = []

    def __init__(self, date):
        self.date = get_calendar_date(date)

        try:
            self.office_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except HolyDayOfficeDay.DoesNotExist:
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)

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
                "label": "Morning Prayer",
                "link": reverse("morning_prayer", args=[today.year, today.month, today.day]),
            },
            "evening_prayer": {
                "label": "Evening Prayer",
                "link": reverse("evening_prayer", args=[today.year, today.month, today.day]),
            },
            "compline": {
                "label": "Compline",
                "link": reverse("compline", args=[today.year, today.month, today.day]),
            },
            "current": self.office,
            "date": today.strftime("%A %B %-d, %Y")
        }

    @cached_property
    def settings(self):

        return [
            {
                "title": "Psalter Cycle",
                "name": "psalter",
                "options": [
                    {
                        "value": "60",
                        "hide": ["psalter-thirty"],
                        "show": ["psalter-sixty"],
                        "heading": "60 Day",
                        "text": "Pray through the psalms once every 60 days",
                    },
                    {
                        "value": "30",
                        "hide": ["psalter-sixty"],
                        "show": ["psalter-thirty"],
                        "heading": "30 Day",
                        "text": "Pray through the psalms once every 30 days",
                    },
                ],
            },
            {
                "title": "Reading Cycle",
                "name": "reading_cycle",
                "options": [
                    {
                        "value": "1",
                        "hide": ["alternate-reading"],
                        "show": ["main-reading"],
                        "heading": "One Year",
                        "text": mark_safe("Read through most of the bible each year. (Use if you pray <strong>both</strong> morning and evening prayer)"),
                    },
                    {
                        "value": "2",
                        "hide": ["main-reading"],
                        "show": ["alternate-reading"],
                        "heading": "Two Year",
                        "text": mark_safe("Read through most of the bible in two years. (Use if you pray <strong>only one</strong> of morning and evening prayer)"),
                    },
                ],
            },
            {
                "title": "Reading Length",
                "name": "reading_length",
                "options": [
                    {
                        "value": "full",
                        "hide": ["abbreviated-reading"],
                        "show": ["full-reading"],
                        "heading": "Full",
                        "text": "The full readings will always be used.",
                    },
                    {
                        "value": "abbreviated",
                        "hide": ["full-reading"],
                        "show": ["abbreviated-reading"],
                        "heading": "Abbreviated",
                        "text": "Suggested abbreviations, when available.",
                    },
                ],
            },
            {
                "title": "Language Style",
                "name": "language_style",
                "options": [
                    {
                        "value": "traditional",
                        "hide": ["contemporary"],
                        "show": ["traditional"],
                        "heading": "Traditional",
                        "text": "Traditional language for the Kyrie and Our Father",
                    },
                    {
                        "value": "contemporary",
                        "hide": ["traditional"],
                        "show": ["contemporary"],
                        "heading": "Contemporary",
                        "text": "Modern language for the Kyrie and Our Father",
                    },
                ],
            },
            {
                "title": "Collects",
                "name": "collects",
                "options": [
                    {
                        "value": "rotating",
                        "hide": ["fixed"],
                        "show": ["rotating"],
                        "heading": "Rotating",
                        "text": "A different collect is said for each day of the week",
                    },
                    {
                        "value": "fixed",
                        "hide": ["rotating"],
                        "show": ["fixed"],
                        "heading": "Fixed",
                        "text": "The two traditional collects are said every day",
                    },
                ],
            },
            {
                "title": "Absolution",
                "name": "absolution",
                "options": [
                    {
                        "value": "lay",
                        "hide": ["priest"],
                        "show": ["lay"],
                        "heading": "Lay Person",
                        "text": "A prayer suitable for a deacon or lay person to read",
                    },
                    {
                        "value": "priest",
                        "hide": ["lay"],
                        "show": ["priest"],
                        "heading": "Priest",
                        "text": "An absolution suitable for a priest to pronounce",
                    },
                ],
            },
            {
                "title": "General Thanksgiving",
                "name": "general_thanksgiving",
                "options": [
                    {
                        "value": "on",
                        "hide": [],
                        "show": ["general_thanksgiving"],
                        "heading": "On",
                        "text": "Add the prayer of general thanksgiving to the end of the office",
                    },
                    {
                        "value": "off",
                        "hide": ["general_thanksgiving"],
                        "show": [""],
                        "heading": "Off",
                        "text": "Hide the prayer of general thanksgiving to the end of the office",
                    },
                ],
            },
            {
                "title": "Prayer of St. John Chrysostom",
                "name": "chrysostom",
                "options": [
                    {
                        "value": "on",
                        "hide": [],
                        "show": ["chrysostom"],
                        "heading": "On",
                        "text": "For use when praying in groups of two or more",
                    },
                    {
                        "value": "off",
                        "hide": ["chrysostom"],
                        "show": [""],
                        "heading": "Off",
                        "text": "For when praying individually",
                    },
                ],
            },
            {
                "title": "National Holidays",
                "name": "national_holidays",
                "options": [
                    {
                        "value": "us",
                        "hide": ["canada"],
                        "show": ["us"],
                        "heading": "United States",
                        "text": "United States Holidays",
                    },
                    {
                        "value": "canada",
                        "hide": ["us"],
                        "show": ["canada"],
                        "heading": "Canada",
                        "text": "Canadian Holidays",
                    },
                    {
                        "value": "all",
                        "hide": [],
                        "show": ["canada", "us"],
                        "heading": "All",
                        "text": "Both U.S. and Canadian Holidays",
                    },
                ],
            },
        ]


class EveningPrayer(Office):

    name = "Evening Prayer"
    office = "evening_prayer"

    @cached_property
    def modules(self):
        return [
            (EPHeading(self.date), "office/heading.html"),
            (EPCommemorationListing(self.date), "office/commemoration_listing.html"),
            (EPOpeningSentence(self.date), "office/opening_sentence.html"),
            (Confession(self.date), "office/confession.html"),
            (Invitatory(self.date), "office/invitatory.html"),
            (Hymn(self.date), "office/evening_prayer/hymn.html"),
            (EPPsalms(self.date, self.office_readings, self.thirty_day_psalter_day), "office/psalms.html"),
            (EPReading1(self.date, self.office_readings), "office/main_reading.html"),
            (EPAlternateReading1(self.date, self.office_readings), "office/alternate_reading.html"),
            (EPCanticle1(self.date, self.office_readings), "office/evening_prayer/canticle_1.html"),
            (EPReading2(self.date, self.office_readings), "office/main_reading.html"),
            (EPAlternateReading2(self.date, self.office_readings), "office/alternate_reading.html"),
            (EPCanticle2(self.date, self.office_readings), "office/evening_prayer/canticle_2.html"),
            (Creed(self.date, self.office_readings), "office/creed.html"),
            (Prayers(self.date, self.office_readings), "office/prayers.html"),
            (Suffrages(self.date, self.office_readings), "office/suffrages.html"),
            (EPCollectsOfTheDay(self.date, self.office_readings), "office/collects_of_the_day.html"),
            (EPCollects(self.date, self.office_readings), "office/collects.html"),
            (EPMissionCollect(self.date, self.office_readings), "office/mission_collect.html"),
            (Intercessions(self.date, self.office_readings), "office/intercessions.html"),
            (GeneralThanksgiving(self.date, self.office_readings), "office/general_thanksgiving.html"),
            (Chrysostom(self.date, self.office_readings), "office/chrysostom.html"),
            (Dismissal(self.date, self.office_readings, office=self), "office/dismissal.html"),\
        ]


class MorningPrayer(Office):

    name = "Morning Prayer"
    office = "morning_prayer"

    @cached_property
    def modules(self):
        return [
            (MPHeading(self.date, self.office_readings), "office/heading.html"),
            (MPCommemorationListing(self.date, self.office_readings), "office/commemoration_listing.html"),
            (MPOpeningSentence(self.date, self.office_readings), "office/opening_sentence.html"),
            (Confession(self.date, self.office_readings), "office/confession.html"),
            (Invitatory(self.date, self.office_readings), "office/invitatory.html"),
            (MPInvitatory(self.date, self.office_readings), "office/morning_prayer/mpinvitatory.html"),
            (MPPsalms(self.date, self.office_readings, self.thirty_day_psalter_day), "office/psalms.html"),
            (MPReading1(self.date, self.office_readings), "office/main_reading.html"),
            (MPAlternateReading1(self.date, self.office_readings), "office/alternate_reading.html"),
            (MPCanticle1(self.date, self.office_readings), "office/canticle.html"),
            (MPReading2(self.date, self.office_readings), "office/main_reading.html"),
            (MPAlternateReading2(self.date, self.office_readings), "office/alternate_reading.html"),
            (MPCanticle2(self.date, self.office_readings), "office/canticle.html"),
            (Creed(self.date, self.office_readings), "office/creed.html"),
            (Prayers(self.date, self.office_readings), "office/prayers.html"),
            (Suffrages(self.date, self.office_readings), "office/suffrages.html"),
            (MPCollectsOfTheDay(self.date, self.office_readings), "office/collects_of_the_day.html"),
            (MPCollects(self.date, self.office_readings), "office/collects.html"),
            (MPMissionCollect(self.date, self.office_readings), "office/mission_collect.html"),
            (Intercessions(self.date, self.office_readings), "office/intercessions.html"),
            (GeneralThanksgiving(self.date, self.office_readings), "office/general_thanksgiving.html"),
            (Chrysostom(self.date, self.office_readings), "office/chrysostom.html"),
            (Dismissal(self.date, self.office_readings, office=self), "office/dismissal.html"),
        ]


class Compline(Office):
    name = "Compline"
    office = "compline"

    @cached_property
    def modules(self):
        return [
            (ComplineHeading(self.date, self.office_readings), "office/heading.html"),
            (ComplineCommemorationListing(self.date, self.office_readings), "office/commemoration_listing.html"),
            (ComplineOpening(self.date, self.office_readings), "office/compline_opening.html"),
            (ComplineConfession(self.date, self.office_readings), "office/compline_confession.html"),
            (ComplineInvitatory(self.date, self.office_readings), "office/compline_invitatory.html"),
            (ComplinePsalms(self.date, self.office_readings), "office/compline_psalms.html"),
            (ComplineScripture(self.date, self.office_readings), "office/compline_scripture.html"),
            (ComplinePrayers(self.date, self.office_readings), "office/compline_prayers.html"),
            (ComplineCanticle(self.date, self.office_readings), "office/compline_canticle.html"),
            (ComplineConclusion(self.date, self.office_readings), "office/compline_conclusion.html"),

        ]

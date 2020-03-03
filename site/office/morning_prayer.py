import datetime

from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.canticles import DefaultCanticles, BCP1979CanticleTable, REC2011CanticleTable

from office.offices import (
    Office,
    Confession,
    Invitatory,
    Creed,
    Prayers,
    Intercessions,
    GeneralThanksgiving,
    Chrysostom,
    Dismissal,
    OfficeSection,
    GreatLitany,
)
from office.utils import passage_to_citation
from psalter.utils import get_psalms


class MorningPrayer(Office):

    name = "Morning Prayer"
    office = "morning_prayer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Psalms (30 Day Cycle): {}, Psalms (60 Day Cycle): {}, First Reading: {}, Second Reading: {}, Prayer Book: {}".format(
            "Daily Morning Prayer",
            self.get_formatted_date_string(),
            self.date.primary.name,
            self.thirty_day_psalter_day.mp_psalms.replace(",", " "),
            self.office_readings.mp_psalms.replace(",", " "),
            self.office_readings.mp_reading_1,
            self.office_readings.mp_reading_2,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=5, second=0)
        self.end_time = self.start_time.replace(minute=0, hour=12, second=0)

    @cached_property
    def modules(self):
        return [
            (MPHeading(self.date, self.office_readings), "office/heading.html"),
            (MPCommemorationListing(self.date, self.office_readings), "office/commemoration_listing.html"),
            (MPOpeningSentence(self.date, self.office_readings), "office/opening_sentence.html"),
            (Confession(self.date, self.office_readings), "office/confession.html"),
            (Invitatory(self.date, self.office_readings), "office/invitatory.html"),
            (
                MPInvitatory(self.date, self.office_readings, self.thirty_day_psalter_day),
                "office/morning_prayer/mpinvitatory.html",
            ),
            (MPPsalms(self.date, self.office_readings, self.thirty_day_psalter_day), "office/psalms.html"),
            (MPReading1(self.date, self.office_readings), "office/main_reading.html"),
            (MPAlternateReading1(self.date, self.office_readings), "office/alternate_reading.html"),
            (MPCanticle1(self.date, self.office_readings), "office/canticle.html"),
            (MPReading2(self.date, self.office_readings), "office/main_reading.html"),
            (MPAlternateReading2(self.date, self.office_readings), "office/alternate_reading.html"),
            (MPCanticle2(self.date, self.office_readings), "office/canticle.html"),
            (Creed(self.date, self.office_readings), "office/creed.html"),
            (Prayers(self.date, self.office_readings), "office/prayers.html"),
            (MPSuffrages(self.date, self.office_readings), "office/morning_prayer/suffrages.html"),
            (MPCollectsOfTheDay(self.date, self.office_readings), "office/collects_of_the_day.html"),
            (MPCollects(self.date, self.office_readings), "office/collects.html"),
            (GreatLitany(self.date, self.office_readings, office=self), "office/great_litany.html"),
            (MPMissionCollect(self.date, self.office_readings), "office/mission_collect.html"),
            (Intercessions(self.date, self.office_readings), "office/intercessions.html"),
            (GeneralThanksgiving(self.date, self.office_readings), "office/general_thanksgiving.html"),
            (Chrysostom(self.date, self.office_readings), "office/chrysostom.html"),
            (Dismissal(self.date, self.office_readings, office=self), "office/dismissal.html"),
        ]


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

    def rotating(self):
        if "Easter Day" in self.date.primary.name or "Easter Week" in self.date.primary.name:
            return (self.pascha_nostrum, self.pascha_nostrum)

        if self.date.season.name == "Eastertide":
            if self.date.date.timetuple().tm_yday % 3 == 0:
                return (self.pascha_nostrum, self.pascha_nostrum)

        if self.date.date.timetuple().tm_yday % 2 == 0:
            thirty_day = self.jubilate
            sixty_day = self.jubilate
            if "100" in self.office_readings.mp_psalms.split(","):
                sixty_day = self.venite

            if "100" in self.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = self.venite
        else:
            thirty_day = self.venite
            sixty_day = self.venite
            if "95" in self.office_readings.mp_psalms.split(","):
                sixty_day = self.jubilate

            if "95" in self.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = self.jubilate

        return (thirty_day, sixty_day)

    def venite_most_days(self):
        if "Easter Day" in self.date.primary.name or "Easter Week" in self.date.primary.name:
            return (self.pascha_nostrum, self.pascha_nostrum)

        thirty_day = self.venite
        sixty_day = self.venite

        if "95" in self.office_readings.mp_psalms.split(","):
            sixty_day = self.jubilate

        if "95" in self.thirty_day_psalter_day.mp_psalms.split(","):
            thirty_day = self.jubilate

        return (thirty_day, sixty_day)

    def jubilate_on_sundays_and_feasts(self):
        if "Easter Day" in self.date.primary.name or "Easter Week" in self.date.primary.name:
            return (self.pascha_nostrum, self.pascha_nostrum)

        if self.date.season.name == "Eastertide" and self.date.primary.rank.name in (
            "PRINCIPAL_FEAST",
            "SUNDAY",
            "HOLY_DAY",
        ):
            return (self.pascha_nostrum, self.pascha_nostrum)

        if self.date.primary.rank.name in ("PRINCIPAL_FEAST", "SUNDAY", "HOLY_DAY"):
            thirty_day = self.jubilate
            sixty_day = self.jubilate

            if "100" in self.office_readings.mp_psalms.split(","):
                sixty_day = self.venite
            if "100" in self.thirty_day_psalter_day.mp_psalms.split(","):
                thirty_day = self.venite
            return (thirty_day, sixty_day)

        thirty_day = self.venite
        sixty_day = self.venite

        if "95" in self.office_readings.mp_psalms.split(","):
            sixty_day = self.jubilate

        if "95" in self.thirty_day_psalter_day.mp_psalms.split(","):
            thirty_day = self.jubilate

        return (thirty_day, sixty_day)

    @cached_property
    def pascha_nostrum(self):
        return {
            "heading": "PASCHA NOSTRUM",
            "subheading": "Christ Our Passover",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/pascha_nostrum.html", {}),
            "citation": mark_safe("1 CORINTHIANS 5:7-8<br>ROMANS 6:9-11<br>1 CORINTHIANS 15:20-22"),
            "antiphon": None,
        }

    @cached_property
    def jubilate(self):
        return {
            "heading": "Jubilate",
            "subheading": "Be Joyful",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/jubilate.html", {}),
            "citation": "PSALM 100",
            "antiphon": self.antiphon,
        }

    @cached_property
    def venite(self):
        lent = self.date.season.name == "Lent" or self.date.season.name == "Holy Week"
        return {
            "heading": "Venite",
            "subheading": "O Come",
            "rubric": "Officiant and People, all standing",
            "content": render_to_string("office/morning_prayer/venite.html", {"lent": lent}),
            "citation": "PSALM 95:1-7, 8-11" if not lent else "PSALM 95",
            "antiphon": self.antiphon,
        }

    @cached_property
    def data(self):

        values = {
            "jubilate_on_sundays_and_feasts": self.jubilate_on_sundays_and_feasts(),
            "venite_most_days": self.venite_most_days(),
            "rotating": self.rotating(),
        }
        return values


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


# 1 / 24
# 1 / 6
# 3 / 26
# 5 / 25


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
                if self.office_readings.mp_reading_1_testament != "DC"
                else "Here ends the Reading.",
                "people": "Thanks be to God." if self.office_readings.mp_reading_1_testament != "DC" else "",
            },
            "deuterocanon": self.office_readings.mp_reading_1_testament not in ["OT", "NT"],
        }


class MPAlternateReading1(OfficeSection):
    @cached_property
    def data(self):
        from office.evening_prayer import EPReading1

        if self.date.date.year % 2 == 0:
            module = EPReading1(self.date, self.office_readings)
            return module.data

        module = MPReading1(self.date, self.office_readings)
        return module.data


class MPCanticle1(OfficeSection):
    @cached_property
    def data(self):

        return {
            "default": DefaultCanticles().get_mp_canticle_1(self.date),
            "1979": BCP1979CanticleTable().get_mp_canticle_1(self.date),
            "2011": REC2011CanticleTable().get_mp_canticle_1(self.date),
        }


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


class MPAlternateReading2(OfficeSection):
    @cached_property
    def data(self):
        from office.evening_prayer import EPReading2

        if self.date.date.year % 2 == 0:
            module = EPReading2(self.date, self.office_readings)
            return module.data

        module = MPReading2(self.date, self.office_readings)
        return module.data


class MPCanticle2(OfficeSection):
    @cached_property
    def data(self):

        return {
            "default": DefaultCanticles().get_mp_canticle_2(self.date),
            "1979": BCP1979CanticleTable().get_mp_canticle_2(self.date),
            "2011": REC2011CanticleTable().get_mp_canticle_2(self.date),
        }


class MPSuffrages(OfficeSection):
    @cached_property
    def data(self):
        return {}


class MPCollectsOfTheDay(OfficeSection):
    @cached_property
    def data(self):
        return {
            "collects": (
                (
                    commemoration.name,
                    commemoration.morning_prayer_collect.replace(" Amen.", ""),
                    commemoration.rank.name,
                )
                for commemoration in self.date.all
                if commemoration.morning_prayer_collect
            )
        }


class MPCollects(OfficeSection):
    @cached_property
    def data(self):
        weekly_collects = (
            (
                "A COLLECT FOR THE RENEWAL OF LIFE",
                "Monday",
                "O God, the King eternal, whose light divides the day from the night and turns the shadow of death into the morning: Drive far from us all wrong desires, incline our hearts to keep your law, and guide our feet into the way of peace; that, having done your will with cheerfulness during the day, we may, when night comes, rejoice to give you thanks; through Jesus Christ our Lord.",
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


class MPMissionCollect(OfficeSection):
    def get_weekday_class(self):
        start = "mission-mp-"
        if self.date.date.weekday() in (2, 4, 6):
            return start + "wfs"
        return start + "not-wfs"

    @cached_property
    def data(self):

        mission_collects = (
            "Almighty and everlasting God, who alone works great marvels: Send down upon our clergy and the congregations committed to their charge the life-giving Spirit of your grace, shower them with the continual dew of your blessing, and ignite in them a zealous love of your Gospel; through Jesus Christ our Lord. ",
            "O God, you have made of one blood all the peoples of the earth, and sent your blessed Son to preach peace to those who are far off and to those who are near: Grant that people everywhere may seek after you and find you; bring the nations into your fold; pour out your Spirit upon all flesh; and hasten the coming of your kingdom; through Jesus Christ our Lord.",
            "Lord Jesus Christ, you stretched out your arms of love on the hard wood of the Cross that everyone might come within the reach of your saving embrace: So clothe us in your Spirit that we, reaching forth our hands in love, may bring those who do not know you to the knowledge and love of you; for the honor of your Name.",
        )

        day_of_year = self.date.date.timetuple().tm_yday
        collect_number = day_of_year % 3

        if collect_number == 0:
            collect = mission_collects[0]
            subheading = "I"
        elif collect_number == 1:
            collect = mission_collects[1]
            subheading = "II"
        else:
            collect = mission_collects[2]
            subheading = "III"

        return {
            "heading": "A Collect for Mission",
            "collect": collect,
            "subheading": subheading,
            "weekday_class": self.get_weekday_class(),
        }

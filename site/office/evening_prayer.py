import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.canticles import DefaultCanticles, BCP1979CanticleTable, REC2011CanticleTable

# from office.morning_prayer import MPReading1, MPReading2
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
    PandemicPrayers,
    Reading,
    ThirdReading,
)
from office.utils import passage_to_citation
from psalter.utils import get_psalms


class EveningPrayer(Office):

    name = "Evening Prayer"
    office = "evening_prayer"

    start_time = "4:00 PM"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Psalms (30 Day Cycle): {}, Psalms (60 Day Cycle): {}, First Reading: {}, Second Reading: {}, Prayer Book: {}".format(
            "Daily Evening Prayer",
            self.get_formatted_date_string(),
            self.date.primary_evening.name,
            self.thirty_day_psalter_day.ep_psalms.replace(",", " "),
            self.office_readings.ep_psalms.replace(",", " "),
            self.office_readings.ep_reading_1,
            self.office_readings.ep_reading_2,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=16, second=0)
        self.end_time = self.start_time.replace(minute=59, hour=23, second=59)

    @cached_property
    def modules(self):
        return [
            (EPHeading(self.date), "office/heading.html"),
            (EPCommemorationListing(self.date), "office/commemoration_listing.html"),
            (EPOpeningSentence(self.date), "office/opening_sentence.html"),
            (Confession(self.date), "office/confession.html"),
            (Invitatory(self.date), "office/invitatory.html"),
            (EPInvitatory(self.date), "office/evening_prayer/hymn.html"),
            (EPPsalms(self.date, self.office_readings, self.thirty_day_psalter_day), "office/psalms.html"),
            (EPFirstReading(self.date, self.office_readings), "office/reading_section.html"),
            (EPCanticle1(self.date, self.office_readings), "office/canticle.html"),
            (EPSecondReading(self.date, self.office_readings), "office/reading_section.html"),
            (EPCanticle2(self.date, self.office_readings), "office/canticle.html"),
            (ThirdReading(self.date, self.office_readings), "office/reading_section.html"),
            (Creed(self.date, self.office_readings), "office/creed.html"),
            (Prayers(self.date, self.office_readings), "office/prayers.html"),
            (EPSuffrages(self.date, self.office_readings), "office/evening_prayer/suffrages.html"),
            (EPCollectsOfTheDay(self.date, self.office_readings), "office/collects_of_the_day.html"),
            (EPCollects(self.date, self.office_readings), "office/collects.html"),
            (GreatLitany(self.date, self.office_readings, office=self), "office/great_litany.html"),
            (EPMissionCollect(self.date, self.office_readings), "office/mission_collect.html"),
            (PandemicPrayers(self.date, self.office_readings, office=self), "office/pandemic_prayers.html"),
            (Intercessions(self.date, self.office_readings), "office/intercessions.html"),
            (GeneralThanksgiving(self.date, self.office_readings), "office/general_thanksgiving.html"),
            (Chrysostom(self.date, self.office_readings), "office/chrysostom.html"),
            (Dismissal(self.date, self.office_readings, office=self), "office/dismissal.html"),
        ]


class EPHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Daily<br>Evening Prayer"), "calendar_date": self.date}


class EPCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": True,
            "heading": "This Evening's Commemoration{}".format("s" if len(self.date.all_evening) > 1 else ""),
            "commemorations": self.date.all_evening,
        }


class EPInvitatory(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPOpeningSentence(OfficeSection):
    def get_sentence(self):

        if "Thanksgiving Day" in self.date.primary_evening.name:
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
            or self.date.primary_evening.rank.name == "EMBER_DAY"
            or self.date.primary_evening.rank.name == "ROGATION_DAY"
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

        if (
            self.date.primary_evening.name == "The Day of Pentecost"
            or self.date.primary_evening.name == "Eve of The Day of Pentecost"
        ):

            if self.date.date.year % 2 == 0:
                return {
                    "sentence": "The Spirit and the Bride say, “Come.” And let the one who hears say, “Come.” And let the one who is thirsty come; let the one who desires take the water of life without price.",
                    "citation": "REVELATION 22:17",
                }

            return {
                "sentence": "There is a river whose streams make glad the city of God, the holy dwelling place of the Most High.",
                "citation": "PSALM 46:4",
            }

        if (
            "Ascension" in self.date.primary_evening.name
            or len(self.date.all_evening) > 1
            and "Ascension" in self.date.all_evening[1].name
        ):
            return {
                "sentence": "For Christ has entered, not into holy places made with hands, which are copies of the true things, but into heaven itself, now to appear in the presence of God on our behalf.",
                "citation": "HEBREWS 9:24",
            }

        if (
            self.date.primary_evening.name == "Trinity Sunday"
            or self.date.primary_evening.name == "Eve of Trinity Sunday"
        ):
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

        mass_psalm = ""
        mass_heading = ""
        for reading in self.date.evening_mass_readings:
            if reading.reading_type == "psalm":
                if self.date.primary_evening.name == "Eve of Easter Day" and reading.reading_number != 4:
                    continue
                mass_psalm = reading.long_text
                mass_heading = "The Psalm Appointed"
                break

        return {
            "heading_60": "The Psalm{} Appointed".format("s" if len(citations_60) > 1 else ""),
            "psalms_60": get_psalms(psalms_60),
            "heading_30": "The Psalm{} Appointed".format("s" if len(citations_30) > 1 else ""),
            "psalms_30": get_psalms(psalms_30),
            "psalms_mass": mass_psalm,
            "heading_mass": mass_heading,
            "daily_office_tag": "daily-office-readings-{}".format(
                "sunday" if self.date.primary_evening.rank.precedence_rank <= 4 else "feria"
            ),
            "mass_tag": "mass-readings-{}".format(
                "sunday" if self.date.primary_evening.rank.precedence_rank <= 4 else "feria"
            ),
        }


class EPFirstReading(Reading):

    heading = "The First Lesson"
    tag = "first-"

    @cached_property
    def has_main_reading(self):
        return True

    @cached_property
    def has_abbreviated_reading(self):
        return True if self.office_readings.ep_reading_1_abbreviated else False

    @cached_property
    def has_alternate_reading(self):
        return self.date.date.year % 2 != 0

    @cached_property
    def has_alternate_abbreviated_reading(self):
        if not self.has_alternate_reading:
            return False
        return True if self.office_readings.mp_reading_1_abbreviated else False

    @cached_property
    def has_mass_reading(self):
        return self.date.primary.rank.precedence_rank <= 4

    @cached_property
    def has_abbreviated_mass_reading(self):
        if not self.has_mass_reading:
            return False
        for reading in self.date.mass_readings:
            if reading.reading_number == 1 and reading.short_citation:
                return True
        return False

    def get_main_reading(self):
        return {
            "intro": passage_to_citation(self.office_readings.ep_reading_1),
            "passage": self.office_readings.ep_reading_1,
            "reading": self.office_readings.ep_reading_1_text,
            "closing": self.closing(self.office_readings.ep_reading_1_testament),
            "tag": "main-reading",
        }

    def get_abbreviated_reading(self):
        if not self.has_abbreviated_reading:
            return None
        return {
            "intro": passage_to_citation(self.office_readings.ep_reading_1_abbreviated),
            "passage": self.office_readings.ep_reading_1_abbreviated,
            "reading": self.office_readings.ep_reading_1_abbreviated_text,
            "closing": self.closing(self.office_readings.ep_reading_1_testament),
            "tag": "abbreviated-reading",
        }

    def get_alternate_reading(self):
        if not self.has_alternate_reading:
            return None
        return {
            "intro": passage_to_citation(self.office_readings.mp_reading_1),
            "passage": self.office_readings.mp_reading_1,
            "reading": self.office_readings.mp_reading_1_text,
            "closing": self.closing(self.office_readings.mp_reading_1_testament),
            "tag": "alternate-reading",
        }

    def get_alternate_abbreviated_reading(self):
        if not self.has_alternate_abbreviated_reading:
            return None
        return {
            "intro": passage_to_citation(self.office_readings.mp_reading_1_abbreviated),
            "passage": self.office_readings.mp_reading_1_abbreviated,
            "reading": self.office_readings.mp_reading_1_abbreviated_text,
            "closing": self.closing(self.office_readings.mp_reading_1_testament),
            "tag": "alternate-abbreviated-reading",
        }

    def get_mass_reading(self):
        if not self.has_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 1:
                return {
                    "intro": passage_to_citation(reading.long_citation),
                    "passage": reading.long_citation,
                    "reading": reading.long_text,
                    "closing": self.closing(reading.testament),
                    "tag": "mass-reading",
                }

        return None

    def get_abbreviated_mass_reading(self):
        if not self.has_abbreviated_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 1 and reading.short_citation:
                return {
                    "intro": passage_to_citation(reading.short_citation),
                    "passage": reading.short_citation,
                    "reading": reading.short_text,
                    "closing": self.closing(reading.testament),
                    "tag": "abbreviated-mass-reading",
                }

        return None


class EPSecondReading(Reading):

    heading = "The Second Lesson"
    tag = "second-"

    @cached_property
    def has_main_reading(self):
        return True

    @cached_property
    def has_abbreviated_reading(self):
        return False

    @cached_property
    def has_alternate_reading(self):
        return self.date.date.year % 2 != 0

    @cached_property
    def has_alternate_abbreviated_reading(self):
        return False

    @cached_property
    def has_mass_reading(self):
        return self.date.primary.rank.precedence_rank <= 4

    @cached_property
    def has_abbreviated_mass_reading(self):
        if not self.has_mass_reading:
            return False
        for reading in self.date.mass_readings:
            if reading.reading_number == 3 and reading.short_citation:
                return True
        return False

    def get_main_reading(self):
        return {
            "intro": passage_to_citation(self.office_readings.ep_reading_2),
            "passage": self.office_readings.ep_reading_2,
            "reading": self.office_readings.ep_reading_2_text,
            "closing": self.closing(self.office_readings.ep_reading_2_testament),
            "tag": "main-reading",
        }

    def get_abbreviated_reading(self):
        return None

    def get_alternate_reading(self):
        if not self.has_alternate_reading:
            return None
        return {
            "intro": passage_to_citation(self.office_readings.mp_reading_2),
            "passage": self.office_readings.mp_reading_2,
            "reading": self.office_readings.mp_reading_2_text,
            "closing": self.closing(self.office_readings.mp_reading_2_testament),
            "tag": "alternate-reading",
        }

    def get_alternate_abbreviated_reading(self):
        return None

    def get_mass_reading(self):
        if not self.has_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 3:
                return {
                    "intro": passage_to_citation(reading.long_citation),
                    "passage": reading.long_citation,
                    "reading": reading.long_text,
                    "closing": self.closing(reading.testament),
                    "tag": "mass-reading",
                }

        return None

    def get_abbreviated_mass_reading(self):
        if not self.has_abbreviated_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 3 and reading.short_citation:
                return {
                    "intro": passage_to_citation(reading.short_citation),
                    "passage": reading.short_citation,
                    "reading": reading.short_text,
                    "closing": self.closing(reading.testament),
                    "tag": "abbreviated-mass-reading",
                }

        return None


class EPCanticle1(OfficeSection):
    def get_antiphon(self):
        if self.date.date.month != 12:
            return None
        antiphons = {
            "16": {
                "latin": "O Sapientia, quae ex ore Altissimi prodiisti, attingens a fine usque ad finem, fortiter suaviterque disponens omnia: veni ad docendum nos viam prudentiae.",
                "english": "O Wisdom, who came from the mouth of the Most High, reaching from end to end and ordering all things mightily and sweetly: come, and teach us the way of prudence.",
                "hymn": "O come, thou Wisdom from on high who orderest all things mightily; to us the path of knowledge show, and teach us in her ways to go. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:2-3, 28:29",
            },
            "17": {
                "latin": "O Adonai, et Dux domus Israel, qui Moysi in igne flammae rubi apparuisti, et ei in Sina legem dedisti: veni ad redimendum nos in brachio extento.",
                "english": "O Lord and Ruler the house of Israel, who appeared to Moses in the flame of the burning bush and gave him the law on Sinai: come, and redeem us with outstretched arms.",
                "hymn": "O come, O come, thou Lord of might, who to thy tribes on Sinai's height in ancient times didst give the law, in cloud, and majesty, and awe. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:4-5, 33:22",
            },
            "18": {
                "latin": "O Radix Jesse, qui stas in signum populorum, super quem continebunt reges os suum, quem Gentes deprecabuntur: veni ad liberandum nos, jam noli tardare.",
                "english": "O Root of Jesse, that stands for an ensign of the people, before whom the kings keep silence and unto whom the Gentiles shall make supplication: come, to deliver us, and tarry not.",
                "hymn": "O come, through Branch of Jesse's tree, free them from Satan's tyranny that trust thy mighty power to save, and give them victory oer' the grave. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 11:1, 10",
            },
            "19": {
                "latin": "O clavis David, et sceptrum domus Israel: qui aperis, et nemo claudit; claudis, et nemo aperit: veni, et educ vinctum de domo carceris, sedentem in tenebris.",
                "english": "O Key of David, and scepter of the house of Israel, who opens and no man shuts, who shuts and no man opens: come, and lead forth the captive who sits in the shadows from his prison.",
                "hymn": "O come, though Key of David, come, and open wide our heavenly home; make safe the way that leads on high, and close the path to misery. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 9:6, 22:22.",
            },
            "20": {
                "latin": "O Oriens, splendor lucis æternæ, et sol justitiæ: veni, et illumina sedentes in tenebris, et umbra mortis.",
                "english": "O dawn of the east, brightness of light eternal, and sun of justice: come, and enlighten those who sit in darkness and in the shadow of death.",
                "hymn": "O come, thou Dayspring from on high, and cheer us by thy drawing night; disperse the gloomy clouds of night, and death's dark shadow put to flight. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 9:2",
            },
            "21": {
                "latin": "O Rex Gentium, et desideratus earum, lapisque angularis, qui facis utraque unum: veni, et salva hominem, quem de limo formasti.",
                "english": "O King of the gentiles and their desired One, the cornerstone that makes both one: come, and deliver man, whom you formed out of the dust of the earth.",
                "hymn": "O come, Desire of nations, bind in one the hearts of all mankind; bid thou our sad divisions cease, and be thyself our King of Peace. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 2:4, 9:7",
            },
            "22": {
                "latin": "O Emmanuel, Rex et legifer noster, exspectatio gentium, et Salvator earum: veni ad salvandum nos Domine Deus noster.",
                "english": "O Emmanuel, God with us, our King and lawgiver, the expected of the nations and their Savior: come to save us, O Lord our God.",
                "hymn": "O come, O come, Emmanuel, and ransom captive Israel, that mourns in lonley exile here until the Sod of God appear. Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "Isaiah 7:14",
            },
            "23": {
                "latin": "O Virgo virginum, quomodo fiet istud? Quia nec primam similem visa es nec habere sequentem. Filiae Jerusalem, quid me admiramini? Divinum est mysterium hoc quod cernitis.",
                "english": "O Virgin of virgins, how shall this be? For neither before you was any like you, nor shall there be after. Daughters of Jerusalem, why do you marvel at me? The thing which you behold is a divine mystery.",
                "hymn": "O Virgin great! How shall this be? For none before nor hence were like to thee; Why, Salem’s daughters, marvel ye? Behold, a heav’nly mystery! Rejoice! Rejoice! Emmanuel shall come to thee, O Israel.",
                "citation": "",
            },
        }
        index = str(self.date.date.day)
        try:
            return antiphons[index]
        except KeyError:
            return None

    @cached_property
    def data(self):

        return {
            "antiphon": self.get_antiphon(),
            "default": DefaultCanticles().get_ep_canticle_1(self.date),
            "1979": BCP1979CanticleTable().get_ep_canticle_1(self.date),
            "2011": REC2011CanticleTable().get_ep_canticle_1(self.date),
        }


class EPCanticle2(OfficeSection):
    @cached_property
    def data(self):

        return {
            "default": DefaultCanticles().get_ep_canticle_2(self.date),
            "1979": BCP1979CanticleTable().get_ep_canticle_2(self.date),
            "2011": REC2011CanticleTable().get_ep_canticle_2(self.date, self.office_readings),
        }


class EPSuffrages(OfficeSection):
    def get_names(self):
        names = [
            feast.saint_name for feast in self.date.all_evening if hasattr(feast, "saint_name") and feast.saint_name
        ]
        names = ["the Blessed Virgin Mary"] + names
        return ", ".join(names)

    def get_default_set(self):

        if self.date.date.timetuple().tm_yday % 2:
            return "b"

        return "a"

    @cached_property
    def data(self):
        self.date
        return {"default_set": self.get_default_set(), "names": self.get_names()}


class EPCollectsOfTheDay(OfficeSection):
    @cached_property
    def data(self):
        return {
            "collects": (
                (
                    commemoration.name,
                    commemoration.evening_prayer_collect.replace(" Amen.", ""),
                    commemoration.rank.name,
                )
                for commemoration in self.date.all_evening
                if commemoration.evening_prayer_collect
            )
        }


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


class EPMissionCollect(OfficeSection):
    def get_weekday_class(self):
        start = "mission-ep-"
        if self.date.date.weekday() in (2, 4, 6):
            return start + "wfs"
        return start + "not-wfs"

    @cached_property
    def data(self):

        mission_collects = (
            "O God and Father of all, whom the whole heavens adore: Let the whole earth also worship you, all nations obey you, all tongues confess and bless you, and men, women, and children everywhere love you and serve you in peace; through Jesus Christ our Lord.",
            "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give your angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for your love’s sake.",
            "O God, you manifest in your servants the signs of your presence: Send forth upon us the Spirit of love, that in companionship with one another your abounding grace may increase among us; through Jesus Christ our Lord.",
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

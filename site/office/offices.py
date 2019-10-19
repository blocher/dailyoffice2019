import re

from django.template.loader import render_to_string
from django.utils.functional import cached_property

from churchcal.calculations import get_calendar_date
from office.models import OfficeDay, HolyDayOfficeDay, StandardOfficeDay
from psalter.utils import get_psalms


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
        return {
            "heading": "This Evening's Commemoration{}".format("s" if len(self.date.all_evening) > 1 else ""),
            "commemorations": self.date.all_evening,
        }


class EPOpeningSentence(OfficeSection):
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
        citations = self.office_readings.ep_psalms.split(",")
        return {
            "heading": "The Psalm{} Appointed".format("s" if len(citations) > 1 else ""),
            "psalms": get_psalms(self.office_readings.ep_psalms),
        }


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


class EPPrayers(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPSuffrages(OfficeSection):
    @cached_property
    def data(self):
        return {}


class EPCollectsOfTheDay(OfficeSection):
    @cached_property
    def data(self):
        return {
            "collects": {
                commemoration.name: commemoration.evening_prayer_collect.replace(" Amen.", "")
                for commemoration in self.date.all_evening
                if commemoration.evening_prayer_collect
            }
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
        elif self.date.date.weekday() == 1 or self.date.date.weekday() == 4 or self.date.date.weekday() == 6:
            collect = mission_collects[1]
        elif self.date.date.weekday() == 2 or self.date.date.weekday() == 5:
            collect = mission_collects[1]

        return {"heading": "Prayer for Mission", "collect": collect}


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

        return {"collect": weekly_collects[self.date.date.weekday()]}


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
            (EPOpeningSentence(self.date), "office/evening_prayer/opening_sentence.html"),
            (EPConfession(self.date), "office/evening_prayer/confession.html"),
            (EPInvitatory(self.date), "office/evening_prayer/invitatory.html"),
            (Hymn(self.date), "office/evening_prayer/hymn.html"),
            (EPPsalms(self.date, self.office_readings), "office/evening_prayer/psalms.html"),
            (EPReading1(self.date, self.office_readings), "office/evening_prayer/reading.html"),
            (EPCanticle1(self.date, self.office_readings), "office/evening_prayer/canticle_1.html"),
            (EPReading2(self.date, self.office_readings), "office/evening_prayer/reading.html"),
            (EPCanticle2(self.date, self.office_readings), "office/evening_prayer/canticle_2.html"),
            (EPCreed(self.date, self.office_readings), "office/evening_prayer/creed.html"),
            (EPPrayers(self.date, self.office_readings), "office/evening_prayer/prayers.html"),
            (EPSuffrages(self.date, self.office_readings), "office/evening_prayer/suffrages.html"),
            (EPCollectsOfTheDay(self.date, self.office_readings), "office/evening_prayer/collects_of_the_day.html"),
            (EPCollects(self.date, self.office_readings), "office/evening_prayer/collects.html"),
            (EPMissionCollect(self.date, self.office_readings), "office/evening_prayer/mission_collect.html"),
        ]

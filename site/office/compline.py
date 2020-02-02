import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.offices import Office, OfficeSection
from psalter.utils import get_psalms


class Compline(Office):
    name = "Compline"
    office = "compline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Prayer Book: {}".format(
            "Compline (Bedtime Prayer)",
            self.get_formatted_date_string(),
            self.date.primary_evening.name,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=20, second=0)
        self.end_time = self.start_time.replace(minute=59, hour=23, second=59)

    @cached_property
    def modules(self):
        return [
            (ComplineHeading(self.date, self.office_readings), "office/heading.html"),
            (ComplineCommemorationListing(self.date, self.office_readings), "office/commemoration_listing.html"),
            (ComplineOpening(self.date, self.office_readings), "office/compline_opening.html"),
            (ComplineConfession(self.date, self.office_readings), "office/compline_confession.html"),
            (ComplineInvitatory(self.date, self.office_readings), "office/compline_invitatory.html"),
            (ComplinePsalms(self.date, self.office_readings), "office/minor_office_psalms.html"),
            (ComplineScripture(self.date, self.office_readings), "office/minor_office_scripture.html"),
            (ComplinePrayers(self.date, self.office_readings), "office/compline_prayers.html"),
            (ComplineCanticle(self.date, self.office_readings), "office/compline_canticle.html"),
            (ComplineConclusion(self.date, self.office_readings), "office/compline_conclusion.html"),
        ]


class ComplineHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Compline"), "calendar_date": self.date}


class ComplineCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": True,
            "heading": "This Nights's Commemoration{}".format("s" if len(self.date.all) > 1 else ""),
            "commemorations": self.date.all_evening,
        }


class ComplineOpening(OfficeSection):
    @cached_property
    def data(self):
        return {}


class ComplineConfession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin"}


class ComplineInvitatory(OfficeSection):
    @cached_property
    def data(self):
        return {
            "alleluia": self.date.evening_season.name != "Lent" and self.date.evening_season.name != "Holy Week",
            "heading": "Invitatory",
        }


class ComplinePsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Psalms", "psalms": get_psalms("4,31:1-6,91,134")}


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
                "citation": "MATTHEW 11:28-30",
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

    collects = [
        (
            "A Collect for Evening",
            "Visit this place, O Lord, and drive far from it all snares of the enemy; let your holy angels dwell with us to preserve us in peace; and let your blessing be upon us always; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Aid Against Peril",
            "Lighten our darkness, we beseech you, O Lord; and by your great mercy defend us from all perils and dangers of this night; for the love of your only Son, our Savior Jesus Christ.",
        ),
        (
            "A Collect for Evening",
            "Be present, O merciful God, and protect us through the hours of this night, so that we who are wearied by the changes and chances of this life may rest in your eternal changelessness; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Evening",
            "Look down, O Lord, from your heavenly throne, illumine this night with your celestial brightness, and from the children of light banish the deeds of darkness; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Saturdays",
            "We give you thanks, O God, for revealing your Son Jesus Christ to us by the light of his resurrection: Grant that as we sing your glory at the close of this day, our joy may abound in the morning as we celebrate the Paschal mystery; through Jesus Christ our Lord.",
        ),
        (
            "A Collect for Mission",
            "Keep watch, dear Lord, with those who work, or watch, or weep this night, and give your angels charge over those who sleep. Tend the sick, Lord Christ; give rest to the weary, bless the dying, soothe the suffering, pity the afflicted, shield the joyous; and all for your love’s sake.",
        ),
        (
            "A Collect for Evening",
            "O God, your unfailing providence sustains the world we live in and the life we live: Watch over those, both night and day, who work while others sleep, and grant that we may never forget that our common life depends upon each other’s toil; through Jesus Christ our Lord.",
        ),
    ]

    def get_collects(self):

        if self.date.date.weekday() in [6]:  # Sunday
            return self.collects[0], self.collects[1], self.collects[5]

        if self.date.date.weekday() in [0]:  # Monday
            return self.collects[2], self.collects[3], self.collects[5]

        if self.date.date.weekday() in [1]:  # Tuesday
            return self.collects[0], self.collects[2], self.collects[5]

        if self.date.date.weekday() in [2]:  # Wednesday
            return self.collects[1], self.collects[3], self.collects[6]

        if self.date.date.weekday() in [3]:  # Thursday
            return self.collects[0], self.collects[3], self.collects[5]

        if self.date.date.weekday() in [4]:  # Friday
            return self.collects[1], self.collects[2], self.collects[6]

        if self.date.date.weekday() in [5]:  # Saturday
            return self.collects[2], self.collects[4], self.collects[5]

    @cached_property
    def data(self):
        return {"heading": "The Prayers", "collects": self.get_collects()}


class ComplineCanticle(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "Nunc Dimittis",
            "subheading": "The Song of Simeon",
            "alleluia": self.date.evening_season.name == "Eastertide",
        }


class ComplineConclusion(OfficeSection):
    @cached_property
    def data(self):
        return {"alleluia": self.date.evening_season.name == "Eastertide"}

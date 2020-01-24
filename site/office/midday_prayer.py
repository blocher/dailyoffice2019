import datetime

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.offices import Office, OfficeSection
from psalter.utils import get_psalms


class MiddayPrayer(Office):
    name = "Midday Prayer"
    office = "midday_prayer"

    start_time = "11:00 AM"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "Office: {}, Date: {}, Commemoration: {}, Prayer Book: {}".format(
            "Midday Prayer",
            self.get_formatted_date_string(),
            self.date.primary_evening.name,
            "The Book of Common Prayer (2019), Anglican Church in North America",
        )

        self.start_time = datetime.datetime.combine(self.date.date, datetime.time())
        self.start_time = self.start_time.replace(minute=0, hour=11, second=0)
        self.end_time = self.start_time.replace(minute=0, hour=16, second=0)

    @cached_property
    def modules(self):
        return [
            (MiddayHeading(self.date, self.office_readings), "office/heading.html"),
            (MiddayCommemorationListing(self.date, self.office_readings), "office/commemoration_listing.html"),
            (MiddayInvitatory(self.date, self.office_readings), "office/midday_invitatory.html"),
            (MiddayPsalms(self.date, self.office_readings), "office/minor_office_psalms.html"),
            (MiddayScripture(self.date, self.office_readings), "office/minor_office_scripture.html"),
            (MiddayPrayers(self.date, self.office_readings), "office/midday_prayers.html"),
            (MiddayConclusion(self.date, self.office_readings), "office/midday_conclusion.html"),
        ]

class MiddayHeading(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": mark_safe("Midday Prayer"), "calendar_date": self.date}

class MiddayCommemorationListing(OfficeSection):
    @cached_property
    def data(self):
        return {
            "day": self.date,
            "evening": False,
            "heading": "This Day's Commemoration{}".format("s" if len(self.date.all) > 1 else ""),
            "commemorations": self.date.all,
        }

class MiddayInvitatory(OfficeSection):
    @cached_property
    def data(self):
        return {"alleluia": self.date.evening_season.name != "Lent" and self.date.evening_season.name != "Holy Week"}

class MiddayPsalms(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "The Psalms", "psalms": get_psalms("119:105-112,121,124,126")}

class MiddayScripture(OfficeSection):
    def get_scripture(self):

        if self.date.date.weekday() in [0, 3, 6]:
            return {
                "sentence": "Jesus said, “Now is the judgment of this world; now will the ruler of this world be cast out. And I, when I am lifted up from the earth, will draw all people to myself.”",
                "citation": "JOHN 12:31-32",
            }

        if self.date.date.weekday() in [1, 4]:
            return {
                "sentence": "If anyone is in Christ, he is a new creation. The old has passed away; behold, the new has come. All this is from God, who through Christ reconciled us to himself and gave us the ministry of reconciliation.",
                "citation": "2 CORINTHIANS 5:17-18",
            }

        if self.date.date.weekday() in [2, 5]:
            return {
                "sentence": "From the rising of the sun to its setting my name will be great among the nations, and in every place incense will be offered to my name, and a pure offering. For my name will be great among the nations, says the Lord of Hosts.",
                "citation": "MALACHI 1:11",
            }

    @cached_property
    def data(self):
        return {"heading": "The Reading", "sentence": self.get_scripture(), "midday": True}

class MiddayPrayers(OfficeSection):
    def get_collects(self):

        collects = [
            (
                "Blessed Savior, at this hour you hung upon the Cross, stretching out your loving arms: Grant that all the peoples of the earth may look to you and be saved; for your tender mercies’ sake."
            ),
            (
                "Almighty Savior, who at mid-day called your servant Saint Paul to be an apostle to the Gentiles: We pray you to illumine the world with the radiance of your glory, that all nations may come and worship you; for you live and reign with the Father and the Holy Spirit, one God, for ever and ever."
            ),
            (
                "Father of all mercies, you revealed your boundless compassion to your apostle Saint Peter in a three-fold vision: Forgive our unbelief, we pray, and so strengthen our hearts and enkindle our zeal, that we may fervently desire the salvation of all people, and diligently labor in the extension of your kingdom; through him who gave himself for the life of the world, your Son our Savior Jesus Christ."
            ),
            (
                "Pour your grace into our hearts, O Lord, that we who have known the incarnation of your Son Jesus Christ, announced by an angel to the Virgin Mary, may by his Cross and passion be brought to the glory of his resurrection; who lives and reigns with you, in the unity of the Holy Spirit, one God, now and for ever."
            ),
        ]

        if self.date.date.weekday() in [6]:  # Sunday
            return collects[0], collects[1]

        if self.date.date.weekday() in [0, 5]:  # Monday,  #Saturday
            return collects[2], collects[3]

        if self.date.date.weekday() in [1]:  # Tuesday
            return collects[0], collects[2]

        if self.date.date.weekday() in [2]:  # Wednesday
            return collects[1], collects[3]

        if self.date.date.weekday() in [3]:  # Thursday
            return collects[0], collects[3]

        if self.date.date.weekday() in [4]:  # Friday
            return collects[1], collects[2]

    @cached_property
    def data(self):
        return {"heading": "The Prayers", "collects": self.get_collects()}

class MiddayConclusion(OfficeSection):
    @cached_property
    def data(self):
        return {"alleluia": self.date.season.name == "Eastertide"}

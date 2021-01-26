import datetime

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.models import HolyDayOfficeDay, StandardOfficeDay, ThirtyDayPsalterDay
from office.utils import passage_to_citation


class Office(object):

    name = "Daily Office"
    modules = []

    def get_formatted_date_string(self):
        return "{dt:%A} {dt:%B} {dt.day}, {dt.year}".format(dt=self.date.date)

    def __init__(self, date):
        from churchcal.calculations import get_calendar_date

        self.date = get_calendar_date(date)

        try:
            self.office_readings = HolyDayOfficeDay.objects.get(commemoration=self.date.primary)
        except HolyDayOfficeDay.DoesNotExist:
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)

        self.thirty_day_psalter_day = ThirtyDayPsalterDay.objects.get(day=self.date.date.day)

        primary_feast_name = (
            self.date.primary_evening.name
            if self.name == "Evening Prayer" or self.name == "Compline"
            else self.date.primary.name
        )
        self.title = "{} for {}: {} | The Daily Office according to The Book of Common Prayer (2019)".format(
            self.name, self.get_formatted_date_string(), primary_feast_name
        )

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
                "label": "Morning",
                "link": reverse("morning_prayer", args=[today.year, today.month, today.day]),
            },
            "midday_prayer": {
                "label": "Midday",
                "link": reverse("midday_prayer", args=[today.year, today.month, today.day]),
            },
            "evening_prayer": {
                "label": "Evening",
                "link": reverse("evening_prayer", args=[today.year, today.month, today.day]),
            },
            "compline": {"label": "Compline", "link": reverse("compline", args=[today.year, today.month, today.day])},
            "family_morning_prayer": {
                "label": "Morning",
                "link": reverse("family_morning_prayer", args=[today.year, today.month, today.day]),
            },
            "family_midday_prayer": {
                "label": "Midday",
                "link": reverse("family_midday_prayer", args=[today.year, today.month, today.day]),
            },
            "family_early_evening_prayer": {
                "label": "Early Evening",
                "link": reverse("family_early_evening_prayer", args=[today.year, today.month, today.day]),
            },
            "family_close_of_day_prayer": {
                "label": "Close of Day",
                "link": reverse("family_close_of_day_prayer", args=[today.year, today.month, today.day]),
            },
            "current": self.office,
            "date": f"{today:%B} {today.day}, {today.year}",
        }


class OfficeSection(object):
    def __init__(self, date, office_readings=None, thirty_day_psalter_day=None, office=None):
        self.date = date
        self.office_readings = office_readings
        self.thirty_day_psalter_day = thirty_day_psalter_day
        self.office = office

    @cached_property
    def data(self):
        raise NotImplementedError


class Reading(OfficeSection):
    @staticmethod
    def closing(testament):
        return {
            "reader": "The Word of the Lord." if testament != "DC" else "Here ends the Reading.",
            "people": "Thanks be to God." if testament != "DC" else "",
        }

    def data(self):
        return {
            "heading": self.heading,
            "has_main_reading": self.has_main_reading,
            "has_abbreviated_reading": self.has_abbreviated_reading,
            "has_alternate_reading": self.has_alternate_reading,
            "has_alternate_abbreviated_reading": self.has_alternate_abbreviated_reading,
            "has_mass_reading": self.has_mass_reading,
            "has_abbreviated_mass_reading": self.has_abbreviated_mass_reading,
            "main_reading": self.get_main_reading(),
            "abbreviated_reading": self.get_abbreviated_reading(),
            "alternate_reading": self.get_alternate_reading(),
            "alternate_abbreviated_reading": self.get_alternate_abbreviated_reading(),
            "mass_reading": self.get_mass_reading(),
            "abbreviated_mass_reading": self.get_abbreviated_mass_reading(),
            "tag_prefix": self.tag,
        }


class ThirdReading(Reading):

    heading = "The Third Lesson"
    tag = "third-"

    @cached_property
    def has_main_reading(self):
        return False

    @cached_property
    def has_abbreviated_reading(self):
        return False

    @cached_property
    def has_alternate_reading(self):
        return False

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
            if reading.reading_number == 4 and reading.short_citation:
                return True
        return False

    def get_main_reading(self):
        return None

    def get_abbreviated_reading(self):
        return None

    def get_alternate_reading(self):
        return None

    def get_alternate_abbreviated_reading(self):
        return None

    def get_mass_reading(self):
        if not self.has_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 4:
                return {
                    "intro": passage_to_citation(reading.long_citation),
                    "passage": reading.long_citation,
                    "reading": reading.long_text,
                    "closing": self.closing(reading.testament),
                    "tag": "mass-reading",
                    "deuterocanon": reading.testament == "DC",
                }

        return None

    def get_abbreviated_mass_reading(self):
        if not self.has_abbreviated_mass_reading:
            return None
        for reading in self.date.mass_readings:
            if reading.reading_number == 4 and reading.short_citation:
                return {
                    "intro": passage_to_citation(reading.short_citation),
                    "passage": reading.short_citation,
                    "reading": reading.short_text,
                    "closing": self.closing(reading.testament),
                    "tag": "abbreviated-mass-reading",
                    "deuterocanon": reading.testament == "DC",
                }

        return None


class Confession(OfficeSection):
    @cached_property
    def data(self):
        return {"heading": "Confession of Sin", "fast_day": self.date.fast_day}


class Invitatory(OfficeSection):
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
        return {"heading": "The Prayers"}


class PandemicPrayers(OfficeSection):
    election_start_date = datetime.datetime.strptime("2020/10/27 0:00:00", "%Y/%m/%d %H:%M:%S").date()
    election_end_date = datetime.datetime.strptime("2020/11/04 23:59:59", "%Y/%m/%d %H:%M:%S").date()

    def get_collect_1(self):
        collects = [
            {
                "title": "In Time of Great Sickness and Mortality",
                "collect": "O Most mighty and merciful God, in this time of grievous sickness, we flee to you for comfort. Deliver us, we beseech you, from our peril; give strength and skill to all those who minister to the sick; prosper the means made use of for their cure; and grant that, perceiving how frail and uncertain our life is, we may apply our hearts unto that heavenly wisdom which leads to eternal life; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "Book of Common Prayer, 1928 (U.S.)".upper(),
            },
            {
                "title": "In the Time of any Common Plague or Sickness",
                "collect": "O Almighty God, who in your wrath sent a plague upon your own people in the wilderness for their obstinate rebellion against Moses and Aaron, and also in the time of King David, sent a plague of pestilence which killed seventy thousand, but remembering your mercy spared the rest: have pity upon us miserable sinners, who now are visited with great sickness and mortality; and in the same way that you then accepted an atonement and commanded the destroying Angel to cease from punishing: so it may now please you to withdraw from us this plague and grievous sickness, through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "Book of Common Prayer, 1662 (England)".upper(),
            },
            {
                "title": "Prayer for the Great Plague of 1665",
                "collect": "O Most gracious God, Father of mercies and of our Lord Jesus Christ, look down upon us, we beseech you, in much pity and compassion and behold our great misery and trouble. For there is wrath gone out against us, and the plague has begun. That dreadful arrow of yours sticks fast in our flesh, and the venom thereof fires our blood and drinks up our spirits. Should you suffer it to bring us all to the dust of death, we must yet still acknowledge that you are righteous, O Lord, and your judgements are just. For our transgressions multiplied against you, as the sand on the sea-shore might justly bring over us a deluge of your wrath. The cry of our sins that has pierced the very heavens might well return with showers of vengeance upon our heads. While our earth is defiled by the inhabitants of it, what wonder; if you command an evil angel to pour out his vial into our air to fill it with infection and the noisome pestilence and so to turn the very breath of our Life into the savour of death unto us all! But yet we beseech you, O our God, forget not to be gracious: neither shut up your loving kindness in displeasure. For his sake, who himself took our infirmities and bore our sicknesses, have mercy upon us; and say to the destroying Angel, “It is enough”. O let that blood of sprinkling, which speaks better things then that of Abel be upon the Lintel and the two side posts in all our dwellings, that the destroyer may pass by. Let the sweet odor of your blessed Son's all-sufficient sacrifice and intercession (infinitely more prevalent than the typical incense of Aaron) interpose between the living and the dead and be our full and perfect atonement, ever acceptable with you, that the plague may be stayed. O let us live and we will praise your Name, and these your judgments shall teach us to look every man into the plague of his own heart: that being cleansed from all our sins, we may serve you with pure hearts all our days, perfecting holiness in your fear until we come at last where there is no more sickness nor death through your tender mercies in him alone who is our Life, and our health, and our salvation, Jesus Christ, our ever blessed savior and redeemer.",
                "response": "Amen.",
                "citation": "1665, Gilbert Sheldon, Archbishop of Canterbury".upper(),
            },
        ]

        day_of_year = self.date.date.timetuple().tm_yday
        collect_number = day_of_year % 2
        if self.office.office == "morning_prayer":
            return collects[collect_number]
        return collects[1 - collect_number]

    def get_collect_2(self):
        collects = [
            {
                "title": "In Times of Natural Disaster",
                "collect": "Almighty God, by your Word you laid the foundations of the earth, set the bounds of the sea, and still the wind and waves. Surround us with your grace and peace, and preserve us through this plague. By your Spirit, lift up those who have fallen, strengthen those who work to rescue or rebuild, and fill us with the hope of your new creation; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#26, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "In Times of Social Conflict or Unrest",
                "collect": " Increase, O God, the spirit of neighborliness among us, that in peril we may uphold one another, in suffering tend to one another, and in homelessness, loneliness, or exile befriend one another. Grant us brave and enduring hearts that we may strengthen one another, until the disciplines and testing of these days are ended, and you again give peace in our time; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#44, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "For the Recovery of a Sick Person",
                "collect": "Almighty and immortal God, giver of life and health: We implore your mercy for your servants who are sickened by this virus, that by your blessing upon them and upon those who minister to them with your healing gifts, they may be restored to health of body and mind, according to your gracious will, and may give thanks to you in your holy Church; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#61, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "For Civil Authorities",
                "collect": "Almighty God, our heavenly Father, send down on those who hold public office, especially those working to stop the spread of the Coronavirus, the spirit of wisdom, charity, and justice; that with steadfast purpose they may faithfully serve in their offices to promote the well being of all people; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#30, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "For Those Who Serve Others",
                "collect": "O Lord our heavenly Father, whose blessed Son came not to be served, but to serve: We ask you to bless all who, following in his steps, give themselves to the service of others especially those who are laboring in this time of plague; endue them with wisdom, patience, and courage, that they may strengthen the weak and raise up those who fall, and, being inspired by your love, may worthily minister to the suffering, the friendless, and the needy; for the sake of him who laid down his life for us, your Son our Savior Jesus Christ.",
                "response": "Amen.",
                "citation": "#45, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "For the Medical Professions",
                "collect": "Almighty God, whose blessed Son Jesus Christ went about doing good, and healing all manner of sickness and disease among the people: Continue in our hospitals his gracious work among us especially in this time of plague and pandemic; console and heal the sick; grant to the physicians, nurses, and assisting staff wisdom and skill, diligence and patience; prosper their work, O Lord, and send down your blessing upon all who serve the suffering; through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#50, Book of Common Prayer (2019)".upper(),
            },
            {
                "title": "For Trustfulness in Times of Worry and Anxiety",
                "collect": "Most loving Father, you will us to give thanks for all things, to dread nothing but the loss of you, and to cast all our care on the One who cares for us. Preserve us from faithless fears and worldly anxieties, and grant that no clouds of this mortal life may hide from us the light of that love which is immortal, and which you have manifested unto us in your Son, Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#80, Book of Common Prayer (2019)".upper(),
            },
        ]

        if self.office.office == "morning_prayer":
            return collects[self.date.date.weekday()]

        return collects[6 - self.date.date.weekday()]

    def get_collect_3(self):
        if self.date.date >= self.election_start_date and self.date.date <= self.election_end_date:
            return {
                "title": "For an Election",
                "collect": "Almighty God, to whom we must account for all our powers and privileges: Guide and direct, we humbly pray, the minds of all those who are called to elect fit persons to serve in the presidency and offices across the country. Grant that in the exercise of our choice we may promote your glory, and the welfare of this nation. This we ask for the sake of our Lord and Savior Jesus Christ.",
                "response": "Amen.",
                "citation": "#31, Book of Common Prayer (2019)".upper(),
            }
        return None

    def get_collect_4(self):
        if self.date.date >= self.election_start_date and self.date.date <= self.election_end_date:

            return {
                "title": "For Our Nation",
                "collect": "Almighty God, who hast given us this good land for our heritage: We humbly beseech thee that we may always prove ourselves a people mindful of thy favor and glad to do thy will. Bless our land with honorable industry, sound learning, and pure conduct. Save us from violence, discord, and confusion; from pride and arrogance, and from every evil way. Defend our liberties, and fashion into one united people the multitudes brought hither out of many kindreds and tongues. Endue with the spirit of wisdom those to whom, in thy Name, we entrust the authority of government, that there may be justice and peace at home, and that, through obedience to thy law, we may show forth thy praise among the nations of the earth. In the time of prosperity, fill our hearts with thankfulness, and in the day of trouble, suffer not our trust in thee to fail; all of which we ask through Jesus Christ our Lord.",
                "response": "Amen.",
                "citation": "#39, Book of Common Prayer (2019)".upper(),
            }
        return None

    @cached_property
    def data(self):
        return {
            "collect_1": self.get_collect_1(),
            "collect_2": self.get_collect_2(),
            "collect_3": self.get_collect_3(),
            "collect_4": self.get_collect_4(),
        }


class Intercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "heading": "Intercessions and Thanksgivings",
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
    def get_fixed_grace(self):

        return {
            "officiant": "The grace of our Lord Jesus Christ, and the love of God, and the fellowship of the Holy Spirit, be with us all evermore.",
            "people": "Amen.",
            "citation": "2 CORINTHIANS 13:14",
        }

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

        return {
            "heading": "Dismissal",
            "officiant": officiant,
            "people": people,
            "grace": self.get_grace(),
            "fixed_grace": self.get_fixed_grace(),
        }


class FMCreed(OfficeSection):
    @cached_property
    def data(self):
        return {}


class FamilyRubricSection(OfficeSection):
    @cached_property
    def data(self):
        return {
            "rubric": mark_safe(
                "<br>These devotions follow the basic structure of the Daily Office of the Church and are particularly appropriate for families with young children.<br><br>The Reading and the Collect may be read by one person, and the other parts said in unison, or in some other convenient manner."
            )
        }


class FamilyIntercessions(OfficeSection):
    @cached_property
    def data(self):
        return {
            "title": "Intercessions",
            "rubric": mark_safe(
                "A hymn or canticle may be used.<br><br>Prayers may be offered for ourselves and others."
            ),
        }


class GreatLitany(OfficeSection):
    def get_names(self):
        feasts = self.date.all_evening if self.office.name == "evening_prayer" else self.date.all
        names = [feast.saint_name for feast in feasts if hasattr(feast, "saint_name") and feast.saint_name]
        names = ["the Blessed Virgin Mary"] + names
        return ", ".join(names)

    def get_leaders(self):
        parts = [
            '<span class="us">your servant Joe Biden, the President, </span>',
            '<span class="canada">your servants Her Majesty Queen Elizabeth, the Sovereign, and Justin Trudeau, the Prime Minister, </span>'
            '<span class="national_none">your servants, our national leaders, </span>',
        ]
        return mark_safe("".join(parts))

    def get_weekday_class(self):
        if self.office.office == "evening_prayer":
            start = "litany-ep-"
        else:
            start = "litany-mp-"
        if self.date.date.weekday() in (2, 4, 6):
            return start + "wfs"
        return start + "not-wfs"

    @cached_property
    def data(self):
        return {"names": self.get_names(), "leaders": self.get_leaders(), "weekday_class": self.get_weekday_class()}

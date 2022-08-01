from django.template.loader import render_to_string


class Canticle(object):
    latin_name = "Canticle"
    english_name = "Canticle"
    template = "canticle.html"
    seasons = []
    office = None
    gloria = True
    citation = None
    rubric = "The following Canticle is sung or said, all standing"

    @property
    def content(self):
        return render_to_string("office/canticles/" + self.template)


class MP1(Canticle):
    latin_name = "TE DEUM LAUDAMUS"
    english_name = "We Praise You, O God"
    template = "mp1.html"
    seasons = ["Outside Lent"]
    office = "morning"
    gloria = False
    citation = ""


class MP2(Canticle):
    latin_name = "BENEDICTUS ES, DOMINE"
    english_name = "A Song of Praise"
    template = "mp2.html"
    seasons = ["Lent"]
    office = "morning"
    gloria = False
    citation = "SONG OF THE THREE YOUNG MEN, 29-34"


class MP3(Canticle):
    latin_name = "BENEDICTUS"
    english_name = "The Song of Zechariah"
    template = "mp3.html"
    seasons = ["Anytime"]
    office = "morning"
    gloria = True
    citation = "LUKE 1:68-79"


class EP1(Canticle):
    latin_name = "MAGNIFICAT"
    english_name = "The Song of Mary"
    template = "ep1.html"
    seasons = ["Anytime"]
    office = "evening"
    gloria = True
    citation = "LUKE 1:46-55"


class EP2(Canticle):
    latin_name = "NUNC DIMITTIS"
    english_name = "The Song of Simeon"
    template = "ep2.html"
    seasons = ["Anytime"]
    office = "evening"
    gloria = True
    citation = "LUKE 2:29-32"


class S1(Canticle):
    latin_name = "MAGNA ET MIRABILIA"
    english_name = "The Song of the Redeemed"
    template = "s1.html"
    seasons = ["Advent", "Eastertide"]
    office = "supplemental"
    gloria = True
    citation = "REVELATION 15:3-4"


class S2(Canticle):
    latin_name = "SURGE, ILLUMINARE"
    english_name = "Arise, shine, for your light has come"
    template = "s2.html"
    seasons = ["Epiphany"]
    office = "supplemental"
    gloria = True
    citation = "ISAIAH 60:1-3, 11, 14, 18-19"


class S3(Canticle):
    latin_name = "KYRIE PANTOKRATOR"
    english_name = "A Song of Penitence"
    template = "s3.html"
    seasons = ["Lent"]
    office = "supplemental"
    gloria = False
    citation = "PRAYER OF MANASSEH, 1-2, 4, 6-7, 11-15"


class S4(Canticle):
    latin_name = "QUAERITE DOMINUM"
    english_name = "Seek the Lord while he wills to be found"
    template = "s4.html"
    seasons = ["Lent"]
    office = "supplemental"
    gloria = True
    citation = "ISAIAH 55:6-11"


class S5(Canticle):
    latin_name = "CANTEMUS DOMINO"
    english_name = "The Song of Moses"
    template = "s5.html"
    seasons = ["Eastertide"]
    office = "supplemental"
    gloria = True
    citation = "EXODUS 15:1-6, 11-13, 17-18"


class S6(Canticle):
    latin_name = "DIGNUS ES"
    english_name = "A Song to the Lamb"
    template = "s6.html"
    seasons = ["Ascensiontide", "Eastertide"]
    office = "supplemental"
    gloria = False
    citation = "REVELATION 4:11; 5:9-10, 13, 14"


class S7(Canticle):
    latin_name = "CANTATE DOMINO"
    english_name = "Sing unto the Lord"
    template = "s7.html"
    seasons = ["Eastertide", "Non-penitential seasons"]
    office = "supplemental"
    gloria = True
    citation = "PSALM 98"


class S8(Canticle):
    latin_name = "ECCE, DEUS"
    english_name = "Surely, it is God who saves me"
    template = "s8.html"
    seasons = ["Anytime"]
    office = "supplemental"
    gloria = True
    citation = "ISAIAH 12:2-6"


class S9(Canticle):
    latin_name = "DEUS MISEREATUR"
    english_name = "God be merciful"
    template = "s9.html"
    seasons = ["Anytime"]
    office = "supplemental"
    gloria = False
    citation = "PSALM 67"


class S10(Canticle):
    latin_name = "BENEDICITE, OMNIA OPERA DOMINI"
    english_name = "A Song of Creation"
    template = "s10.html"
    seasons = ["Saturday"]
    office = "supplemental"
    gloria = False
    citation = "SONG OF THE THREE YOUNG MEN, 35-65"


class O1(Canticle):
    latin_name = "GLORIA IN EXCELSIS"
    english_name = "Glory to God in the highest"
    template = "o1.html"
    seasons = ["Non-penitential seasons"]
    office = "other"
    gloria = False
    citation = ""


class O2(Canticle):
    latin_name = "JUBILATE"
    english_name = "Be Joyful"
    template = "o2.html"
    seasons = ["When the Benedictus occurs"]
    office = "other"
    gloria = False
    citation = "PSALM 100"


class CanticleRules(object):
    def get_mp_canticle_1(self, calendar_date):
        raise NotImplementedError

    def get_mp_canticle_2(self, calendar_date):
        raise NotImplementedError

    def get_ep_canticle_1(self, calendar_date):
        raise NotImplementedError

    def get_ep_canticle_2(self, calendar_date):
        raise NotImplementedError


class DefaultCanticles(CanticleRules):
    def get_mp_canticle_1(self, calendar_date):
        if calendar_date.season.name in ["Lent", "Holy Week"]:
            return MP2
        return MP1

    def get_mp_canticle_2(self, calendar_date):
        return MP3

    def get_ep_canticle_1(self, calendar_date):
        return EP1

    def get_ep_canticle_2(self, calendar_date):
        return EP2


class BCP1979CanticleTable(CanticleRules):
    def get_mp_canticle_1(self, calendar_date):

        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return MP3

        if calendar_date.date.weekday() == 6:  # Sunday
            if calendar_date.season.name == "Advent":
                return S2

            if calendar_date.season.name in ["Lent", "Holy Week"]:
                return S3

            if calendar_date.season.name == "Eastertide":
                return S5

            return MP3

        if calendar_date.date.weekday() == 0:  # Monday
            return S8

        if calendar_date.date.weekday() == 1:  # Tuesday
            return MP2

        if calendar_date.date.weekday() == 2:  # Wednesday
            if calendar_date.season.name in ["Lent", "Holy Week"]:
                return S3

            return S2

        if calendar_date.date.weekday() == 3:  # Thursday
            return S5

        if calendar_date.date.weekday() == 4:  # Friday
            if calendar_date.season.name in ["Lent", "Holy Week"]:
                return S3

            return S4

        if calendar_date.date.weekday() == 5:  # Thursday
            return S10

    def get_mp_canticle_2(self, calendar_date):

        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return MP1

        if calendar_date.date.weekday() == 6:  # Sunday
            if calendar_date.season.name in ["Advent", "Lent", "Holy Week"]:
                return MP3

            return MP1

        if calendar_date.date.weekday() == 0:  # Monday
            return S1

        if calendar_date.date.weekday() == 1:  # Tuesday
            return S6

        if calendar_date.date.weekday() == 2:  # Wednesday
            return MP3

        if calendar_date.date.weekday() == 3:  # Thursday
            if calendar_date.season.name in ["Advent", "Lent", "Holy Week"]:
                return S1

            return O1

        if calendar_date.date.weekday() == 4:  # Friday
            return S6

        if calendar_date.date.weekday() == 5:  # Saturday
            return S1

    def get_ep_canticle_1(self, calendar_date):
        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return EP1

        if calendar_date.date.weekday() == 6:  # Sunday
            return EP1

        if calendar_date.date.weekday() == 0:  # Monday
            if calendar_date.season.name in ["Lent", "Holy Week"]:
                return S3
            return S5

        if calendar_date.date.weekday() == 1:  # Tuesday
            return S4

        if calendar_date.date.weekday() == 2:  # Wednesday
            return S10

        if calendar_date.date.weekday() == 3:  # Thursday
            return S2

        if calendar_date.date.weekday() == 4:  # Friday
            return MP2

        if calendar_date.date.weekday() == 5:  # Saturday
            return S8

    def get_ep_canticle_2(self, calendar_date):
        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return EP2

        if calendar_date.date.weekday() in [6, 0, 2, 4]:  # Sunday, Monday, Wednesday, Friday
            return EP2

        return EP1


class REC2011CanticleTable(CanticleRules):
    def get_mp_canticle_1(self, calendar_date):

        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return MP1

        if calendar_date.date.weekday() == 6:  # Sunday
            return MP1

        if calendar_date.season.name == "Christmastide":
            return MP1

        if calendar_date.season.name == "Advent":
            return S1

        if calendar_date.season.name == "Epiphanytide":
            return S2

        if calendar_date.season.name in ["Lent", "Holy Week"]:
            return MP2

        for commemoration in calendar_date.all:
            if "Ascension" in commemoration.name or "Day of Pentecost" in commemoration.name:
                return S6

        if calendar_date.season.name == "Eastertide":
            return S5

        if calendar_date.season.name == "Season After Pentecost":

            if calendar_date.date.weekday() == 5:
                return S10
            return S8

        return MP1

    def get_mp_canticle_2(self, calendar_date):
        if calendar_date.date.month == 4 and calendar_date.date.day == 29:
            return O2
        return MP3

    def get_ep_canticle_1(self, calendar_date):
        if calendar_date.date.month == 11 and calendar_date.date.day == 13:
            return S7
        return EP1

    def get_ep_canticle_2(self, calendar_date, office_readings):
        if (
            calendar_date.primary.rank.precedence_rank in [1, 3]
            and calendar_date.primary.rank.name != "PRIVILEGED_OBSERVANCE"
        ):
            return EP2

        # First and Second Evensong of Sunday
        if calendar_date.date.weekday() == 5 or calendar_date.date.weekday() == 6:
            return EP2

        if calendar_date.season.name == "Advent":
            return S4

        if calendar_date.season.name in ["Lent", "Holy Week"]:
            return S3

        if calendar_date.season.name in ["Christmastide", "Eastertide"]:
            return S7

        if calendar_date.season.name in ["Epiphanytide", "Season After Pentecost"]:
            thirty_day = S9
            sixty_day = S9
            if calendar_date.date.day == 12:
                thirty_day = EP2
            if "67" in office_readings.ep_psalms:
                sixty_day = EP2
            if thirty_day == sixty_day:
                return thirty_day
            return (thirty_day, sixty_day)

        return EP2

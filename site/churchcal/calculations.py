from collections import OrderedDict
from datetime import datetime, timedelta, date

from dateutil.parser import parse

from django.utils.functional import cached_property
from indexed import IndexedOrderedDict

from .utils import advent, week_days
from churchcal.models import Commemoration, FerialCommemoration, Proper, Season, Calendar, CommemorationRank

from django.core.cache import cache


class CalendarDate(object):
    def __init__(self, date, calendar, year):

        self.date = date
        self.calendar = calendar

        self.required = []
        self.optional = []
        self.primary = None
        self.finalized = False

        self.season = None

        self.year = year

    def _find_proper(self):
        date = datetime.strptime("2019-{}-{}".format(self.date.month, self.date.day), "%Y-%m-%d").date()
        return Proper.objects.filter(calendar=self.calendar, start_date__lte=date, end_date__gte=date).first()

    @property
    def all(self):
        return self.required + self.optional

    @property
    def all_evening(self):
        required = self.evening_required if hasattr(self, "evening_required") else self.required
        optional = self.evening_optional if hasattr(self, "evening_optional") else self.optional
        return required + optional

    @property
    def primary_evening(self):
        return self.all_evening[0]

    @cached_property
    def proper(self):
        if self.season.name != "Season After Pentecost" and self.primary.name != "The Day of Pentecost":
            return None

        if self.date.weekday() == 6:
            return self._find_proper()

        return None

    @cached_property
    def office_year(self):

        return 1 if self.year.start_year % 2 == 0 else 2


    FAST_NONE = 0
    FAST_PARTIAL = 1
    FAST_FULL = 2
    FAST_DAYS_RANKS = {FAST_NONE: "None", FAST_PARTIAL: "Fast", FAST_FULL: "Fast (Total abstinence)"}

    @cached_property
    def fast_day(self):

        # Sundays are never fast days
        if self.date.weekday() == 6:
            return self.FAST_NONE

        if self.primary.name == "Ash Wednesday" or self.primary.name == "Good Friday":
            return self.FAST_FULL

        # Ember days and rogation days are fast days
        if len(self.required) == 0:
            for optional in self.optional:
                if optional.rank.name in ["EMBER_DAY", "ROGATION_DAY"]:
                    return self.FAST_PARTIAL

        # Christmas and Easter are never fast days
        if self.season.name in ["Christmastide", "Eastertide"]:
            return self.FAST_NONE


        # Not for primary feasts (Annunciation)
        if self.primary.rank.name == "PRINCIPAL_FEAST":
            return self.FAST_NONE


        # All of lent is a fast day
        if self.season.name == "Lent" or self.season.name == "Holy Week":
            return self.FAST_PARTIAL

        # Fridays
        if self.date.weekday() == 4:

            return self.FAST_PARTIAL

        return self.FAST_NONE

    def _sort_commemorations(self):

        self.required = sorted(self.required, key=lambda commemoration: (commemoration.rank.precedence_rank))
        self.optional = sorted(self.optional, key=lambda commemoration: (commemoration.rank.precedence_rank))

    def add_commemoration(self, commemoration):

        if not commemoration.rank.required:
            self.optional.append(commemoration)
        else:
            self.required.append(commemoration)

        self._sort_commemorations()

    def apply_rules(self):

        self._sort_commemorations()

        transfers = self.process_transfers()
        self.finalize_day()
        return transfers

    def handle_privileged_lesser_feast(self):

        if len(self.required) < 1:
            return None

        if self.required[0].rank.name != "PRIVILEGED_LESSER_FEAST":
            return None

        if len(self.optional) < 1:
            return None

        required = self.required
        self.required = []
        return required

    def process_transfers(self):

        transfers = self.handle_privileged_lesser_feast()
        if transfers:
            return transfers

        if len(self.required) < 2:
            return []

        required = self.required.copy()
        if self.season.name not in ("Advent", "Lent", "Holy Week", "Eastertide"):
            if self.required[1].rank.name == "HOLY_DAY":
                alternate_sunday = self.required[1].copy()
                alternate_sunday.rank = CommemorationRank.objects.get(calendar=self.calendar, name="ALTERNATE_SUNDAY")
                self.required = self.required[:1] + [alternate_sunday]
            else:
                self.required = self.required[:1]
        else:
            self.required = required[:1]
        transfers = required[1:]
        for transfer in transfers:
            transfer.transferred = True
        return [feast for feast in transfers if feast.rank.name != "SUNDAY"]

    def append_feria_if_needed(self):

        # Don't append Feria to a Sunday!
        if self.date.weekday() == 6:
            return

        if self.required and self.required[0].rank.name == "PRIVILEGED_OBSERVANCE":
            return

        if SetNamesAndCollects.has_collect_for_feria(self):
            return

        self.optional.append(FerialCommemoration(self.date, self.season, self.calendar))

    def finalize_day(self):

        self.append_feria_if_needed()
        self.optional = sorted(self.optional, key=lambda commemoration: (commemoration.rank.precedence_rank))

        if len(self.required) > 0:
            self.primary = self.required[0]
        else:
            self.primary = self.optional[0]
        self.finalized = True

    def __repr__(self):
        return "{} {} - {}".format(
            self.date.strftime("%A"),
            str(self.date),
            " | ".join(["{} {}".format(commemoration.name, commemoration.rank.name) for commemoration in self.all]),
        )


class ChurchYearIterator:
    def __init__(self, church_year, start_position=-1, key=None):
        self._church_year = church_year
        self._index = start_position + 1
        self._public_index = start_position
        if key:
            self.jump_by_key(key)

    def __next__(self):
        if self._index < len(self._church_year.dates):
            result = self._church_year.dates.values()[self._index]
            self._index += 1
            self._public_index += 1
            return result
        raise StopIteration

    def next(self):
        if self.index >= len(self.self._church_year.dates):
            raise StopIteration
        self._public_index += 1
        self._index += 1
        return self._church_year.dates.values()[self._public_index]

    def previous(self):
        if self._index <= 0:
            raise StopIteration
        self._public_index -= 1
        self._index -= 1
        result = self._church_year.dates.values()[self._public_index]

        return result

    def get_current(self):
        return self._church_year.dates.values()[self._public_index]

    def get_previous(self):
        if self._index <= 0:
            raise None
        return self._church_year.dates.values()[self._public_index - 1]

    def get_next(self):
        if self._index >= len(self._church_year.dates):
            return None
        return self._church_year.dates.values()[self._public_index + 1]

    def get_by_index(self, index):
        return self._church_year.dates.values()[index]

    def get_by_key(self, key):
        index = self._church_year.dates.keys().index(key)
        return self.get_by_index(index)

    def jump_by_index(self, index):
        result = self._church_year.dates.values()[index]
        self._index = index + 1
        self._public_index = index
        return result

    def jump_by_key(self, key):
        index = self._church_year.dates.keys().index(key)
        return self.jump_by_index(index)

    def get_current_index(self):
        return self._public_index


class ChurchYear(object):
    def __iter__(self):
        return ChurchYearIterator(self)

    def __init__(self, year_of_advent, calendar="ACNA_BCP2019"):

        self.calendar = Calendar.objects.filter(abbreviation=calendar).first()

        self.start_year = year_of_advent
        self.end_year = year_of_advent + 1

        self.dates = IndexedOrderedDict()

        start_date = advent(year_of_advent)
        end_date = advent(year_of_advent + 1) - timedelta(days=1)

        self.seasons = self._get_seasons()
        self.season_tracker = None
        # create each date
        for single_date in self.daterange(start_date, end_date):
            name = single_date.strftime("%Y-%m-%d")
            self.dates[name] = CalendarDate(single_date, calendar=self.calendar, year=self)

        # add commemorations to date
        commemorations = (
            Commemoration.objects.select_related("rank", "cannot_occur_after__rank")
            .filter(calendar__abbreviation=calendar)
            .all()
        )
        already_added = []
        for commemoration in commemorations:

            if not commemoration.can_occur_in_year(self.start_year):
                continue

            try:
                self.dates[commemoration.initial_date_string(self.start_year)].add_commemoration(commemoration)
                already_added.append(commemoration.pk)

            except KeyError:
                pass

        for key, calendar_date in self.dates.items():

            # seasons
            self._set_season(calendar_date)

            # apply transfers
            transfers = calendar_date.apply_rules()
            new_date = (calendar_date.date + timedelta(days=1)).strftime("%Y-%m-%d")
            if new_date in self.dates.keys():
                self.dates[new_date].required = transfers + self.dates[new_date].required

        SetNamesAndCollects(self)

        # print(
        #     "{} = {} - {} {}".format(
        #         calendar_date.season,
        #         calendar_date.date.strftime("%a, %b, %d, %Y"),
        #         calendar_date.primary.__repr__(),
        #         "(Proper {})".format(calendar_date.proper.number) if calendar_date.proper else "",
        #         "+" if calendar_date.day_of_special_commemoration else "",
        #     )
        #
        # )
        # print(calendar_date.required, calendar_date.optional)

        # #print("{} - {} - {}".format(self.mass_year, sself.daily_mass_year, self.office_year))

    def _get_seasons(self):
        seasons = (
            Season.objects.filter(calendar=Calendar.objects.filter(abbreviation=self.calendar.abbreviation).get())
            .order_by("order")
            .all()
        )
        season_mapping = {}
        for season in seasons:
            season_mapping[season.start_commemoration.name] = season
        self.seasons = season_mapping
        # print(self.seasons)

    def _set_season(self, calendar_date):

        calendar_date.season = self.season_tracker
        calendar_date.evening_season = calendar_date.season

        if not calendar_date.required:
            return

        possible_days = [feast.name for feast in calendar_date.required]

        if not self.seasons:
            self._get_seasons()

        if "The Day of Pentecost" in possible_days:
            calendar_date.season = self.season_tracker

        for match in self.seasons.keys():
            if match in possible_days:
                self.season_tracker = self.seasons[match]
                if "The Day of Pentecost" not in possible_days:
                    calendar_date.season = self.season_tracker

        calendar_date.evening_season = calendar_date.season


    @staticmethod
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days + 1)):
            yield start_date + timedelta(n)

    @cached_property
    def mass_year(self):

        if self.start_year % 3 == 0:
            return "A"

        if self.start_year % 3 == 1:
            return "B"

        if self.start_year % 3 == 2:
            return "C"

    @cached_property
    def daily_mass_year(self):

        return 1 if self.end_year % 2 != 0 else 2

    @cached_property
    def office_year(self):

        return "I" if self.start_year % 2 == 0 else "II"

    @cached_property
    def first_date(self):
        return self.dates[:1]

    @cached_property
    def last_date(self):
        return self.dates[-1]

    def get_date(self, date_string):
        date = to_date(date_string)
        try:
            date = self.dates[date.strftime("%Y-%m-%d")]
            date.year = self
            return date
        except KeyError:
            print(date)
            print(date.strftime("%Y-%m-%d"))
            return None


class CalendarYear(object):
    def __init__(self, year):

        first_year = year - 1
        second_year = year

        first_year = ChurchYear(first_year)
        second_year = ChurchYear(second_year)

        dates = IndexedOrderedDict(list(first_year.dates.items()) + list(second_year.dates.items()))

        base = datetime(year, 1, 1)
        date_list = [base + timedelta(days=x) for x in range(0, 365)]

        self.dates = [dates[date.strftime("%Y-%m-%d")] for date in date_list]


class SetNamesAndCollects(object):
    def __init__(self, church_calendar):

        self.church_calendar = church_calendar

        checks = [self.own_collect, self.proper_collect, self.feria_collect, self.saint_collect, self.fallback_collect]

        self.i = iter(self.church_calendar)
        while True:
            try:
                calendar_date = next(self.i)
                # print(calendar_date.date, calendar_date.primary.name, self.i.get_previous().primary.name, self.i.get_next().primary.name)

                for commemoration in calendar_date.all:

                    for check in checks:
                        check(commemoration, calendar_date)
                        if hasattr(commemoration, "morning_prayer_collect"):
                            break
                    self.check_previous_evening(calendar_date)
            except StopIteration:
                break

    def check_previous_evening(self, calendar_date):

        if calendar_date.primary.rank.precedence_rank > 4:
            return

        if calendar_date.primary.rank.name == "PRIVILEGED_OBSERVANCE":
            return

        previous = self.i.get_previous()
        if not previous:
            return

        if previous.primary.rank.required and previous.primary.rank.name != "PRIVILEGED_OBSERVANCE":
            return

        previous.evening_required = previous.required.copy()
        previous.evening_optional = previous.optional.copy()
        feast_copy = calendar_date.primary.copy()
        feast_copy.name = "Eve of {}".format(feast_copy.name)

        if feast_copy.eve_collect:
            feast_copy.evening_prayer_collect = feast_copy.eve_collect

        previous.evening_required.append(feast_copy)

        for idx, commemoration in enumerate(previous.evening_required):
            if "PRIVILEGED_OBSERVANCE" in commemoration.rank.name:
                previous.evening_required.pop(idx)

        if feast_copy.rank.name == "SUNDAY":
            for idx, commemoration in enumerate(previous.evening_optional):
                if "FERIA" in commemoration.rank.name:
                    previous.evening_optional.pop(idx)

        previous.evening_season = calendar_date.season

        # @TODO: resort

    def own_collect(self, commemoration, calendar_date):

        if "FERIA" in commemoration.rank.name:
            return False

        if commemoration.collect:

            commemoration.morning_prayer_collect = (
                commemoration.evening_prayer_collect
            ) = commemoration.collect.replace(" [this day]", " this day")
            if commemoration.alternate_collect:
                commemoration.evening_prayer_collect = commemoration.alternate_collect

    def proper_collect(self, commemoration, calendar_date):
        if not commemoration.rank.required:
            return
        if calendar_date.proper and calendar_date.proper.collect:
            commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = calendar_date.proper.collect
            if commemoration.rank.name == "SUNDAY":
                proper_string = " (Proper {})".format(calendar_date.proper.number)
                commemoration.name = "{}{}".format(commemoration.name, proper_string)

    def feria_collect(self, commemoration, calendar_date):

        if "FERIA" in commemoration.rank.name:
            i = self.i.get_current_index()
            while True:
                i = i - 1
                previous = self.i.get_by_index(i)
                if not previous:
                    break
                if self.has_collect_for_feria(previous):
                    if previous.proper and previous.proper.collect:
                        commemoration.morning_prayer_collect = previous.proper.collect
                        commemoration.evening_prayer_collect = previous.proper.collect
                        name = previous.primary.name
                        if name[:3] == "The":
                            name = name.replace("The ", "the ")
                        if previous.primary.rank.name == "PRINCIPAL_FEAST":
                            proper_string = " (Proper {})".format(previous.proper.number)
                            commemoration.name = "{} after {}{}".format(
                                week_days[calendar_date.date.weekday()], name, proper_string
                            )
                        else:
                            commemoration.name = "{} after {}".format(week_days[calendar_date.date.weekday()], name)
                    else:
                        commemoration.morning_prayer_collect = previous.primary.morning_prayer_collect.replace(
                            "to be born this day of a pure virgin", "to be born of a pure virgin"
                        )
                        commemoration.evening_prayer_collect = previous.primary.evening_prayer_collect.replace(
                            "to be born this day of a pure virgin", "to be born of a pure virgin"
                        )
                        commemoration.name = "{} after {}".format(
                            week_days[calendar_date.date.weekday()], previous.primary.name.replace("The ", "the ")
                        )

                    break
        return False

    def saint_collect(self, commemoration, calendar_date):
        if not commemoration.saint_type:
            return False

        if commemoration.saint_type == "PASTOR":
            if commemoration.saint_gender in ["M", "F"]:
                text = "O God, our heavenly Father, you raised up your faithful servant {} to be a {} pastor in your Church and to feed your flock: Give abundantly to all pastors the gifts of your Holy Spirit, that they may minister in your household as true servants of Christ and stewards of your divine mysteries; through Jesus Christ our Lord, who lives and reigns with you and the Holy Spirit, one God, for ever and ever.".format(
                    commemoration.saint_name, commemoration.saint_fill_in_the_blank
                ).replace(
                    " ", " "
                )
            else:
                text = "O God, our heavenly Father, you raised up your faithful servants {} to be {} pastors in your Church and to feed your flock: Give abundantly to all pastors the gifts of your Holy Spirit, that they may minister in your household as true servants of Christ and stewards of your divine mysteries; through Jesus Christ our Lord, who lives and reigns with you and the Holy Spirit, one God, for ever and ever.".format(
                    commemoration.saint_name, commemoration.saint_fill_in_the_blank
                ).replace(
                    " ", " "
                )

        if commemoration.saint_type == "MONASTIC":
            text = "O God, your blessed Son became poor for our sake, and chose the Cross over the kingdoms of this world: Deliver us from an inordinate love of worldly things, that we, inspired by the devotion of your servant{} {}, may seek you with singleness of heart, behold your glory by faith, and attain to the riches of your everlasting kingdom, where we shall be united with our Savior Jesus Christ; who lives and reigns with you and the Holy Spirit, one God, now and for ever. ".format(
                "s" if commemoration.saint_gender == "P" else "", commemoration.saint_name
            )

        if commemoration.saint_type == "MARTYR":
            text = "Almighty God, you gave your servant{} {} boldness to confess the Name of our Savior Jesus Christ before the rulers of this world, and courage to die for this faith: Grant that we may always be ready to give a reason for the hope that is in us, and to suffer gladly for the sake of our Lord Jesus Christ; who lives and reigns with you and the Holy Spirit, one God, for ever and ever. ".format(
                "s" if commemoration.saint_gender == "P" else "", commemoration.saint_name
            )

        if commemoration.saint_type == "MISSIONARY":
            text = (
                "Almighty and everlasting God, you called your servant{} {} to preach the Gospel {}: Raise up in this and every land evangelists and heralds of your kingdom, that your Church may proclaim the unsearchable riches of our Savior Jesus Christ; who lives and reigns with you and the Holy Spirit, one God, now and for ever. ".format(
                    "s" if commemoration.saint_gender == "P" else "",
                    commemoration.saint_name,
                    commemoration.saint_fill_in_the_blank,
                )
                .replace(" ", " ")
                .replace(" :", ":")
            )

        if commemoration.saint_type == "TEACHER":
            text = "Almighty God, you gave your servant{} {} special gifts of grace to understand and teach the truth revealed in Christ Jesus: Grant that by this teaching we may know you, the one true God, and Jesus Christ whom you have sent; who lives and reigns with you and the Holy Spirit, one God, for ever and ever.  Amen.".format(
                "s" if commemoration.saint_gender == "P" else "", commemoration.saint_name
            )

        if commemoration.saint_type == "RENEWER":
            text = "Almighty and everlasting God, you kindled the flame of your love in the heart of your servant{} {} to manifest your compassion and mercy to the poor and the persecuted: Grant to us, your humble servants, a like faith and power of love, that we who give thanks for {} righteous zeal may profit by {} example; through Jesus Christ our Lord, who lives and reigns with you and the Holy Spirit, one God, for ever and ever.".format(
                "s" if commemoration.saint_gender == "P" else "",
                commemoration.saint_name,
                "his"
                if commemoration.saint_gender == "M"
                else "her"
                if commemoration.saint_gender == "F"
                else "their",
                "his"
                if commemoration.saint_gender == "M"
                else "her"
                if commemoration.saint_gender == "F"
                else "their",
            )

        if commemoration.saint_type == "REFORMER":
            text = "O God, by your grace your servant{} {}, kindled by the flame of your love, became {} burning and shining light{} in your Church, turning pride into humility and error into truth: Grant that we may be set aflame with the same spirit of love and discipline, and walk before you as children of light; through Jesus Christ our Lord, who lives and reigns with you, in the unity of the Holy Spirit, one God, now and for ever.".format(
                "s" if commemoration.saint_gender == "P" else "",
                commemoration.saint_name,
                "a" if commemoration.saint_gender != "P" else "",
                "s" if commemoration.saint_gender == "P" else "",
            ).replace(
                " ", " "
            )

        if commemoration.saint_type == "ECUMENIST":
            text = "Almighty God, we give you thanks for the ministry of {}, who labored that the Church of Jesus Christ might be one: Grant that we, instructed by {} teaching and example, and knit together in unity by your Spirit, may ever stand firm upon the one foundation, which is Jesus Christ our Lord; who lives and reigns with you, in the unity of the Holy Spirit, one God, now and for ever.".format(
                commemoration.saint_name,
                "his"
                if commemoration.saint_gender == "M"
                else "her"
                if commemoration.saint_gender == "F"
                else "their",
            )

        if commemoration.saint_type == "SAINT_1":
            text = "Almighty God, you have surrounded us with a great cloud of witnesses: Grant that we, encouraged by the good example of your servant{} {}, may persevere in running the race that is set before us, until at last, with {}, we attain to your eternal joy; through Jesus Christ, the pioneer and perfecter of our faith, who lives and reigns with you and the Holy Spirit, one God, for ever and ever. ".format(
                "s" if commemoration.saint_gender == "P" else "",
                commemoration.saint_name,
                "him" if commemoration.saint_gender == "M" else "her" if commemoration.saint_gender == "F" else "them",
            )

        if commemoration.saint_type == "SAINT_2":
            text = "Almighty God, by your Holy Spirit you have made us one with your saints in heaven and on earth: Grant that in our earthly pilgrimage we may always be supported by this fellowship of love and prayer, and know ourselves to be surrounded by their witness to your power and mercy; for the sake of Jesus Christ, in whom all our intercessions are acceptable through the Spirit, and who lives and reigns with you and the same Spirit, one God, for ever and ever."

        if text:
            commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = text

    def fallback_collect(self, commemoration, calendar_date):
        commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = None

    @staticmethod
    def has_collect_for_feria(calendar_date):

        epiphany = SetNamesAndCollects.is_epiphany(calendar_date)
        if epiphany:
            return epiphany
        christmas = SetNamesAndCollects.is_christmas(calendar_date)
        if christmas:
            return christmas
        ash_wednesday = SetNamesAndCollects.is_ash_wednesday(calendar_date)
        if ash_wednesday:
            return ash_wednesday
        ascension = SetNamesAndCollects.is_ascension(calendar_date)
        if ascension:
            return ascension
        sunday = SetNamesAndCollects.is_sunday(calendar_date)
        if sunday:
            return sunday

        return False

    @staticmethod
    def is_epiphany(calendar_date):
        if calendar_date.required and "The Epiphany" in calendar_date.required[0].name and calendar_date.required[0].rank.required:
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_christmas(calendar_date):
        if calendar_date.required and "Christmas Day" in calendar_date.required[0].name and calendar_date.required[0].rank.required:
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_ash_wednesday(calendar_date):
        if calendar_date.required and "Ash Wednesday" in calendar_date.required[0].name and calendar_date.required[0].rank.required:
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_ascension(calendar_date):
        if calendar_date.required and "Ascension Day" in calendar_date.required[0].name and calendar_date.required[0].rank.required:
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_sunday(calendar_date):
        if calendar_date.date.weekday() == 6:
            for commemoration in calendar_date.all:
                if commemoration.rank.name == "PRINCIPAL_FEAST" and "Pentecost" in commemoration.name:
                    return commemoration
                if commemoration.rank.name == "PRINCIPAL_FEAST" and "Trinity" in commemoration.name:
                    return commemoration
                if commemoration.rank.name == "PRINCIPAL_FEAST" and "Easter" in commemoration.name:
                    return commemoration
            for commemoration in calendar_date.all:
                if commemoration.rank.name == "SUNDAY":
                    return commemoration
            return None
        return None


def to_date(date_string):
    if isinstance(date_string, datetime):
        return date_string.date()

    if isinstance(date_string, date):
        return date

    if isinstance(date_string, str):
        try:
            return parse(date_string).date()
        except ValueError:
            return None

    return None


def get_calendar_date(date_string):
    date = to_date(date_string)
    advent_start = advent(date.year)
    year = date.year if date >= advent_start else date.year - 1
    church_year = ChurchYear(year)
    # church_year = cache.get(str(year))
    # if not church_year:
    #     church_year = ChurchYear(year)
    #     cache.set(str(year), church_year)
    return church_year.get_date(date_string)

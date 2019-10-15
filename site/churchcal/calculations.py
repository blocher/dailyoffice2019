from collections import OrderedDict
from datetime import datetime, timedelta, date

from dateutil.parser import parse

from django.utils.functional import cached_property
from indexed import IndexedOrderedDict

from .utils import advent, week_days
from churchcal.models import Commemoration, FerialCommemoration, Proper, Season, Calendar, CommemorationRank
import copy


class CalendarDate(object):
    def __init__(self, date, calendar):

        self.date = date
        self.calendar = calendar

        self.required = []
        self.optional = []
        self.primary = None
        self.finalized = False

        self.season = None

    def _find_proper(self):
        date = datetime.strptime("2019-{}-{}".format(self.date.month, self.date.day), "%Y-%m-%d").date()
        return Proper.objects.filter(calendar=self.calendar, start_date__lte=date, end_date__gte=date).first()

    @property
    def all(self):
        return self.required + self.optional

    @cached_property
    def proper(self):
        if self.season.name != "Season After Pentecost" and self.primary.name != "The Day of Pentecost":
            return None

        if self.date.weekday() == 6:
            return self._find_proper()

        return None

    FAST_NONE = 0
    FAST_PARTIAL = 1
    FAST_FULL = 2
    FAST_DAYS_RANKS = {FAST_NONE: "None", FAST_PARTIAL: "Fast", FAST_FULL: "Fast (Total abstinence)"}

    @cached_property
    def fast_day(self):

        # Sundays are never fast days
        if self.date.weekday() == 6:
            return self.FAST_NONE

        # Christmas and Easter are never fast days
        if self.season.name in ["Christmastide", "Eastertide"]:
            return self.FAST_NONE

        if self.primary.name == "Ash Wednesday" or self.primary.name == "Good Friday":
            return self.FAST_FULL

        # Not for primary feasts (Annunciation)
        if self.primary.rank.precedence_rank == 1:
            return self.FAST_NONE

        # Ember days and rogation days are fast days
        if len(self.required) == 0:
            for optional in self.optional:
                if optional.rank.name in ["EMBER_DAY", "ROGATION_DAY"]:
                    return self.FAST_PARTIAL

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

        required = self.required
        if self.season.name != "Advent" and self.season.name != "Lent" and self.season.name != "Eastertide":
            if self.required[1].rank.name == "HOLY_DAY":
                alternate_sunday = self.required[1].copy()
                alternate_sunday.rank = CommemorationRank.objects.get(calendar=self.calendar, name="ALTERNATE_SUNDAY")
                self.required = required[:1] + [alternate_sunday]
            else:
                self.required = required[:1]
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

        # Don't append a Feria to a Principal Feast or Privileged Observance
        if len(self.required) > 0 and self.required[0].rank.precedence_rank <= 2:
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
            self.dates[name] = CalendarDate(single_date, calendar=self.calendar)

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
        if not self.seasons:
            self._get_seasons()
        if len(calendar_date.required) > 0 and calendar_date.required[0].name == "The Day of Pentecost":
            calendar_date.season = self.season_tracker
        if len(calendar_date.required) > 0 and calendar_date.required[0].name in self.seasons.keys():
            self.season_tracker = self.seasons[calendar_date.required[0].name]
        if not calendar_date.required or calendar_date.required[0].name != "The Day of Pentecost":
            calendar_date.season = self.season_tracker

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

    def get_date(self, date_string):
        date = to_date(date_string)
        try:
            date = self.dates[date.strftime("%Y-%m-%d")]
            date.year = self
            return date
        except IndexError:
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

        for calendar_date in self.dates:
            pass
            # print(
            #     "{} {} - {} {}".format(
            #         calendar_date.season,
            #         calendar_date.date.strftime("%a, %b, %d, %Y"),
            #         calendar_date.primary.__repr__(),
            #         "+" if calendar_date.day_of_special_commemoration else "",
            #     )
            # )


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
                    self.check_previous_evening()
            except StopIteration:
                break

    def check_previous_evening(self):
        return False
        # current = self.i.get_current_index()
        # if not current.primary.rank.required:
        #     return
        # previous = self.i.get_previous()
        # if not previous:
        #     return
        # if previous.primary.rank.required:
        #     return
        #
        # if current.primary.eve_collect:
        #     previous.primary.evening_prayer_collect = current.primary.eve_collect
        #     return
        #
        # previous.primary.evening_prayer_collect = current.primary.evening_prayer_collect

    def own_collect(self, commemoration, calendar_date):

        if "FERIA" in commemoration.rank.name:
            return False

        if commemoration.collect:
            commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = commemoration.collect
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
                        commemoration.morning_prayer_collect = previous.primary.morning_prayer_collect
                        commemoration.evening_prayer_collect = previous.primary.evening_prayer_collect
                        commemoration.name = "{} after {}".format(
                            week_days[calendar_date.date.weekday()], previous.primary.name
                        )

                    break
        return False

    def saint_collect(self, commemoration, calendar_date):
        pass

    def fallback_collect(self, commemoration, calendar_date):
        commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = None

    def has_collect_for_feria(self, calendar_date):
        epiphany = self.is_epiphany(calendar_date)
        if epiphany:
            return epiphany
        christmas = self.is_christmas(calendar_date)
        if christmas:
            return christmas
        ash_wednesday = self.is_ash_wednesday(calendar_date)
        if ash_wednesday:
            return ash_wednesday
        sunday = self.is_sunday(calendar_date)
        if sunday:
            return sunday

        return False

    @staticmethod
    def is_epiphany(calendar_date):
        if "The Epiphany" in calendar_date.primary.name and calendar_date.primary.rank.required:
            return calendar_date.primary
        return None

    @staticmethod
    def is_christmas(calendar_date):
        if "Christmas Day" in calendar_date.primary.name and calendar_date.primary.rank.required:
            return calendar_date.primary
        return None

    @staticmethod
    def is_ash_wednesday(calendar_date):
        if "Ash Wednesday" in calendar_date.primary.name and calendar_date.primary.rank.required:
            return calendar_date.primary
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
    year = date.year if date > advent_start else date.year - 1
    year = ChurchYear(year)
    return year.get_date(date_string)

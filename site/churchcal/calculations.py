from datetime import datetime, timedelta, date

from dateutil.parser import parse
from django.core.cache import cache
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from indexed import IndexedOrderedDict

from churchcal.models import Commemoration, FerialCommemoration, Proper, Season, Calendar, CommemorationRank
from website import settings
from .utils import advent, week_days, easter


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
        sunday_date = self.date
        if sunday_date.weekday() != 6:
            sun_offset = (sunday_date.weekday() - 6) % 7
            sunday_date = sunday_date - timedelta(days=sun_offset)
        date = datetime.strptime("2019-{}-{}".format(sunday_date.month, sunday_date.day), "%Y-%m-%d").date()
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
    def morning_and_evening(self):
        start = self.all
        for commemoration in self.all_evening:
            if commemoration not in start:
                start.append(commemoration)
        return start

    @property
    def primary_evening(self):
        return self.all_evening[0]

    @cached_property
    def proper(self):
        if self.season.name != "Season After Pentecost" and self.primary.name not in [
            "The Day of Pentecost",
            "Trinity Sunday",
        ]:
            return None

        return self._find_proper()

    @cached_property
    def office_year(self):
        return 1 if self.year.start_year % 2 == 0 else 2

    @cached_property
    def mass_readings(self):
        if self.proper and self.primary.rank.name in ["SUNDAY"]:
            return self.proper.get_mass_readings_for_year(self.year.mass_year)
        return self.primary.get_mass_readings_for_year(self.year.mass_year)

    @cached_property
    def get_all_mass_readings(self):
        readings = []
        for commemoration in self.all:
            if self.proper and commemoration.rank.name == "SUNDAY":
                readings.append(self.proper.get_mass_readings_for_year(self.year.mass_year))
            else:
                readings.append(commemoration.get_mass_readings_for_year(self.year.mass_year))
        return readings

    @cached_property
    def evening_mass_readings(self):
        if self.proper:
            return self.proper.get_mass_readings_for_year(self.year.mass_year)
        return self.primary_evening.get_mass_readings_for_year(self.year.mass_year, time="evening")

    FAST_UNKNOWN = -1
    FAST_NONE = 0
    FAST_PARTIAL = 1
    FAST_FULL = 2
    FAST_DAYS_RANKS = {FAST_NONE: "", FAST_PARTIAL: "Fast (Partial abstinence)", FAST_FULL: "Fast (Total abstinence)"}
    FAST_DAY_LABELS = {FAST_NONE: "NONE", FAST_PARTIAL: "FAST_PARTIAL", FAST_FULL: "FAST_TOTAL_ABSTIENCE"}

    @cached_property
    def fast_day_reasons(self):
        reasons = []

        if self.primary.name in ["Ash Wednesday", "Good Friday"]:
            reasons.append(self.primary.name)

        if len(self.required) == 0 or self.primary.rank.name != "PRINCIPAL_FEAST":
            for optional in self.optional:
                if optional.rank.name in ["EMBER_DAY", "ROGATION_DAY"]:
                    reasons.append(optional.rank.formatted_name)

        # All of lent is a fast day
        if self.season.name == "Lent" or self.season.name == "Holy Week":
            reasons.append("Lent")

        # Fridays
        if self.season.name not in ["Christmastide", "Eastertide"] and self.date.weekday() == 4:
            reasons.append("Friday")

        return reasons

    @cached_property
    def fast_day(self):
        # Sundays are never fast days
        if self.date.weekday() == 6:
            return self.FAST_NONE

        if self.primary.name in ["Ash Wednesday", "Good Friday"]:
            return self.FAST_FULL

        if len(self.required) == 0 or self.primary.rank.name != "PRINCIPAL_FEAST":
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
            if self.required[1].rank.precedence_rank < 4:
                alternate_sunday = self.required[1].copy()
                if alternate_sunday.rank.name != "SUNDAY":
                    alternate_sunday.rank = CommemorationRank.objects.get(
                        calendar=self.calendar, name="ALTERNATE_SUNDAY"
                    )
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

    #
    # # in case we want to cache by day instead of year
    # def build_from_cache(self):
    #     for name, date in self.dates.items():
    #         self.dates[name] = cache.get(name)
    #         if not self.dates[name]:
    #             return self.build_from_scratch()

    def build_from_scratch(self):
        self.seasons = self._get_seasons()
        self.season_tracker = None
        # create each date
        for name, date in self.dates.items():
            single_date = datetime.strptime(name, "%Y-%m-%d").date()
            self.dates[name] = CalendarDate(single_date, calendar=self.calendar, year=self)

        # add commemorations to date
        commemorations = (
            Commemoration.objects.select_related(
                "rank",
                "cannot_occur_after__rank",
            )
            .filter(calendar=self.calendar)
            .all()
        )
        already_added = []
        for commemoration in commemorations:
            if not commemoration.can_occur_in_year(self.start_year):
                continue
            try:
                if type(commemoration.initial_date_string(self.start_year)) == list:
                    self.dates[commemoration.initial_date_string(self.start_year)[0]].add_commemoration(commemoration)
                    self.dates[commemoration.initial_date_string(self.start_year)[1]].add_commemoration(commemoration)
                else:
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

    def __init__(self, year_of_advent, calendar="ACNA_BCP2019"):
        self.calendar = Calendar.objects.filter(abbreviation=calendar).first()

        self.start_year = year_of_advent
        self.end_year = year_of_advent + 1

        self.dates = IndexedOrderedDict()

        start_date = advent(year_of_advent)
        end_date = advent(year_of_advent + 1) - timedelta(days=1)

        self.start_date = start_date
        self.end_date = end_date

        self.seasons = self._get_seasons()
        self.season_tracker = None
        # create each date
        for single_date in self.daterange(start_date, end_date):
            name = single_date.strftime("%Y-%m-%d")
            self.dates[name] = None
        return self.build_from_scratch()

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
    def __iter__(self):
        return ChurchYearIterator(self)

    def __init__(self, year, first_year, second_year):
        year = int(year)
        dates = IndexedOrderedDict(**first_year.dates, **second_year.dates)
        dates = {k: v for (k, v) in dates.items() if int(k.split("-")[0]) == year}
        dates = IndexedOrderedDict(**dates)
        self.dates = dates

        del dates
        del first_year
        del second_year


class SetNamesAndCollects(object):
    def __init__(self, church_calendar):
        self.church_calendar = church_calendar

        checks = [
            self.own_collect,
            self.proper_collect,
            self.feria_collect,
            self.saint_collect,
            self.fallback_collect,
        ]

        self.i = iter(self.church_calendar)
        while True:
            try:
                calendar_date = next(self.i)

                for commemoration in calendar_date.all:
                    if "SUNDAY" in commemoration.rank.name:
                        self.append_seuptuagesima_if_needed(commemoration, calendar_date)

            except StopIteration:
                break

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

        self.i = iter(self.church_calendar)
        while True:
            try:
                calendar_date = next(self.i)

                for commemoration in calendar_date.all:
                    if "SUNDAY" in commemoration.rank.name:
                        self.append_o_antiphon_if_needed(commemoration, calendar_date)

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

        # if previous.primary.rank.required and previous.primary.rank.name != "PRIVILEGED_OBSERVANCE":
        #     return

        previous.evening_required = previous.required.copy()
        previous.evening_optional = previous.optional.copy()
        feast_copy = calendar_date.primary.copy()

        if feast_copy.collect_eve:
            feast_copy.evening_prayer_collect = feast_copy.collect_eve

        previous_names = [feast.name for feast in previous.all]
        if feast_copy.name not in previous_names:
            feast_copy.name = "Eve of {}".format(feast_copy.name)
            previous.evening_required.append(feast_copy)
        previous.proper = calendar_date.proper

        for idx, commemoration in enumerate(previous.evening_required):
            if "PRIVILEGED_OBSERVANCE" in commemoration.rank.name:
                previous.evening_required.pop(idx)

        if feast_copy.rank.name == "SUNDAY":
            for idx, commemoration in enumerate(previous.evening_optional):
                if "FERIA" in commemoration.rank.name:
                    previous.evening_optional.pop(idx)

        previous.evening_season = calendar_date.season

    def own_collect(self, commemoration, calendar_date):
        if "FERIA" in commemoration.rank.name:
            return False

        if commemoration.collect_1:
            commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = commemoration.collect_1
            if commemoration.collect_2:
                commemoration.evening_prayer_collect = commemoration.collect_2
            # commemoration.morning_prayer_collect = (
            #     commemoration.evening_prayer_collect
            # ) = commemoration.collect.replace(" [this day]", " this day")
            # if commemoration.alternate_collect:
            #     commemoration.evening_prayer_collect = commemoration.alternate_collect

    def proper_collect(self, commemoration, calendar_date):
        if not commemoration.rank.required:
            return
        if calendar_date.proper and calendar_date.proper.collect_1:
            commemoration.proper = calendar_date.proper
            commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = (
                calendar_date.proper.collect_1
            )
            if commemoration.rank.name == "SUNDAY" or commemoration.name in ["The Day of Pentecost", "Trinity Sunday"]:
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
                    target_commemoration = self.has_collect_for_feria(previous)
                    commemoration.collect_1 = target_commemoration.collect_1
                    commemoration.collect_2 = target_commemoration.collect_2
                    commemoration.collect_eve = target_commemoration.collect_eve
                    if previous.proper and previous.proper.collect_1:
                        calendar_date.proper = previous.proper
                        commemoration.morning_prayer_collect = previous.proper.collect_1
                        commemoration.evening_prayer_collect = previous.proper.collect_1
                        name = target_commemoration.name

                        if name[:3] == "The":
                            name = name.replace("The ", "the ")
                        if previous.primary.rank.name == "PRINCIPAL_FEAST":
                            commemoration.name = "{} after {}".format(week_days[calendar_date.date.weekday()], name)
                        else:
                            commemoration.name = "{} after {}".format(week_days[calendar_date.date.weekday()], name)
                        commemoration.original_proper = previous.proper
                    else:
                        commemoration.morning_prayer_collect = previous.primary.morning_prayer_collect
                        commemoration.evening_prayer_collect = previous.primary.evening_prayer_collect
                        commemoration.name = "{} after {}".format(
                            week_days[calendar_date.date.weekday()], previous.primary.name.replace("The ", "the ")
                        )
                        commemoration.original_commemoration = previous.primary
                    self.append_seuptuagesima_if_needed(commemoration, calendar_date)
                    self.append_o_antiphon_if_needed(commemoration, calendar_date)
                    if "gesima" in commemoration.name:
                        commemoration.alternate_color_2 = "purple" if commemoration.alternate_color else None
                        commemoration.alternate_color = (
                            commemoration.alternate_color if commemoration.alternate_color else "purple"
                        )
                    break

        return False

    def append_seuptuagesima_if_needed(self, commemoration, calendar_date):
        easter_day = easter(calendar_date.date.year)
        seventy_days_before_easter = easter_day - timedelta(days=9 * 7)
        date = calendar_date.date
        if seventy_days_before_easter == date:
            commemoration.name = "{}, or Septuagesima".format(commemoration.name)
            commemoration.alternate_color_2 = "purple" if commemoration.alternate_color else None
            commemoration.alternate_color = (
                commemoration.alternate_color if commemoration.alternate_color else "purple"
            )

    def append_o_antiphon_if_needed(self, commemoration, calendar_date):
        if calendar_date.date.month == 12:
            if calendar_date.date.day == 16:
                commemoration.name = mark_safe(
                    "{} <em>(O Sapientia / O Wisdom from on high)</em>".format(commemoration.name)
                )

            if calendar_date.date.day == 17:
                commemoration.name = mark_safe("{} <em>(O Adonai / O Lord of Might)</em>".format(commemoration.name))

            if calendar_date.date.day == 18:
                commemoration.name = mark_safe(
                    "{} <em>(O Radix Jesse / O Root of Jesse)</em>".format(commemoration.name)
                )

            if calendar_date.date.day == 19:
                commemoration.name = mark_safe(
                    "{} <em>(O Clavis David / O Key of David)</em>".format(commemoration.name)
                )

            if calendar_date.date.day == 20:
                commemoration.name = mark_safe("{} <em>(O Oriens / O Daypsring)</em>".format(commemoration.name))

            if calendar_date.date.day == 21:
                commemoration.name = mark_safe(
                    "{} <em>(O Rex Gentium / O Desire of Nations)</em>".format(commemoration.name)
                )

            if calendar_date.date.day == 22:
                commemoration.name = mark_safe(
                    "{} <em>(O Emmanuel / O Come, Emmanuel)</em>".format(commemoration.name)
                )

            if calendar_date.date.day == 23:
                commemoration.name = mark_safe(
                    "{} <em>(O Virgo Virginum / O Virgin of Virgins)</em>".format(commemoration.name)
                )

    def saint_collect(self, commemoration, calendar_date):
        if not hasattr(commemoration, "saint_type") or not commemoration.saint_type:
            return False

        commemoration.morning_prayer_collect = commemoration.evening_prayer_collect = commemoration.common_collect()

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
        pentecost = SetNamesAndCollects.is_pentecost_or_trinity(calendar_date)
        if pentecost:
            return pentecost
        sunday = SetNamesAndCollects.is_sunday(calendar_date)
        if sunday:
            return sunday

        return False

    @staticmethod
    def is_epiphany(calendar_date):
        if (
            calendar_date.required
            and "The Epiphany" in calendar_date.required[0].name
            and calendar_date.required[0].rank.required
        ):
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_christmas(calendar_date):
        if (
            calendar_date.required
            and "Christmas Day" in calendar_date.required[0].name
            and calendar_date.required[0].rank.required
        ):
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_ash_wednesday(calendar_date):
        if (
            calendar_date.required
            and "Ash Wednesday" in calendar_date.required[0].name
            and calendar_date.required[0].rank.required
        ):
            return calendar_date.required[0]
        return None

    @staticmethod
    def is_ascension(calendar_date):
        if (
            calendar_date.required
            and "Ascension Day" in calendar_date.required[0].name
            and calendar_date.required[0].rank.required
        ):
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

    @staticmethod
    def is_pentecost_or_trinity(calendar_date):
        if calendar_date.date.weekday() == 6:
            for commemoration in calendar_date.all:
                if commemoration.rank.name == "PRINCIPAL_FEAST" and commemoration.name in [
                    "The Day of Pentecost",
                    "Trinity Sunday",
                ]:
                    commemoration = commemoration.copy()
                    commemoration.name = f"{commemoration.name} (Proper {calendar_date.proper.number})"
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


def get_church_year(date_string):
    date = to_date(date_string)
    advent_start = advent(date.year)
    year = date.year if date >= advent_start else date.year - 1
    church_year = cache.get(str(year)) if settings.USE_CALENDAR_CACHE else None
    church_year = None
    if not church_year:
        church_year = ChurchYear(year)
        cache.set(str(year), church_year, 60 * 60 * 12)
    return church_year


def get_calendar_date(date_string):
    church_year = get_church_year(date_string)
    return church_year.get_date(date_string)

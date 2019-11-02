from builtins import NotImplementedError
from datetime import date, datetime, timedelta

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from model_utils.managers import InheritanceManager, InheritanceQuerySetMixin, InheritanceManagerMixin

from churchcal.base_models import BaseModel
from churchcal.utils import advent, easter, weekday_after

from churchcal.inheritence_query_set import _get_subclasses_recurse_without_managed, get_queryset_as_subclasses


class Denomination(BaseModel):

    name = models.CharField(max_length=256)
    abbreviation = models.CharField(max_length=256)


class Calendar(BaseModel):

    name = models.CharField(max_length=256)
    denomination = models.ForeignKey("Denomination", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.CharField(max_length=256)
    abbreviation = models.CharField(max_length=256)
    google_sheet_id = models.CharField(max_length=256)


class CommemorationRank(BaseModel):
    RANKS = [(level, level) for level in range(1, 10)]

    name = models.CharField(max_length=256)
    formatted_name = models.CharField(max_length=256)
    precedence_rank = models.PositiveSmallIntegerField(choices=RANKS)
    required = models.BooleanField(default=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)

    def get_collect(self, calendar_date=None):
        if self.collect:
            return self.collect

        if calendar_date and calendar_date.proper:
            return self.proper.collect

        return None

    def __repr__(self):
        return "{} ({}) ({})".format(self.name, self.rank.formatted_name, self.color)


class Commemoration(BaseModel):
    InheritanceQuerySetMixin._get_subclasses_recurse = _get_subclasses_recurse_without_managed
    InheritanceManagerMixin.get_queryset = get_queryset_as_subclasses
    objects = InheritanceManager()

    name = models.CharField(max_length=256)
    rank = models.ForeignKey("CommemorationRank", on_delete=models.SET_NULL, null=True, blank=True)
    cannot_occur_after = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=256, null=True, blank=True)
    additional_color = models.CharField(max_length=256, null=True, blank=True)
    alternate_color = models.CharField(max_length=256, null=True, blank=True)
    alternate_color_2 = models.CharField(max_length=256, null=True, blank=True)
    collect = models.TextField(blank=True, null=True)
    alternate_collect = models.TextField(blank=True, null=True)
    eve_collect = models.TextField(blank=True, null=True)
    color_notes = models.CharField(max_length=256, null=True, blank=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)
    link_1 = models.URLField(null=True, blank=True)
    link_2 = models.URLField(null=True, blank=True)
    link_3 = models.URLField(null=True, blank=True)

    def _year_from_advent_year(self, year, month, day):

        advent_date = advent(year)

        if month > advent_date.month or (month == advent_date.month and day >= advent_date.day):
            return year
        else:
            return year + 1

    def initial_date(self, advent_year):

        raise NotImplementedError()

    @cached_property
    def cannot_occur_after_subtype(self):
        if not self.cannot_occur_after:
            return None
        return Commemoration.objects.get(pk=self.cannot_occur_after.pk)

    def initial_date_string(self, advent_year):

        return self.initial_date(advent_year).strftime("%Y-%m-%d")

    def can_occur_in_year(self, advent_year):
        if not self.cannot_occur_after:
            return True

        if self.initial_date(advent_year=advent_year) >= self.cannot_occur_after_subtype.initial_date(
            advent_year=advent_year
        ):
            return False

        return True

    def __repr__(self):
        return "{} ({}) ({})".format(self.name, self.rank.formatted_name, self.color)


class SanctoraleCommemoration(Commemoration):
    month = models.PositiveSmallIntegerField()
    day = models.PositiveSmallIntegerField()
    saint_name = models.CharField(max_length=256, null=True, blank=True)
    saint_type = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        choices=(
            ("PASTOR", "OF A PASTOR"),
            ("MONASTIC", "OF A MONASTIC OR RELIGIOUS"),
            ("MARTYR", "OF A MARTYR"),
            ("MISSIONARY", "OF A MISSIONARY OR EVANGELIST"),
            ("TEACHER", "OF A TEACHER OF THE FAITH"),
            ("RENEWER", "OF A RENEWER OF SOCIETY"),
            ("REFORMER", "OF A REFORMER OF THE CHURCH"),
            ("SAINT_1", "OF ANY COMMEMORATION 1"),
            ("SAINT_2", "OF ANY COMMEMORATION 2"),
            ("ECUMENIST", "OF AN ECUMENIST"),
        ),
    )

    saint_gender = models.CharField(
        max_length=1, null=True, blank=True, choices=(("M", "Male"), ("F", "Female"), ("P", "Plural"))
    )
    saint_fill_in_the_blank = models.CharField(max_length=256, null=True, blank=True)

    def initial_date(self, advent_year):
        year = self._year_from_advent_year(advent_year, self.month, self.day)

        return date(year, self.month, self.day)


class SanctoraleBasedCommemoration(Commemoration):
    weekday = models.CharField(max_length=256)
    number_after = models.SmallIntegerField()
    month_after = models.PositiveSmallIntegerField()
    day_after = models.PositiveSmallIntegerField()

    def initial_date(self, advent_year):
        early_year = weekday_after(
            weekday=self.weekday,
            month=self.month_after,
            day=self.day_after,
            year=advent_year,
            number_after=self.number_after,
        )

        advent_start = advent(advent_year)

        if early_year >= advent_start:
            return early_year

        return weekday_after(
            weekday=self.weekday,
            month=self.month_after,
            day=self.day_after,
            year=advent_year + 1,
            number_after=self.number_after,
        )


class TemporaleCommemoration(Commemoration):
    days_after_easter = models.SmallIntegerField()

    def initial_date(self, advent_year):
        year = advent_year + 1
        easter_date = easter(year)
        return easter_date + timedelta(days=self.days_after_easter)


class FerialCommemoration(Commemoration):
    class Meta:
        managed = False

    def __init__(self, date, season, calendar, *args, **kwargs):
        super(FerialCommemoration, self).__init__(*args, **kwargs)
        self.date = date
        self.name = season.rank.formatted_name
        self.rank = season.rank
        self.color = season.color
        self.alternate_color = season.alternate_color

    def initial_date(self, advent_year):
        return self.date


class Proper(BaseModel):

    number = models.IntegerField(choices=zip(range(1, 29), range(1, 29)), blank=False, null=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    collect = models.TextField(blank=True, null=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)
    collect = models.TextField(blank=True, null=True)

    def __repr__(self):
        return str(self.number)


class Season(BaseModel):

    order = models.IntegerField(choices=zip(range(1, 29), range(1, 29)), blank=False, null=False)
    name = models.CharField(max_length=1024)
    start_commemoration = models.ForeignKey("Commemoration", on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=255)
    alternate_color = models.CharField(max_length=255, null=True, blank=True)
    rank = models.ForeignKey(CommemorationRank, on_delete=models.CASCADE, null=False, blank=False)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)

    def __repr__(self):
        return self.name

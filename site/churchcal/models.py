from builtins import NotImplementedError
from datetime import date, timedelta

from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.utils.functional import cached_property
from django_ckeditor_5.fields import CKEditor5Field
from model_utils.managers import InheritanceManager, InheritanceQuerySetMixin, InheritanceManagerMixin

from churchcal.base_models import BaseModel
from churchcal.inheritence_query_set import _get_subclasses_recurse_without_managed, get_queryset_as_subclasses
from churchcal.utils import advent, easter, weekday_after


class Denomination(BaseModel):
    name = models.CharField(max_length=256)
    abbreviation = models.CharField(max_length=256)


class Calendar(BaseModel):
    name = models.CharField(max_length=256)
    denomination = models.ForeignKey("Denomination", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.CharField(max_length=256)
    abbreviation = models.CharField(max_length=256)
    google_sheet_id = models.CharField(max_length=256)

    def __str__(self):
        return "{} ({})".format(self.denomination.name, self.name)


class CommemorationRank(BaseModel):
    RANKS = [(level, level) for level in range(1, 10)]

    name = models.CharField(max_length=256)
    formatted_name = models.CharField(max_length=256)
    precedence_rank = models.PositiveSmallIntegerField(choices=RANKS)
    required = models.BooleanField(default=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return self.formatted_name


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
    collect_1 = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="commemoration_collect_1"
    )
    collect_2 = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="commemoration_collect_2"
    )
    collect_eve = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="commemoration_collect_eve"
    )
    color_notes = models.CharField(max_length=256, null=True, blank=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)
    link_1 = models.URLField(null=True, blank=True)
    link_2 = models.URLField(null=True, blank=True)
    link_3 = models.URLField(null=True, blank=True)
    biography = CKEditor5Field(blank=True, null=True)
    image_link = models.URLField(null=True, blank=True)

    ai_one_sentence = models.TextField(null=True, blank=True)
    ai_quote = models.TextField(null=True, blank=True)
    ai_quote_by = models.TextField(null=True, blank=True)
    ai_quote_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_verse = models.TextField(null=True, blank=True)
    ai_verse_citation = models.TextField(null=True, blank=True)
    ai_hagiography = models.TextField(null=True, blank=True)
    ai_hagiography_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_legend = models.TextField(null=True, blank=True)
    ai_legend_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_legend_title = models.TextField(null=True, blank=True)
    ai_bullet_points = models.TextField(null=True, blank=True)
    ai_bullet_points_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_traditions = models.TextField(null=True, blank=True)
    ai_traditions_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_foods = models.TextField(null=True, blank=True)
    ai_foods_citations = ArrayField(models.URLField(), null=True, blank=True)
    ai_image_1 = models.URLField(null=True, blank=True, max_length=1024)
    ai_image_2 = models.URLField(null=True, blank=True, max_length=1024)

    ai_lesser_feasts_and_fasts = models.TextField(null=True, blank=True)
    ai_martyrology = models.TextField(null=True, blank=True)
    ai_butler = models.TextField(null=True, blank=True)

    @property
    def name_no_tags(self):
        from office.management.commands.import_collects import do_strip_tags

        return do_strip_tags(self.name)

    def get_collects(self, calendar_date=None):
        if self.collect:
            return self.collect

        if calendar_date and calendar_date.proper:
            return self.proper.collect

        return None

    def _year_from_advent_year(self, year, month, day):
        advent_date = advent(year)
        advent_2_date = advent(year + 1)
        after_advent = month > advent_date.month or (month == advent_date.month and day >= advent_date.day)
        before_2_advent = month < advent_2_date.month or (month == advent_2_date.month and day < advent_2_date.day)

        if after_advent and before_2_advent:
            return [year, year + 1]
        elif after_advent:
            return year
        else:
            return year + 1

    def initial_date(self, advent_year, calendar_year=None):
        raise NotImplementedError()

    @cached_property
    def cannot_occur_after_subtype(self):
        if not self.cannot_occur_after:
            return None
        return Commemoration.objects.get(pk=self.cannot_occur_after.pk)

    def initial_date_string(self, advent_year):
        if type(self.initial_date(advent_year)) != date:
            return [
                self.initial_date(advent_year)[0].strftime("%Y-%m-%d"),
                self.initial_date(advent_year)[1].strftime("%Y-%m-%d"),
            ]
        return self.initial_date(advent_year).strftime("%Y-%m-%d")

    def can_occur_in_year(self, advent_year):
        if not self.cannot_occur_after:
            return True

        if self.initial_date(advent_year=advent_year) >= self.cannot_occur_after_subtype.initial_date(
            advent_year=advent_year
        ):
            return False

        return True

    def get_mass_readings_for_year(self, year, time="morning"):
        commemoration = (
            self.original_commemoration
            if hasattr(self, "original_commemoration") and self.original_commemoration
            else self
        )
        proper = (
            self.original_proper
            if hasattr(self, "original_proper") and self.original_proper
            else self.proper if hasattr(self, "proper") and self.proper else None
        )
        if proper:
            query = MassReading.objects.filter(years__contains=year, proper=proper).order_by("reading_number")
        else:
            query = MassReading.objects.filter(years__contains=year, commemoration=commemoration).order_by(
                "reading_number"
            )

        if year in ["A", "C"] and time == "morning":
            query = query.order_by("reading_number", "-order")
        else:
            query = query.order_by("reading_number", "order")

        if self.name == "Eve of Easter Day":
            query = query.filter(abbreviation="EasterEve")

        if self.name == "Easter Day":
            if time == "morning":
                query = query.filter(service="Principal Service")
            else:
                query = query.filter(service="Evening Service")

        if self.name == "Eve of The Nativity of our Lord Jesus Christ: Christmas Day":
            query = query.filter(service="I")

        if self.name == "The Nativity of Our Lord Jesus Christ: Christmas Day":
            if time == "morning":
                query = query.filter(service="II")
            else:
                query = query.fitler(service="III")

        if self.name in ["Eve of Palm Sunday", "Palm Sunday"]:
            query = query.filter(service="Liturgy of the Word")

        return query.all()

    def get_all_mass_readings_for_year(self, year):
        commemoration = (
            self.original_commemoration
            if hasattr(self, "original_commemoration") and self.original_commemoration
            else self
        )
        proper = (
            self.original_proper
            if hasattr(self, "original_proper") and self.original_proper
            else self.proper if hasattr(self, "proper") and self.proper else None
        )
        if hasattr(commemoration, "saint_type") and commemoration.saint_type:
            query = MassReading.objects.filter(common__abbreviation=commemoration.saint_type).order_by(
                "reading_number"
            )
        elif proper:
            query = MassReading.objects.filter(years__contains=year, proper=proper).order_by("reading_number")
        else:
            query = MassReading.objects.filter(years__contains=year, commemoration__uuid=commemoration.uuid).order_by(
                "reading_number"
            )
            if "Eve of" in commemoration.name:
                query = query.exclude(
                    service__in=["II", "III", "Early Service", "Principal Service", "Evening Service"]
                )

        query = query.order_by("abbreviation", "reading_number", "order", "service")
        query = query.select_related("long_scripture", "short_scripture")
        return query.all()

    def __repr__(self):
        return "{} ({}) ({})".format(self.name, self.rank.formatted_name, self.color)

    def __str__(self):
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
    common = models.ForeignKey("churchcal.Common", blank=True, null=True, on_delete=models.SET_NULL)

    def initial_date(self, advent_year, calendar_year=None):
        year = self._year_from_advent_year(advent_year, self.month, self.day)
        if type(year) == list:
            return [date(year[0], self.month, self.day), date(year[1], self.month, self.day)]

        return date(year, self.month, self.day)

    def get_mass_readings_for_year(self, year, time="morning"):
        readings = super().get_mass_readings_for_year(year, time)
        commemoration = (
            self.original_commemoration
            if hasattr(self, "original_commemoration") and self.original_commemoration
            else self
        )
        if not readings and commemoration.saint_type:
            readings = MassReading.objects.filter(common__abbreviation=commemoration.saint_type).all()
        return readings

    def build_collect(self, text):
        if not self.common:
            return None

        plural = "s" if self.saint_gender not in ["M", "F"] else ""
        if self.saint_type in ["MONASTIC", "MARTYR"]:
            return text.format(plural, self.saint_name)

        if self.saint_type in ["MISSIONARY", "PASTOR"]:
            a = "" if not plural else "s"
            return text.format(plural, self.saint_name, a, self.saint_fill_in_the_blank, plural).replace(" :", ":")

        if self.saint_type == "RENEWER":
            pronoun = "his" if self.saint_gender == "M" else "her" if self.saint_gender == "F" else "their"
            return text.format(plural, self.saint_name, pronoun, pronoun)

        if self.saint_type == "REFORMER":
            return text.format(plural, self.saint_name, "a" if not plural else "", "s" if plural else "")

        if self.saint_type == "ECUMENIST":
            pronoun = "his" if self.saint_gender == "M" else "her" if self.saint_gender == "F" else "their"
            return text.format(self.saint_name, pronoun)

        if self.saint_type in ["SAINT_1", "TEACHER"]:
            pronoun = "him" if self.saint_gender == "M" else "her" if self.saint_gender == "F" else "them"
            return text.format(plural, self.saint_name, pronoun)

        return text

    def common_collect(self):
        from office.models import AbstractCollect

        text = self.common.collect_format_string
        text_tle = self.common.collect_tle_format_string
        return AbstractCollect(text=self.build_collect(text), traditional_text=self.build_collect(text_tle))


class SanctoraleBasedCommemoration(Commemoration):
    weekday = models.CharField(max_length=256)
    number_after = models.SmallIntegerField()
    month_after = models.PositiveSmallIntegerField()
    day_after = models.PositiveSmallIntegerField()
    additional_days_after = models.PositiveSmallIntegerField(default=0)

    def can_occur_in_year(self, advent_year):
        result = super().can_occur_in_year(advent_year)
        if not result:
            return False

        all_saints_is_sunday = self.initial_date(advent_year).month == 11 and self.initial_date(advent_year).day == 1
        if all_saints_is_sunday:
            return False
        return True

    def initial_date(self, advent_year, calendar_year=None):
        early_year = weekday_after(
            weekday=self.weekday,
            month=self.month_after,
            day=self.day_after,
            year=advent_year,
            number_after=self.number_after,
        )

        advent_start = advent(advent_year)

        if early_year >= advent_start:
            if self.additional_days_after:
                early_year += timedelta(days=self.additional_days_after)
            return early_year

        return_date = weekday_after(
            weekday=self.weekday,
            month=self.month_after,
            day=self.day_after,
            year=advent_year + 1,
            number_after=self.number_after,
        )

        if self.additional_days_after:
            return_date += timedelta(days=self.additional_days_after)

        return return_date


class TemporaleCommemoration(Commemoration):
    days_after_easter = models.SmallIntegerField()

    def initial_date(self, advent_year, calendar_year=None):
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

    def initial_date(self, advent_year, calendar_year=None):
        return self.date


class Proper(BaseModel):
    number = models.IntegerField(choices=zip(range(1, 29), range(1, 29)), blank=False, null=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    collect_1 = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="proper_collect_1"
    )
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)

    def get_mass_readings_for_year(self, year):
        return MassReading.objects.filter(years__contains=year, proper=self).order_by("reading_number", "order").all()

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


class MassReading(BaseModel):
    long_citation = models.CharField(max_length=256)
    long_text = models.TextField(blank=True, null=True)
    service = models.CharField(max_length=256)
    short_citation = models.CharField(max_length=256)
    short_text = models.TextField(blank=True, null=True)
    years = models.CharField(max_length=3)
    commemoration = models.ForeignKey("Commemoration", on_delete=models.SET_NULL, null=True, blank=True)
    proper = models.ForeignKey("Proper", on_delete=models.SET_NULL, null=True, blank=True)
    common = models.ForeignKey("Common", on_delete=models.SET_NULL, null=True, blank=True)
    reading_type = models.CharField(
        max_length=256,
        choices=(("prophecy", "prophecy"), ("psalm", "psalm"), ("epistle", "epistle"), ("gospel", "gospel")),
    )
    book = models.CharField(max_length=256)
    testament = models.CharField(max_length=4)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)
    abbreviation = models.CharField(max_length=256, blank=True, null=True)
    reading_number = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField()
    long_scripture = models.ForeignKey(
        "office.Scripture", on_delete=models.SET_NULL, null=True, blank=True, related_name="long_scripture"
    )
    short_scripture = models.ForeignKey(
        "office.Scripture", on_delete=models.SET_NULL, null=True, blank=True, related_name="short_scripture"
    )

    def __repr__(self):
        return self.long_citation


class Common(BaseModel):
    abbreviation = models.CharField(max_length=256)
    name = models.CharField(max_length=256)
    collect_1 = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="common_collect_1"
    )
    collect_2 = models.ForeignKey(
        "office.Collect", on_delete=models.SET_NULL, null=True, blank=True, related_name="common_collect_2"
    )
    collect_format_string = models.CharField(max_length=1024, blank=True, null=True)
    collect_tle_format_string = models.CharField(max_length=1024, blank=True, null=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=False, blank=False)

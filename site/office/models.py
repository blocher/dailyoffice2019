import re

from ckeditor.fields import RichTextField
from django.db import models

from churchcal.base_models import BaseModel
from churchcal.models import Commemoration


class OfficeDay(BaseModel):
    TESTAMENTS = (("OT", "Old Testament"), ("DC", "Deuterocanon"), ("AP", "Apocrypha"), ("NT", "New Testament"))

    holy_day_name = models.CharField(max_length=255, null=True, blank=True)
    mp_psalms = models.CharField(max_length=255)
    mp_reading_1 = models.CharField(max_length=255)
    mp_reading_1_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    mp_reading_1_text = models.TextField(blank=True, null=True)
    mp_reading_1_abbreviated = models.CharField(max_length=255, null=True, blank=True)
    mp_reading_1_abbreviated_text = models.TextField(blank=True, null=True)
    mp_reading_2 = models.CharField(max_length=255)
    mp_reading_2_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    mp_reading_2_text = models.TextField(blank=True, null=True)
    ep_psalms = models.CharField(max_length=255)
    ep_reading_1 = models.CharField(max_length=255)
    ep_reading_1_text = models.TextField(blank=True, null=True)
    ep_reading_1_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    ep_reading_1_abbreviated = models.CharField(max_length=255, null=True, blank=True)
    ep_reading_1_abbreviated_text = models.TextField(blank=True, null=True)
    ep_reading_2 = models.CharField(max_length=255)
    ep_reading_2_testament = models.CharField(max_length=2, choices=TESTAMENTS)
    ep_reading_2_text = models.TextField(blank=True, null=True)

    def __getattribute__(self, attrname):
        value = super().__getattribute__(attrname)
        try:
            return value.replace("<h3>", "<h3 class='reading-heading off'>")
        except (AttributeError, TypeError):
            return value


class StandardOfficeDay(OfficeDay):
    month = models.IntegerField()
    day = models.IntegerField()


class HolyDayOfficeDay(OfficeDay):
    commemoration = models.ForeignKey(Commemoration, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)


class ThirtyDayPsalterDay(BaseModel):
    day = models.IntegerField()
    mp_psalms = models.CharField(max_length=255)
    ep_psalms = models.CharField(max_length=255)

    def psalm_string_to_list(self, psalms):
        return psalms.split(psalms)

    def get_mp_pslams(self):
        return self.psalm_string_to_list(self.mp_psalms)

    def get_ep_pslams(self):
        return self.psalm_string_to_list(self.ep_psalms)


class AboutItem(BaseModel):
    question = models.CharField(max_length=4000)
    answer = RichTextField()
    app_mode = models.BooleanField(default=True)
    web_mode = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    def save(self, *args, **kwargs):

        return super().save(*args, **kwargs)

    @property
    def question_for_web(self):
        if self.mode == "app":
            return None
        return self.question.replace("{medium}", "site")

    @property
    def answer_for_web(self):
        if self.mode == "app":
            return None
        return self.answer.replace("{medium}", "site")

    @property
    def question_for_app(self):
        if self.mode == "web":
            return None
        return self.question.replace("{medium}", "app")

    @property
    def answer_for_app(self):
        if self.mode == "web":
            return None
        return self.answer.replace("{medium}", "app")

    def mode(self):
        if self.web_mode and self.app_mode:
            return "both"
        if self.web_mode:
            return "web"
        return "app"

    def display_name(self):
        return "{} ({})".format(re.sub("<[^<]+?>", "", self.question), self.mode())

    def __str__(self):
        return self.display_name()

    class Meta(object):
        ordering = ["order"]


class UpdateNotice(BaseModel):
    notice = RichTextField()
    app_mode = models.BooleanField(default=True)
    web_mode = models.BooleanField(default=True)
    version = models.FloatField()

    def save(self, *args, **kwargs):

        return super().save(*args, **kwargs)

    def mode(self):
        if self.web_mode and self.app_mode:
            return "both"
        if self.web_mode:
            return "web"
        return "app"

    class Meta(object):
        ordering = ["-version"]


class Setting(BaseModel):
    MAIN_SETTINGS = 1
    ADDITIONAL_SETTINGS = 2
    EXPERT_SETTINGS = 3
    SETTING_TYPES = (
        (MAIN_SETTINGS, "Settings"),
        (ADDITIONAL_SETTINGS, "Additional Settings"),
        (EXPERT_SETTINGS, "Expert Settings"),
    )

    DAILY_OFFICE_SITE = 1
    FAMILY_PRAYER_SITE = 2
    SETTING_SITES = (
        (DAILY_OFFICE_SITE, "Daily Office"),
        (FAMILY_PRAYER_SITE, "Family Prayer"),
    )

    name = models.CharField(max_length=255)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    setting_type = models.PositiveSmallIntegerField(choices=SETTING_TYPES, null=False, default=MAIN_SETTINGS)
    site = models.PositiveSmallIntegerField(choices=SETTING_SITES, null=False, default=DAILY_OFFICE_SITE)


class SettingOption(BaseModel):
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    value = models.CharField(max_length=255)


class CollectType(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class CollectTagCategory(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class CollectTag(BaseModel):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    collect_tag_category = models.ForeignKey(CollectTagCategory, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)


class AbstractCollect(object):
    text = ""
    traditional_text = ""

    def __init__(self, text, traditional_text):
        self.text = text
        self.traditional_text = traditional_text


class Collect(BaseModel):
    COLLECT_TYPES = (
        ("year", "Collects of the Christian Year"),
        ("occasional", "Occasional Prayers"),
        ("office_prayers", "Collects from the Daily Office"),
        ("burial_rite", "Collects from the Burial Rite"),
        ("other", "Other Collects"),
    )

    title = models.CharField(max_length=255)
    text = RichTextField()
    traditional_text = RichTextField(blank=True, null=True)
    collect_type = models.ForeignKey(CollectType, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    number = models.PositiveSmallIntegerField(null=True, blank=True)
    tags = models.ManyToManyField(CollectTag)
    attribution = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

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
    question = RichTextField()
    answer = RichTextField()
    app_mode = models.BooleanField(default=True)
    web_mode = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()

    def save(self, *args, **kwargs):

        return super().save(*args, **kwargs)

    def mode(self):
        if self.web_mode and self.app_mode:
            return "both"
        if self.web_mode:
            return "web"
        return "app"

    def display_name(self):
        return "{} ({})".format(re.sub('<[^<]+?>', '', self.question), self.mode())

    def __str__(self):
        return self.display_name()

    class Meta(object):
        ordering = ['order']


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
        ordering = ['-version']


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
        except AttributeError:
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

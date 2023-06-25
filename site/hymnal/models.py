from django.db import models

from churchcal.base_models import BaseModel


class Hymn(BaseModel):
    hymnal = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=10, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    tune_name = models.CharField(max_length=255, null=True, blank=True)
    pdf = models.FileField(upload_to="hymnal/hymns/pdf", null=True, blank=True)
    mp3 = models.FileField(upload_to="hymnal/hymns/mp3", null=True, blank=True)
    lyrics = models.TextField(null=True, blank=True)
    copyright = models.TextField(null=True, blank=True)
    fair_use = models.BooleanField(default=False)
    rite_planning_id = models.CharField(max_length=255, null=True, blank=True)

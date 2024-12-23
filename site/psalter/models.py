import re

from django.db import models

# Create your models here.
from website.models import UUIDModel


class Psalm(UUIDModel):
    number = models.IntegerField(unique=True, blank=False, null=False)
    latin_title = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return f"Psalm {self.number}"


class PsalmVerse(UUIDModel):
    psalm = models.ForeignKey(Psalm, on_delete=models.CASCADE, blank=False, null=False)
    number = models.IntegerField(blank=False, null=False)
    first_half = models.CharField(max_length=1000, blank=False, null=False)
    second_half = models.CharField(max_length=1000, blank=False, null=False)
    first_half_tle = models.CharField(max_length=1000, blank=True, null=True)
    second_half_tle = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return f"Psalm {self.psalm.number}:{self.number}"

    class Meta:
        unique_together = ("psalm", "number")


class PsalmTopic(UUIDModel):
    topic_name = models.CharField(max_length=255)
    psalms = models.CharField(max_length=2000)
    order = models.PositiveSmallIntegerField()

    @property
    def psalm_list(self):
        psalms = re.sub(r"[^\\d,]+", "", self.psalms)
        return psalms.split(",")

    class Meta:
        ordering = ("order",)


class PsalmTopicPsalm(UUIDModel):
    psalm = models.ForeignKey(Psalm, on_delete=models.CASCADE, blank=False, null=False)
    psalm_topic = models.ForeignKey(PsalmTopic, on_delete=models.CASCADE, blank=False, null=False)
    order = models.PositiveSmallIntegerField()

    @property
    def psalm_list(self):
        psalms = re.sub(r"[^\\d,]+", "", self.psalms)
        return psalms.split(",")

    class Meta:
        ordering = ("order",)

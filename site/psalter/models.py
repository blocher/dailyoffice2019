from django.db import models

# Create your models here.
from website.models import UUIDModel


class Psalm(UUIDModel):

    number = models.IntegerField(unique=True, blank=False, null=False)
    latin_title = models.CharField(max_length=1000, blank=True, null=True)


class PsalmVerse(UUIDModel):

    psalm = models.ForeignKey(Psalm, on_delete=models.CASCADE, blank=False, null=False)
    number = models.IntegerField(blank=False, null=False)
    first_half = models.CharField(max_length=1000, blank=False, null=False)
    second_half = models.CharField(max_length=1000, blank=False, null=False)

    class Meta:
        unique_together = ("psalm", "number")

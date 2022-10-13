from address.models import AddressField
from array_tags.fields import TagField as ArrayField
from array_tags.managers import TagQuerySet as ArrayQuerySet
from django.db import models
from django.utils.functional import cached_property
from djrichtextfield.models import RichTextField

from bible import BibleVersions
from website.models import UUIDModel


class Sermon(UUIDModel):
    title = models.CharField(max_length=255, verbose_name="Sermon title", help_text="Sermon Title")
    location = models.ForeignKey("SermonLocation", null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(
        verbose_name="File", help_text="The sermon in Microsoft Word or text format", blank=True, null=True
    )
    text = models.TextField(verbose_name="Text", help_text="The full content of the sermon", blank=True, null=True)
    content = RichTextField(
        verbose_name="Formatted Content", help_text="The formatted content of the sermon", blank=True, null=True
    )
    summary = models.TextField(verbose_name="Summary", help_text="A summary of the sermon", blank=True, null=True)
    auto_summary = models.TextField(
        verbose_name="Auto-summary", help_text="An auto-generated summary of the sermon", blank=True, null=True
    )
    notes = models.TextField(verbose_name="Notes", help_text="Publicly displayed Notes", blank=True, null=True)
    private_notes = models.TextField(
        verbose_name="Notes (private)", help_text="Notes (Internal only)", blank=True, null=True
    )
    primary_date_and_time_given = models.DateTimeField(
        verbose_name="Date and Time Given",
        help_text="The primary date given (used for sorting).  More than one date and time can be added on the date and time tab",
        null=True,
        blank=True,
    )

    # tags = TaggableManager()

    def save(self, *args, **kwargs):
        self.auto_summary = self.getSummary()
        return super().save(*args, **kwargs)

    def __str__(self):
        return "{} - {} - {}".format(self.title, self.primary_date_and_time_given, self.location)


class SermonDateTime(UUIDModel):
    date_and_time_given = models.DateTimeField(verbose_name="Date Given", help_text="Date and Time Given", null=False)
    sermon = models.ForeignKey("Sermon", verbose_name="Sermon", on_delete=models.CASCADE, null=False)
    primary = models.BooleanField(
        verbose_name="Primary Service",
        help_text="Should this date be the primary date used for sorting?",
        default=False,
    )


class SermonBiblePassage(UUIDModel):
    UNKNOWN = 0
    PROPHECY = 1
    PSALM = 2
    EPISTLE = 3
    GOSPEL = 4
    OTHER = 5

    TYPE_CHOICES = {
        (PROPHECY, "PROPHECY (or other Old Testament)"),
        (PSALM, "PSALM"),
        (EPISTLE, "EPISTLE (or Acts / Revelation)"),
        (GOSPEL, "GOSPEL"),
        (OTHER, "OTHER"),
    }

    sermon = models.ForeignKey("Sermon", verbose_name="Sermon", on_delete=models.CASCADE, null=False)
    type = models.IntegerField(default=UNKNOWN, choices=TYPE_CHOICES, null=False, blank=False)
    passage = models.CharField(max_length=256, blank=False, null=False)
    text = models.TextField(blank=False, null=False)
    html = RichTextField(blank=False, null=False)
    version = models.CharField(
        choices=zip(BibleVersions.VERSIONS.keys(), BibleVersions.VERSIONS.keys()),
        blank=True,
        null=True,
        max_length=256,
    )


class SermonLocation(UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    address = AddressField(blank=True, null=True, default="", on_delete=models.SET_NULL)
    website = models.URLField(blank=True, null=True)
    alternate_names = ArrayField(
        blank=True, null=True, help_text="A list of strings to be matched when importing a sermon."
    )

    objects = ArrayQuerySet.as_manager()

    @cached_property
    def names(self):
        return [self.name] + self.alternate_names

    @cached_property
    def search_strings(self):
        return {name: self for name in self.names}

    def __str__(self):
        return "{} ({}, {})".format(self.name, self.address.locality.name, self.address.locality.state.code)

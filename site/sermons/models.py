from django.db import models
from website.models import UUIDModel


class Sermon(UUIDModel):
    title = models.CharField(max_length=255, verbose_name="Sermon title", help_text="Sermon Title")
    location = models.CharField(max_length=255, verbose_name="Location", help_text="Location Sermon was delivered")
    file = models.FileField(
        verbose_name="File", help_text="The sermon in Microsoft Word or text format", blank=True, null=True
    )
    text = models.TextField(verbose_name="Text", help_text="The full content of the sermon")
    summary = models.TextField(verbose_name="Summary", help_text="A summary of the sermon", blank=True, null=True)
    auto_summary = models.TextField(
        verbose_name="Auto-summary", help_text="An auto-generated summary of the sermon", blank=True, null=True
    )
    notes = models.TextField(verbose_name="Notes", help_text="Publicly displayed Notes", blank=True, null=True)
    private_notes = models.TextField(
        verbose_name="Notes (private)", help_text="Notes (Internal only)", blank=True, null=True
    )


class SermonDateTime(UUIDModel):

    date_and_time_give = models.DateTimeField(verbose_name="Date Given", help_text="Date and Time Given", null=False)
    sermon = models.ForeignKey("Sermon", verbose_name="Sermon", on_delete=models.CASCADE, null=False)

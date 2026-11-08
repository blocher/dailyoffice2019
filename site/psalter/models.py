import re

from django.db import models

# Create your models here.
from psalter.chant.tones import DEFAULT_TONE, TONE_CHOICES
from website.models import UUIDModel


class Psalm(UUIDModel):
    number = models.IntegerField(unique=True, blank=False, null=False)
    latin_title = models.CharField(max_length=1000, blank=True, null=True)
    chant_tone = models.CharField(
        max_length=10,
        blank=True,
        default="",
        choices=TONE_CHOICES,
        help_text=f"The plainsong tone this psalm is pointed for. Blank uses {DEFAULT_TONE}.",
    )

    def __str__(self):
        return f"Psalm {self.number}"


class PsalmVerse(UUIDModel):
    psalm = models.ForeignKey(Psalm, on_delete=models.CASCADE, blank=False, null=False)
    number = models.IntegerField(blank=False, null=False)
    first_half = models.CharField(max_length=1000, blank=False, null=False)
    second_half = models.CharField(max_length=1000, blank=False, null=False)
    first_half_tle = models.CharField(max_length=1000, blank=True, null=True)
    second_half_tle = models.CharField(max_length=1000, blank=True, null=True)
    first_half_spanish = models.CharField(max_length=1000, blank=True, null=True)
    second_half_spanish = models.CharField(max_length=1000, blank=True, null=True)
    first_half_chinese = models.CharField(max_length=1000, blank=True, null=True)
    second_half_chinese = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return f"Psalm {self.psalm.number}:{self.number}"

    class Meta:
        unique_together = ("psalm", "number")


class PsalmVersePointing(UUIDModel):
    """Syllables and stresses of a verse (contemporary text) for plainsong.

    The stress notation (see ``psalter.chant.notation``) is independent of the
    tone, so a psalm can be moved to another tone without pointing it again.
    """

    AGREED = "agreed"
    CHECK = "check"
    NEEDS_REVIEW = "needs_review"
    DICTIONARY = "dictionary"
    APPROVED = "approved"
    STATUS_CHOICES = [
        (NEEDS_REVIEW, "Needs review"),
        (CHECK, "Check: AI and dictionary differ"),
        (AGREED, "AI and dictionary agree"),
        (DICTIONARY, "Dictionary only (no AI)"),
        (APPROVED, "Approved"),
    ]

    verse = models.OneToOneField(PsalmVerse, on_delete=models.CASCADE, related_name="pointing")
    first_half_stress = models.CharField(
        max_length=1200,
        help_text="The first half-verse with / between syllables and + before each stressed syllable.",
    )
    second_half_stress = models.CharField(
        max_length=1200,
        help_text="The second half-verse with / between syllables and + before each stressed syllable.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NEEDS_REVIEW, db_index=True)
    confidence = models.FloatField(blank=True, null=True, help_text="The AI's own confidence, 0 to 1.")
    review_notes = models.TextField(blank=True, default="", help_text="Why this verse was flagged.")
    ai_model = models.CharField(max_length=100, blank=True, default="")
    ai_runs = models.JSONField(blank=True, default=list, help_text="Each AI answer, for comparison.")
    dictionary_first_half = models.CharField(max_length=1200, blank=True, default="")
    dictionary_second_half = models.CharField(max_length=1200, blank=True, default="")

    def __str__(self):
        return f"Pointing for {self.verse}"

    class Meta:
        ordering = ("verse__psalm__number", "verse__number")
        verbose_name = "psalm verse pointing"


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

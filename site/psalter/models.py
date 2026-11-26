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
    # A sung recording of the whole pointed psalm (manage.py record_chant), with
    # the pulse it was sung at and a key of what was sung; the API offers it only
    # while the key still matches the pointing, so the app's highlighting keeps
    # time with it.
    chant_recording = models.FileField(upload_to="chant/", blank=True, default="")
    chant_recording_pulse = models.FloatField(null=True, blank=True)
    chant_recording_key = models.CharField(max_length=40, blank=True, default="")
    chant_recording_voice = models.CharField(max_length=100, blank=True, default="")

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
    Pointing copied from the St. Bernard Psalter (``import_bernard_psalter``)
    carries the book's marks instead, and is sung to the book's tone for the
    verse's office (``tone``).
    """

    AGREED = "agreed"
    CHECK = "check"
    NEEDS_REVIEW = "needs_review"
    DICTIONARY = "dictionary"
    APPROVED = "approved"
    BOOK = "book"
    STATUS_CHOICES = [
        (NEEDS_REVIEW, "Needs review"),
        (CHECK, "Check: flagged for a look"),
        (AGREED, "AI and dictionary agree"),
        (DICTIONARY, "Dictionary only (no AI)"),
        (BOOK, "From the St. Bernard Psalter"),
        (APPROVED, "Approved"),
    ]
    # Statuses that re-pointing leaves alone unless forced.
    TRUSTED = (APPROVED, BOOK)

    SOURCE_AI = "ai"
    SOURCE_DICTIONARY = "dictionary"
    SOURCE_BOOK = "book"
    SOURCE_EDITOR = "editor"
    SOURCE_CHOICES = [
        (SOURCE_AI, "AI stress marking"),
        (SOURCE_DICTIONARY, "Dictionary"),
        (SOURCE_BOOK, "St. Bernard Psalter"),
        (SOURCE_EDITOR, "Editor"),
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
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, default="", db_index=True)
    tone = models.CharField(
        max_length=10,
        blank=True,
        default="",
        choices=TONE_CHOICES,
        help_text="The tone this verse is sung to. Blank uses the psalm's tone.",
    )
    book_page = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="The page of the St. Bernard Psalter this verse was copied from."
    )
    book_office = models.CharField(max_length=40, blank=True, default="", help_text="E.g. Day 4 Evening Prayer.")

    def __str__(self):
        return f"Pointing for {self.verse}"

    class Meta:
        ordering = ("verse__psalm__number", "verse__number")
        verbose_name = "psalm verse pointing"


class PointingProposal(UUIDModel):
    """A suggested correction to a verse's chant pointing, sent from the app.

    Anyone may propose one; an editor accepts it in the admin, which copies it
    to the verse's pointing (source "editor", status "approved").
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    STATUS_CHOICES = [(PENDING, "Pending"), (ACCEPTED, "Accepted"), (DECLINED, "Declined")]

    verse = models.ForeignKey(PsalmVerse, on_delete=models.CASCADE, related_name="pointing_proposals")
    first_half_stress = models.CharField(max_length=1200)
    second_half_stress = models.CharField(max_length=1200)
    tone = models.CharField(max_length=10, blank=True, default="", choices=TONE_CHOICES)
    # What was shown when the proposal was made, to see what it changes.
    previous_first_half = models.CharField(max_length=1200, blank=True, default="")
    previous_second_half = models.CharField(max_length=1200, blank=True, default="")
    note = models.TextField(blank=True, default="")
    name = models.CharField(max_length=200, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    reviewer_note = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Proposal for {self.verse}"

    class Meta:
        ordering = ("-created",)
        verbose_name = "pointing proposal"


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

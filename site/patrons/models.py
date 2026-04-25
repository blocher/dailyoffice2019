import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from patrons.dates import display_month_day, month_day_matches, occurrence_date, validate_month_day


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FamilyMember(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    confirmation_name = models.CharField(max_length=100, blank=True)
    maiden_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    class Meta:
        ordering = ("last_name", "first_name", "middle_name")
        constraints = [
            models.UniqueConstraint(
                fields=("first_name", "middle_name", "confirmation_name", "maiden_name", "last_name"),
                name="unique_patron_family_member_name",
            )
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts = [part for part in [self.first_name, self.middle_name, self.confirmation_name] if part]
        if self.maiden_name:
            parts.append("({})".format(self.maiden_name))
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)

    @property
    def sort_name(self):
        return "{}, {}".format(self.last_name, self.first_name)

    def save(self, *args, **kwargs):
        for field in ["first_name", "middle_name", "confirmation_name", "maiden_name", "last_name"]:
            setattr(self, field, getattr(self, field).strip())
        super().save(*args, **kwargs)


class TextRecipient(TimeStampedModel):
    family_member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    telephone_number = models.CharField(max_length=32)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("family_member__last_name", "family_member__first_name", "telephone_number")
        constraints = [
            models.UniqueConstraint(
                fields=("family_member", "telephone_number"),
                name="unique_patron_text_recipient_number",
            )
        ]

    def __str__(self):
        status = "enabled" if self.enabled else "disabled"
        return "{}: {} ({})".format(self.family_member, self.telephone_number, status)


class TextSchedule(TimeStampedModel):
    time = models.TimeField(help_text="Eastern time")
    relative_days = models.IntegerField(
        default=0,
        help_text="-1 is one day before the event, 0 is the day of the event, and 1 is one day after.",
    )

    class Meta:
        ordering = ("relative_days", "time")
        constraints = [models.UniqueConstraint(fields=("time", "relative_days"), name="unique_patron_text_schedule")]

    def __str__(self):
        if self.relative_days == 0:
            relative = "day of"
        elif self.relative_days < 0:
            relative = "{} day{} before".format(abs(self.relative_days), "" if self.relative_days == -1 else "s")
        else:
            relative = "{} day{} after".format(self.relative_days, "" if self.relative_days == 1 else "s")
        return "{} ET, {}".format(self.time.strftime("%-I:%M %p"), relative)


class PatronalFeast(TimeStampedModel):
    DATE_FIELDS = (
        ("general", "General Roman Calendar (USA)", "Catholic"),
        ("traditional", "Traditional Roman Calendar (1954)", "Traditional Catholic"),
        ("episcopal", "Episcopal Church", "Episcopal"),
    )

    family_member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    normalized_name = models.CharField(max_length=255)
    feast_name = models.CharField(max_length=255)
    general_calendar_name = models.CharField(max_length=255, blank=True)
    traditional_calendar_name = models.CharField(max_length=255, blank=True)
    episcopal_calendar_name = models.CharField(max_length=255, blank=True)

    general_month = models.PositiveSmallIntegerField(blank=True, null=True)
    general_day = models.PositiveSmallIntegerField(blank=True, null=True)
    traditional_month = models.PositiveSmallIntegerField(blank=True, null=True)
    traditional_day = models.PositiveSmallIntegerField(blank=True, null=True)
    episcopal_month = models.PositiveSmallIntegerField(blank=True, null=True)
    episcopal_day = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        ordering = ("family_member__last_name", "family_member__first_name", "normalized_name", "feast_name")
        constraints = [
            models.UniqueConstraint(
                fields=("family_member", "normalized_name", "feast_name"),
                name="unique_patronal_feast_for_member",
            )
        ]

    def __str__(self):
        return "{}: {}".format(self.family_member, self.normalized_name)

    def get_absolute_url(self):
        return reverse("patrons:feast_detail", args=[self.pk])

    def clean(self):
        errors = {}
        for prefix, label, _calendar_label in self.DATE_FIELDS:
            month_field = "{}_month".format(prefix)
            day_field = "{}_day".format(prefix)
            month = getattr(self, month_field)
            day = getattr(self, day_field)
            try:
                validate_month_day(month, day)
            except ValueError as exc:
                errors[month_field] = "{}: {}".format(label, exc)
        if errors:
            raise ValidationError(errors)

    @property
    def display_feast_name(self):
        return (
            self.general_calendar_name
            or self.traditional_calendar_name
            or self.episcopal_calendar_name
            or self.feast_name
        )

    @property
    def date_summary(self):
        pieces = []
        for prefix, label, _calendar_label in self.DATE_FIELDS:
            date_label = display_month_day(
                getattr(self, "{}_month".format(prefix)), getattr(self, "{}_day".format(prefix))
            )
            if date_label:
                pieces.append("{}: {}".format(label, date_label))
        return "; ".join(pieces)

    def iter_month_days(self):
        for prefix, _label, calendar_label in self.DATE_FIELDS:
            month = getattr(self, "{}_month".format(prefix))
            day = getattr(self, "{}_day".format(prefix))
            if month and day:
                yield prefix, calendar_label, month, day

    def occurrence_dates_for_year(self, year):
        seen = set()
        for _prefix, _calendar_label, month, day in self.iter_month_days():
            value = occurrence_date(year, month, day)
            if value not in seen:
                seen.add(value)
                yield value

    def calendar_labels_for_date(self, value):
        labels = []
        for _prefix, calendar_label, month, day in self.iter_month_days():
            if month_day_matches(value, month, day):
                labels.append(calendar_label)
        return labels

    def calendar_label_text_for_date(self, value):
        return ", ".join(self.calendar_labels_for_date(value))

    def matches_date(self, value):
        return any(month_day_matches(value, month, day) for _prefix, _label, month, day in self.iter_month_days())


class Event(TimeStampedModel):
    BIRTHDAY = "birthday"
    BAPTISM = "baptism"
    WEDDING = "wedding"
    CONFIRMATION = "confirmation"
    FIRST_CONFESSION = "first_confession"
    FIRST_COMMUNION = "first_communion"
    DIACONAL_ORDINATION = "diaconal_ordination"
    PRIESTLY_ORDINATION = "priestly_ordination"
    DEATH = "death"

    EVENT_TYPE_CHOICES = (
        (BIRTHDAY, "Birthday"),
        (BAPTISM, "Baptism Day"),
        (WEDDING, "Wedding Day"),
        (CONFIRMATION, "Confirmation Day"),
        (FIRST_CONFESSION, "First Confession Day"),
        (FIRST_COMMUNION, "First Communion Day"),
        (DIACONAL_ORDINATION, "Diaconal Ordination Day"),
        (PRIESTLY_ORDINATION, "Priestly Ordination Day"),
        (DEATH, "Death Day"),
    )

    family_member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    date = models.DateField()
    event_type = models.CharField(max_length=32, choices=EVENT_TYPE_CHOICES)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ("family_member__last_name", "family_member__first_name", "date")
        constraints = [
            models.UniqueConstraint(
                fields=("family_member", "event_type", "date"),
                name="unique_patron_event_for_member",
            )
        ]

    def __str__(self):
        return "{}: {} ({})".format(self.family_member, self.get_event_type_display(), self.date)

    def get_absolute_url(self):
        return reverse("patrons:event_detail", args=[self.pk])

    def occurrence_for_year(self, year):
        return occurrence_date(year, self.date.month, self.date.day)

    def matches_date(self, value):
        return self.occurrence_for_year(value.year) == value


class TextMessageSend(models.Model):
    recipient = models.ForeignKey(TextRecipient, on_delete=models.CASCADE)
    schedule = models.ForeignKey(TextSchedule, on_delete=models.SET_NULL, blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    patronal_feast = models.ForeignKey(PatronalFeast, on_delete=models.CASCADE, blank=True, null=True)
    occurrence_date = models.DateField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    message = models.TextField()
    success = models.BooleanField(default=False)
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-attempted_at",)
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(event__isnull=False) & Q(patronal_feast__isnull=True))
                    | (Q(event__isnull=True) & Q(patronal_feast__isnull=False))
                ),
                name="patron_send_has_event_or_feast",
            ),
            models.UniqueConstraint(
                fields=("recipient", "schedule", "event", "occurrence_date"),
                condition=Q(event__isnull=False),
                name="unique_patron_event_send",
            ),
            models.UniqueConstraint(
                fields=("recipient", "schedule", "patronal_feast", "occurrence_date"),
                condition=Q(patronal_feast__isnull=False),
                name="unique_patron_feast_send",
            ),
        ]

    def __str__(self):
        target = self.event or self.patronal_feast
        return "{} -> {} ({})".format(self.recipient, target, "success" if self.success else "failed")

    def clean(self):
        if bool(self.event_id) == bool(self.patronal_feast_id):
            raise ValidationError("Exactly one of event or patronal feast must be set.")


class CalendarFeed(TimeStampedModel):
    name = models.CharField(max_length=100, default="Patrons Calendar")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def rotate_token(self):
        self.token = uuid.uuid4()
        self.save()

    def get_absolute_url(self):
        return reverse("patrons:calendar_feed", args=[str(self.token)])

    @property
    def subscription_url(self):
        return "{}{}".format(settings.SITE_ADDRESS.rstrip("/"), self.get_absolute_url())

import uuid

from django.db import models


class AnalyticsEvent(models.Model):
    """A single, anonymous usage event.

    Office views are written server-side by ``AnalyticsMiddleware`` (so every
    app version is counted, and the two-request-per-office pattern is deduped by
    ignoring the ``include_audio_links`` request). ``audio_loaded`` is written by
    ``AudioTrackView`` when an MP3 is first served (an upper bound, since the
    player preloads audio). ``audio_play`` is posted by updated clients when the
    user actually presses play. ``client_id`` is a first-party anonymous id and
    is blank for old clients that predate the header.
    """

    OFFICE_VIEW = "office_view"
    AUDIO_PLAY = "audio_play"
    AUDIO_LOADED = "audio_loaded"
    EVENT_TYPE_CHOICES = [
        (OFFICE_VIEW, "Office view"),
        (AUDIO_PLAY, "Audio play (confirmed)"),
        (AUDIO_LOADED, "Audio loaded (approx.)"),
    ]

    SERVICE_OFFICE = "office"
    SERVICE_FAMILY = "family"
    SERVICE_TYPE_CHOICES = [
        (SERVICE_OFFICE, "Daily Office"),
        (SERVICE_FAMILY, "Family Prayer"),
    ]

    PLATFORM_WEB = "web"
    PLATFORM_IOS = "ios"
    PLATFORM_ANDROID = "android"
    PLATFORM_ELECTRON = "electron"
    PLATFORM_UNKNOWN = "unknown"
    PLATFORM_CHOICES = [
        (PLATFORM_WEB, "Web"),
        (PLATFORM_IOS, "iOS"),
        (PLATFORM_ANDROID, "Android"),
        (PLATFORM_ELECTRON, "Electron"),
        (PLATFORM_UNKNOWN, "Unknown"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_index=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, blank=True, default="")
    office = models.CharField(max_length=50, blank=True, default="", db_index=True)
    office_date = models.DateField(null=True, blank=True)
    client_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default=PLATFORM_UNKNOWN)
    browser = models.CharField(max_length=50, blank=True, default="")
    os = models.CharField(max_length=50, blank=True, default="")
    translation = models.CharField(max_length=20, blank=True, default="")
    # Snapshot of the office settings in effect for this view (office_view only),
    # captured from the request query params. Used for "most common setting"
    # distributions in the dashboard.
    settings = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["event_type", "created"]),
            models.Index(fields=["office", "created"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.service_type}/{self.office} ({self.created:%Y-%m-%d %H:%M})"

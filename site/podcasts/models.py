import uuid

from django.db import models


class PodcastEpisode(models.Model):
    """One published episode: a permanent copy of a day's office audio.

    The audio file lives under ``MEDIA_ROOT/podcasts/`` (``filename`` is
    relative to it) and is never deleted or rebuilt: podcast apps keep the
    enclosure URL forever. Deleting a row removes the episode from its feed but
    leaves the file in place.
    """

    feed_slug = models.CharField(max_length=64, db_index=True)
    date = models.DateField()
    title = models.CharField(max_length=512)
    summary = models.TextField(help_text="Plain-text episode description.")
    description_html = models.TextField(help_text="HTML show notes.")
    filename = models.CharField(max_length=512, unique=True)
    file_size = models.PositiveBigIntegerField()
    duration = models.FloatField(help_text="Seconds.")
    chapters = models.JSONField(default=list, blank=True)
    follow_along_url = models.URLField(max_length=4096)
    guid = models.CharField(max_length=255, unique=True)
    published_at = models.DateTimeField(db_index=True)
    notified_at = models.DateTimeField(
        null=True, blank=True, help_text="When directories were told the feed has this episode."
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "feed_slug")
        constraints = [models.UniqueConstraint(fields=("feed_slug", "date"), name="unique_podcast_episode_per_day")]

    def __str__(self):
        return f"{self.feed_slug}: {self.title}"


class PodcastDirectoryListing(models.Model):
    """Where a feed is listed (Apple Podcasts, Spotify, ...), once it is approved.

    Shown on the landing page; edit in the admin as each directory approves a show.
    """

    APPLE = "apple"
    SPOTIFY = "spotify"
    YOUTUBE_MUSIC = "youtube_music"
    AMAZON = "amazon"
    POCKET_CASTS = "pocket_casts"
    OVERCAST = "overcast"
    CASTRO = "castro"
    IHEART = "iheart"
    PODCAST_INDEX = "podcast_index"
    GOODPODS = "goodpods"
    DEEZER = "deezer"
    PLATFORM_CHOICES = [
        (APPLE, "Apple Podcasts"),
        (SPOTIFY, "Spotify"),
        (YOUTUBE_MUSIC, "YouTube Music"),
        (AMAZON, "Amazon Music / Audible"),
        (POCKET_CASTS, "Pocket Casts"),
        (OVERCAST, "Overcast"),
        (CASTRO, "Castro"),
        (IHEART, "iHeartRadio"),
        (PODCAST_INDEX, "Podcast Index"),
        (GOODPODS, "Goodpods"),
        (DEEZER, "Deezer"),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feed_slug = models.CharField(max_length=64, db_index=True)
    platform = models.CharField(max_length=32, choices=PLATFORM_CHOICES)
    url = models.URLField(max_length=1024)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("feed_slug", "order", "platform")
        constraints = [models.UniqueConstraint(fields=("feed_slug", "platform"), name="unique_podcast_listing")]

    def __str__(self):
        return f"{self.feed_slug} on {self.get_platform_display()}"

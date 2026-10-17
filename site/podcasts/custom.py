"""EXPERIMENTAL: a listener's own podcast, with any settings they choose.

A custom feed is one service ("office/morning_prayer", "readings/daily_office",
...) and one set of settings, saved as a ``CustomPodcastFeed`` behind a short
token: ``/podcasts/custom/<token>.xml``. It lists the last seven days, each
appearing at CUSTOM_PODCAST_PUBLISH_HOUR (2 a.m. Eastern) on its day.

Every episode is rendered through the same API view as the in-app player and
the public podcasts (``builder.render_office_audio``), so it is made of the same
content-addressed clips and is the same combined track: a custom feed with a
public feed's settings plays the public feed's track, and one that differs in a
single setting reuses every clip the change doesn't touch. Custom feeds keep no
audio of their own, never re-encode or tag the shared track (the in-app player
plays that file), and never touch the permanent archive under
``MEDIA_ROOT/podcasts/``.

Fetches drive building; there is no cron:

* A feed fetch lists only days already recorded as ready (a
  ``CustomPodcastEpisode``), so podcast apps never see an episode that would
  fail to download, and queues a background build (``office/audio_builds.py``)
  for each day of the window that isn't, so it appears on the next poll.
* An episode request serves the recorded combined track directly. If the
  track has been cleaned up (it is a disposable cache), it is reassembled from
  its clips on the spot; if clips are missing, nothing is synthesized in the
  request: one background build is queued and the answer is 503 Retry-After.
"""

import hashlib
import json
import logging
import os
import re
import secrets
from dataclasses import replace
from datetime import timedelta
from functools import partial
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from churchcal.calculations import get_calendar_date
from office import audio_builds
from office.api.views.index import AUDIO_BIBLE_TRANSLATIONS, audio_available
from office.combined_track import mp3_duration
from office.readings_audio import KINDS, SERVICE_NAMES
from podcasts import builder, catalog, episodes
from podcasts.models import CustomPodcastEpisode, CustomPodcastFeed

logger = logging.getLogger(__name__)

EASTERN = ZoneInfo("America/New_York")
WINDOW_DAYS = 7
TOKEN_BYTES = 8  # 11 URL-safe characters

# The office settings a custom feed may set: every key the public feeds set.
OFFICE_SETTING_KEYS = tuple(sorted(catalog.CONTEMPORARY_SETTINGS))
# The Readings page's choices, as /api/v1/readings_audio/<kind> takes them.
READINGS_CHOICES = {
    "translation": AUDIO_BIBLE_TRANSLATIONS,
    "psalms": ("contemporary", "traditional"),
    "style": ("whole_verse", "half_verse", "unison"),
    "psalter": ("30", "60"),
}
READINGS_SETTING_KEYS = tuple(sorted(READINGS_CHOICES))
SETTING_VALUE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
AUDIO_ONLY = "Audio is read only in English, from the ESV or the KJV."


class InvalidCustomFeed(ValueError):
    pass


def _services():
    """{service: (group, title, catalog feed or None)}: the public feeds' services, then the other readings."""
    services = {}
    for feed in catalog.FEEDS:
        if feed.style == catalog.CONTEMPORARY and feed.service not in services:
            services[feed.service] = (feed.group, feed.title, feed)
    for kind in KINDS:
        services.setdefault(f"readings/{kind}", ("readings", f"Readings for {SERVICE_NAMES[kind]}", None))
    return services


SERVICES = _services()


def builder_options():
    """What the landing page's builder offers: types, their offices, and the settings it may send."""
    return {
        "types": [
            {
                "slug": group["slug"],
                "title": group["title"],
                "description": group["description"],
                "offices": [
                    {"service": service, "title": title, "is_readings": service.startswith("readings/")}
                    for service, (group_slug, title, _) in SERVICES.items()
                    if group_slug == group["slug"]
                ],
            }
            for group in catalog.GROUPS
        ],
        "office_settings": {"keys": list(OFFICE_SETTING_KEYS), "defaults": dict(catalog.CONTEMPORARY_SETTINGS)},
        "readings_settings": {
            "keys": list(READINGS_SETTING_KEYS),
            "defaults": dict(catalog.READINGS_SETTINGS),
            "choices": {key: list(values) for key, values in READINGS_CHOICES.items()},
        },
        "audio": {"bible_translation": list(AUDIO_BIBLE_TRANSLATIONS), "display_language": ["english"]},
        "window_days": WINDOW_DAYS,
        "publish_hour": publish_hour(),
    }


def publish_hour():
    return getattr(settings, "CUSTOM_PODCAST_PUBLISH_HOUR", 2)


def _setting_options():
    from office.models import SettingOption

    options = {}
    for name, value in SettingOption.objects.values_list("setting__name", "value"):
        options.setdefault(name, set()).add(value)
    return options


def normalize(service, raw):
    """The settings a feed is saved with: every known key, sorted, defaults filled in.

    Raises ``InvalidCustomFeed`` for an unknown service or key, a value the
    site doesn't offer, or a combination there is no audio for.
    """
    if service not in SERVICES:
        raise InvalidCustomFeed("Unknown service.")
    if not isinstance(raw, dict):
        raise InvalidCustomFeed("Settings must be an object.")
    readings = service.startswith("readings/")
    keys = READINGS_SETTING_KEYS if readings else OFFICE_SETTING_KEYS
    defaults = catalog.READINGS_SETTINGS if readings else catalog.CONTEMPORARY_SETTINGS
    unknown = sorted(set(raw) - set(keys))
    if unknown:
        raise InvalidCustomFeed(f"Unknown settings: {', '.join(unknown)}.")
    for key, value in raw.items():
        if not isinstance(value, str) or not SETTING_VALUE.fullmatch(value):
            raise InvalidCustomFeed(f"Invalid value for {key}.")
    settings_ = {key: raw.get(key, defaults[key]) for key in keys}
    if readings:
        for key, value in settings_.items():
            if value not in READINGS_CHOICES[key]:
                raise InvalidCustomFeed(AUDIO_ONLY if key == "translation" else f"Invalid value for {key}.")
        return settings_
    if not audio_available(settings_["bible_translation"], settings_["display_language"]):
        raise InvalidCustomFeed(AUDIO_ONLY)
    options = _setting_options()
    for key in raw:
        if options.get(key) and raw[key] not in options[key]:
            raise InvalidCustomFeed(f"Invalid value for {key}.")
    return settings_


def settings_hash(settings_):
    return hashlib.sha256(json.dumps(settings_, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def get_or_create_feed(service, raw_settings):
    """(feed, created). The same service and settings always give the same feed."""
    normalized = normalize(service, raw_settings)
    digest = settings_hash(normalized)
    existing = CustomPodcastFeed.objects.filter(service=service, settings_hash=digest).first()
    if existing:
        return existing, False
    for _ in range(5):
        try:
            with transaction.atomic():
                feed = CustomPodcastFeed.objects.create(
                    token=secrets.token_urlsafe(TOKEN_BYTES),
                    service=service,
                    settings=normalized,
                    settings_hash=digest,
                )
            return feed, True
        except IntegrityError:
            # Someone else just saved these settings, or (rarely) the token is taken.
            existing = CustomPodcastFeed.objects.filter(service=service, settings_hash=digest).first()
            if existing:
                return existing, False
    raise RuntimeError("Could not allocate a custom podcast token.")


def is_traditional(custom):
    translation = custom.settings.get("translation") or custom.settings.get("bible_translation")
    return translation == "kjv"


def as_podcast_feed(custom):
    """The ``PodcastFeed`` episodes, show notes, and the feed are written from.

    Its ``slug`` is the closest public feed's, for its cover art: red for the
    ESV, green for the KJV. Its settings are the listener's.
    """
    group, office_title, public = SERVICES[custom.service]
    traditional = is_traditional(custom)
    if public is None:
        kind = custom.service.split("/", 1)[1]
        public = replace(
            catalog.get_feed("daily-office-readings"),
            service=custom.service,
            office_name=f"Readings for {SERVICE_NAMES[kind]}",
            evening=kind == "evening_prayer",
        )
    art = f"{public.slug}-traditional" if traditional else public.slug
    style = catalog.TRADITIONAL if traditional else catalog.CONTEMPORARY
    feed = replace(public, slug=art, style=style, custom_settings=dict(custom.settings), keywords=())
    title = f"My {office_title} (Experimental) — {catalog.AUTHOR}"
    return replace(
        feed,
        title=title,
        subtitle=f"{office_title}, with your own settings. The last {WINDOW_DAYS} days.",
        description=(
            f"Your own {office_title} podcast from the Daily Office: {feed.style_label}, with the settings you "
            f"chose. It keeps the last {WINDOW_DAYS} days, with each new day's episode at "
            f"{publish_hour()} a.m. Eastern, and every episode links to the text with your settings.\n\n"
            "This is an experiment, and this feed is private: only people with its link can find it. "
            f"Tell us how it works at {catalog.OWNER_EMAIL}.\n\n{catalog.SYNTHESIZED_VOICE_NOTE}"
        ),
    )


def publish_time(day):
    return episodes.published_at(day, hour=publish_hour())


def window(now=None):
    """The days a feed lists right now, newest first: the last seven that have appeared."""
    now = now or timezone.now()
    today = now.astimezone(EASTERN).date()
    latest = today if publish_time(today) <= now else today - timedelta(days=1)
    return [latest - timedelta(days=offset) for offset in range(WINDOW_DAYS)]


def prune(now=None):
    """Forget days that have left every feed's window."""
    CustomPodcastEpisode.objects.filter(date__lt=window(now)[-1]).delete()


def listed_episodes(custom, now=None):
    """The ready episodes in the window, newest first, for the feed XML."""
    days = window(now)
    rows = list(custom.episodes.filter(date__gte=days[-1], date__lte=days[0]).exclude(track_filename=""))
    for row in rows:
        row.published_at = publish_time(row.date)
        row.guid = f"dailyoffice2019-custom-{custom.token}-{row.date:%Y-%m-%d}"
    return rows


def build_identity(custom, day):
    return f"custom-podcast:{custom.pk}:{day:%Y-%m-%d}"


def queue_missing(custom, now=None):
    """Queue background builds for the window's days that aren't recorded yet.

    Includes the next day, so it is ready when it appears. Leaves room in the
    shared build queue for the in-app player (CUSTOM_PODCAST_MAX_PENDING).
    Returns how many were queued.
    """
    days = window(now)
    wanted = days + [days[0] + timedelta(days=1)]
    recorded = set(custom.episodes.filter(date__in=wanted).values_list("date", flat=True))
    limit = getattr(settings, "CUSTOM_PODCAST_MAX_PENDING", 8)
    queued = 0
    for day in wanted:
        if day in recorded:
            continue
        if audio_builds.pending_count() >= limit:
            break
        identity = build_identity(custom, day)
        if audio_builds.has_failed(identity):
            continue
        if audio_builds.schedule(identity, partial(build_episode, custom.pk, day)):
            queued += 1
    return queued


def track_path(filename):
    return os.path.join(settings.MEDIA_ROOT, filename)


def track_exists(filename):
    path = track_path(filename)
    return bool(filename) and os.path.isfile(path) and os.path.getsize(path) > 0


def record(custom, feed, day, calendar_date, data):
    """Save the day's ready combined track (from a render) for the feed to list."""
    single_track = data["audio"]["single_track"]
    filename = single_track[1].removeprefix(settings.MEDIA_URL).lstrip("/")
    path = builder.source_track_path(single_track)
    summary, description = episodes.show_notes(feed, day, calendar_date, data.get("modules"))
    row, _ = CustomPodcastEpisode.objects.update_or_create(
        feed=custom,
        date=day,
        defaults={
            "track_filename": filename,
            "file_size": os.path.getsize(path),
            "duration": mp3_duration(path),
            "chapters": episodes.chapters(single_track[2] if len(single_track) > 2 else []),
            "title": episodes.episode_title(feed, day, calendar_date),
            "summary": summary,
            "description_html": description,
            "follow_along_url": feed.follow_along_url(day),
        },
    )
    return row


def record_no_episode(custom, day):
    row, _ = CustomPodcastEpisode.objects.get_or_create(feed=custom, date=day)
    return row


def build_episode(custom_id, day):
    """Background job: render the day with generation allowed and record it. True when done."""
    custom = CustomPodcastFeed.objects.filter(pk=custom_id).first()
    if custom is None:
        return True
    existing = custom.episodes.filter(date=day).first()
    if existing and (not existing.track_filename or track_exists(existing.track_filename)):
        return True
    feed = as_podcast_feed(custom)
    calendar_date = get_calendar_date(day.strftime("%Y-%m-%d"))
    if not builder.is_publishable(feed, calendar_date):
        record_no_episode(custom, day)
        return True
    data = builder.render_office_audio(feed, day)
    record(custom, feed, day, calendar_date, data)
    return True


def ready_episode(custom, day):
    """The day's episode with its track on disk, assembling it from existing clips if need be.

    Returns None when the service has nothing that day. Raises
    ``audio_builds.AudioNotReady`` (after queueing a build) when clips are
    missing; nothing is synthesized here.
    """
    row = custom.episodes.filter(date=day).first()
    if row and (not row.track_filename or track_exists(row.track_filename)):
        return row if row.track_filename else None
    feed = as_podcast_feed(custom)
    calendar_date = get_calendar_date(day.strftime("%Y-%m-%d"))
    if not builder.is_publishable(feed, calendar_date):
        record_no_episode(custom, day)
        return None
    try:
        with audio_builds.deferred_generation(allow_assembly=True):
            data = builder.render_office_audio(feed, day)
    except audio_builds.AudioNotReady:
        identity = build_identity(custom, day)
        if not audio_builds.has_failed(identity):
            audio_builds.schedule(identity, partial(build_episode, custom.pk, day))
        raise
    return record(custom, feed, day, calendar_date, data)

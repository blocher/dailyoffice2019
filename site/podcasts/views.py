import logging
import re
from datetime import date

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from churchcal.audio_streaming import audio_file_response
from office.audio_builds import AudioNotReady
from office.audio_retention import podcast_media_root
from podcasts import catalog, custom, rss, transcripts
from podcasts.builder import ARTWORK_DIR, EpisodeBuildError
from podcasts.models import CustomPodcastFeed, PodcastDirectoryListing

logger = logging.getLogger(__name__)

FEED_CACHE_SECONDS = 15 * 60


def get_feed_or_404(slug):
    try:
        return catalog.get_feed(slug)
    except KeyError:
        raise Http404("No such podcast.")


class PodcastFeedView(View):
    """``/podcasts/<slug>.xml``: the RSS feed podcast apps subscribe to."""

    def get(self, request, slug):
        feed = get_feed_or_404(slug)
        response = HttpResponse(rss.render_feed(feed), content_type="application/rss+xml; charset=utf-8")
        response["Cache-Control"] = f"public, max-age={FEED_CACHE_SECONDS}"
        return response


class PodcastEpisodeAudioView(View):
    """``/podcasts/episodes/<slug>/<year>/<file>.mp3``: an episode's enclosure.

    Episode files never change once published, so they may be cached forever.
    Supports HEAD and byte ranges, which podcast apps and directories require.
    """

    def get(self, request, path):
        if not re.fullmatch(r"[a-z0-9-]+/\d{4}/[a-z0-9-]+\.mp3", path):
            raise Http404("No such episode.")
        response = audio_file_response(
            podcast_media_root(),
            path,
            range_header=request.META.get("HTTP_RANGE", ""),
            if_range=request.META.get("HTTP_IF_RANGE", ""),
        )
        if response.status_code in (200, 206):
            response["Content-Disposition"] = f'inline; filename="{path.rsplit("/", 1)[-1]}"'
            response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


class PodcastChaptersView(View):
    """``/podcasts/chapters/<slug>/<date>.json``: Podcasting 2.0 chapters."""

    def get(self, request, slug, year, month, day):
        get_feed_or_404(slug)
        try:
            episode_date = date(year, month, day)
        except ValueError:
            raise Http404("No such episode.")
        episode = rss.published_episodes(slug).filter(date=episode_date).first()
        if not episode:
            raise Http404("No such episode.")
        response = JsonResponse({"version": "1.2.0", "chapters": episode.chapters})
        response["Content-Type"] = "application/json+chapters"
        response["Cache-Control"] = "public, max-age=86400"
        return response


def transcript_response(episode, extension, cache_control):
    """An episode's timed transcript as WebVTT or SRT (see ``podcasts.transcripts``)."""
    if not episode or not episode.transcript:
        raise Http404("No transcript.")
    if extension == "srt":
        response = HttpResponse(
            transcripts.to_srt(episode.transcript), content_type="application/x-subrip; charset=utf-8"
        )
    else:
        response = HttpResponse(transcripts.to_vtt(episode.transcript), content_type="text/vtt; charset=utf-8")
    response["Cache-Control"] = cache_control
    response["Access-Control-Allow-Origin"] = "*"
    return response


class PodcastTranscriptView(View):
    """``/podcasts/transcripts/<slug>/<date>.vtt`` (or ``.srt``): an episode's timed transcript."""

    def get(self, request, slug, year, month, day, extension):
        get_feed_or_404(slug)
        try:
            episode_date = date(year, month, day)
        except ValueError:
            raise Http404("No such episode.")
        episode = rss.published_episodes(slug).filter(date=episode_date).first()
        return transcript_response(episode, extension, "public, max-age=86400")


class PodcastArtworkView(View):
    """``/podcasts/artwork/<slug>.jpg``: 3000px cover art (``-600`` for a small copy)."""

    def get(self, request, name):
        slug = name.removesuffix("-600")
        get_feed_or_404(slug)
        path = ARTWORK_DIR / f"{name}.jpg"
        if not path.is_file():
            raise Http404("No artwork.")
        response = FileResponse(open(path, "rb"), content_type="image/jpeg")
        response["Cache-Control"] = "public, max-age=86400"
        return response


def latest_episode(slug):
    episode = rss.published_episodes(slug).first()
    if not episode:
        return None
    return {
        "title": episode.title,
        "date": episode.date.isoformat(),
        "duration": round(episode.duration),
        "audio_url": rss.episode_audio_url(episode),
        "follow_along_url": episode.follow_along_url,
    }


class PodcastCatalogView(View):
    """``/api/v1/podcasts``: every feed, for the landing page."""

    def get(self, request):
        listings = {}
        for listing in PodcastDirectoryListing.objects.all():
            listings.setdefault(listing.feed_slug, []).append(
                {"platform": listing.platform, "label": listing.get_platform_display(), "url": listing.url}
            )
        feeds = [
            {
                "slug": feed.slug,
                "title": feed.title,
                "subtitle": feed.subtitle,
                "description": feed.description,
                "group": feed.group,
                "style": feed.style,
                "is_readings": feed.is_readings,
                "feed_url": rss.feed_url(feed.slug),
                "artwork_url": rss.artwork_url(feed.slug),
                "artwork_small_url": rss.artwork_url(f"{feed.slug}-600"),
                "style_label": feed.style_label,
                "listings": listings.get(feed.slug, []),
                "episode_count": rss.published_episodes(feed.slug).count(),
                "latest_episode": latest_episode(feed.slug),
            }
            for feed in catalog.FEEDS
        ]
        response = JsonResponse(
            {
                "groups": catalog.GROUPS,
                "feeds": feeds,
                "live_alternative": catalog.LIVE_ALTERNATIVE,
                "custom": custom.builder_options(),
            }
        )
        response["Cache-Control"] = "public, max-age=300"
        return response


# --- EXPERIMENTAL custom podcasts (see podcasts/custom.py) -------------------


class CustomPodcastThrottle(SimpleRateThrottle):
    """New custom feeds per IP address, signed in or not."""

    scope = "custom_podcast"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


def custom_feed_json(feed, created=False):
    podcast = custom.as_podcast_feed(feed)
    return {
        "token": feed.token,
        "service": feed.service,
        "settings": feed.settings,
        "title": podcast.title,
        "style_label": podcast.style_label,
        "feed_url": rss.custom_feed_url(feed.token),
        "artwork_url": rss.artwork_url(f"{podcast.slug}-600"),
        "created": created,
    }


class CustomPodcastCreateView(APIView):
    """``POST /api/v1/podcasts/custom`` with ``{"service": ..., "settings": {...}}``.

    Returns the feed for that service and settings, creating it the first time
    (201) and returning the same feed after that (200). Rate-limited per IP.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CustomPodcastThrottle]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        try:
            feed, created = custom.get_or_create_feed(data.get("service"), data.get("settings") or {})
        except custom.InvalidCustomFeed as exc:
            return Response({"detail": str(exc)}, status=400)
        if created:
            # Start on the window now, so episodes are waiting when the app first asks.
            custom.queue_missing(feed)
        return Response(custom_feed_json(feed, created), status=201 if created else 200)


def get_custom_feed_or_404(token):
    feed = CustomPodcastFeed.objects.filter(token=token).first()
    if not feed:
        raise Http404("No such podcast.")
    return feed


def custom_episode_day_or_404(year, month, day):
    try:
        episode_date = date(year, month, day)
    except ValueError:
        raise Http404("No such episode.")
    if episode_date not in custom.window():
        raise Http404("No such episode.")
    return episode_date


class CustomPodcastFeedView(View):
    """``/podcasts/custom/<token>.xml``: a listener's own feed, the last seven days.

    Lists only ready days, and queues builds for the rest (see podcasts/custom.py).
    """

    def get(self, request, token):
        feed = get_custom_feed_or_404(token)
        now = timezone.now()
        CustomPodcastFeed.objects.filter(pk=feed.pk).update(last_fetched_at=now)
        custom.prune(now)
        try:
            custom.queue_missing(feed, now)
        except Exception:
            logger.exception("Could not queue custom podcast builds")
        content = rss.render_custom_feed(custom.as_podcast_feed(feed), feed.token, custom.listed_episodes(feed, now))
        response = HttpResponse(content, content_type="application/rss+xml; charset=utf-8")
        response["Cache-Control"] = "private, max-age=300"
        response["X-Robots-Tag"] = "noindex"
        return response


class CustomPodcastEpisodeAudioView(View):
    """``/podcasts/custom/<token>/<date>.mp3``: the shared combined track, served as is.

    Never re-encoded or tagged: the in-app player plays the same file. 503
    with Retry-After while a missing clip is built in the background.
    """

    def get(self, request, token, year, month, day):
        feed = get_custom_feed_or_404(token)
        episode_date = custom_episode_day_or_404(year, month, day)
        try:
            episode = custom.ready_episode(feed, episode_date)
        except AudioNotReady:
            response = HttpResponse("This episode is being prepared. Please try again shortly.", status=503)
            response["Retry-After"] = str(settings.CUSTOM_PODCAST_RETRY_AFTER)
            response["Cache-Control"] = "no-store"
            return response
        except EpisodeBuildError:
            logger.warning("Custom podcast %s has no audio for %s", feed.token, episode_date, exc_info=True)
            episode = None
        if episode is None:
            raise Http404("No such episode.")
        response = audio_file_response(
            settings.MEDIA_ROOT,
            episode.track_filename,
            range_header=request.META.get("HTTP_RANGE", ""),
            if_range=request.META.get("HTTP_IF_RANGE", ""),
        )
        if response.status_code in (200, 206):
            response["Content-Disposition"] = f'inline; filename="{episode_date:%Y-%m-%d}.mp3"'
            response["Cache-Control"] = "private, max-age=86400"
            response["X-Robots-Tag"] = "noindex"
        return response


class CustomPodcastChaptersView(View):
    """``/podcasts/custom/<token>/<date>.json``: Podcasting 2.0 chapters of a listed episode."""

    def get(self, request, token, year, month, day):
        feed = get_custom_feed_or_404(token)
        episode_date = custom_episode_day_or_404(year, month, day)
        episode = feed.episodes.filter(date=episode_date).exclude(track_filename="").first()
        if not episode:
            raise Http404("No such episode.")
        response = JsonResponse({"version": "1.2.0", "chapters": episode.chapters})
        response["Content-Type"] = "application/json+chapters"
        response["Cache-Control"] = "private, max-age=86400"
        return response


class CustomPodcastTranscriptView(View):
    """``/podcasts/custom/<token>/<date>.vtt`` (or ``.srt``): the timed transcript of a listed episode."""

    def get(self, request, token, year, month, day, extension):
        feed = get_custom_feed_or_404(token)
        episode_date = custom_episode_day_or_404(year, month, day)
        episode = feed.episodes.filter(date=episode_date).exclude(track_filename="").first()
        response = transcript_response(episode, extension, "private, max-age=86400")
        response["X-Robots-Tag"] = "noindex"
        return response

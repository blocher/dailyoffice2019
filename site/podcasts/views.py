import re
from datetime import date

from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views import View

from churchcal.audio_streaming import audio_file_response
from office.audio_retention import podcast_media_root
from podcasts import catalog, rss
from podcasts.builder import ARTWORK_DIR
from podcasts.models import PodcastDirectoryListing

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
            }
        )
        response["Cache-Control"] = "public, max-age=300"
        return response

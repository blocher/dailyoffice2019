"""RSS 2.0 feeds with the Apple Podcasts (itunes:) and Podcasting 2.0 (podcast:) tags.

Specs: https://podcasters.apple.com/support/823-podcast-requirements and
https://podcastindex.org/namespace/1.0.
"""

import uuid
import xml.etree.ElementTree as ET
from email.utils import format_datetime

from django.conf import settings
from django.utils import timezone

from podcasts import catalog
from podcasts.models import PodcastEpisode

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
PODCAST = "https://podcastindex.org/namespace/1.0"
ATOM = "http://www.w3.org/2005/Atom"
CONTENT = "http://purl.org/rss/1.0/modules/content/"
for prefix, namespace in (("itunes", ITUNES), ("podcast", PODCAST), ("atom", ATOM), ("content", CONTENT)):
    ET.register_namespace(prefix, namespace)

# Podcasting 2.0 podcast:guid namespace (a UUIDv5 of the feed URL without scheme).
PODCAST_GUID_NAMESPACE = uuid.UUID("ead4c236-bf58-58c6-a2c6-a6b28d128cb6")
WEBSUB_HUB = "https://pubsubhubbub.appspot.com/"


def base_url():
    return getattr(settings, "PODCAST_BASE_URL", "https://api.dailyoffice2019.com").rstrip("/")


def feed_url(slug):
    return f"{base_url()}/podcasts/{slug}.xml"


def artwork_url(slug):
    return f"{base_url()}/podcasts/artwork/{slug}.jpg"


def episode_audio_url(episode):
    return f"{base_url()}/podcasts/episodes/{episode.filename}"


def chapters_url(episode):
    return f"{base_url()}/podcasts/chapters/{episode.feed_slug}/{episode.date:%Y-%m-%d}.json"


def podcast_guid(slug):
    return str(uuid.uuid5(PODCAST_GUID_NAMESPACE, feed_url(slug).split("://", 1)[1].rstrip("/")))


def published_episodes(slug, now=None):
    now = now or timezone.now()
    return PodcastEpisode.objects.filter(feed_slug=slug, published_at__lte=now).order_by("-published_at")


def itunes_duration(seconds):
    return str(int(round(seconds)))


def _sub(parent, tag, content=None, /, **attributes):
    element = ET.SubElement(parent, tag, {key: str(value) for key, value in attributes.items()})
    if content is not None:
        element.text = str(content)
    return element


def _channel(feed, self_url, artwork, private=False):
    """The <rss> element and its <channel>, before any items."""
    rss = ET.Element("rss", {"version": "2.0"})
    channel = _sub(rss, "channel")
    _sub(channel, f"{{{ATOM}}}link", href=self_url, rel="self", type="application/rss+xml")
    if not private:
        _sub(channel, f"{{{ATOM}}}link", href=WEBSUB_HUB, rel="hub")
    _sub(channel, "title", feed.title)
    _sub(channel, "link", catalog.LANDING_PAGE_URL)
    _sub(channel, "description", feed.description)
    _sub(channel, "language", catalog.LANGUAGE)
    _sub(channel, "copyright", catalog.COPYRIGHT)
    _sub(channel, "generator", "dailyoffice2019.com")
    _sub(channel, "ttl", 60)
    image = _sub(channel, "image")
    _sub(image, "url", artwork)
    _sub(image, "title", feed.title)
    _sub(image, "link", catalog.LANDING_PAGE_URL)

    _sub(channel, f"{{{ITUNES}}}title", feed.title)
    _sub(channel, f"{{{ITUNES}}}subtitle", feed.subtitle)
    _sub(channel, f"{{{ITUNES}}}summary", feed.description)
    _sub(channel, f"{{{ITUNES}}}author", catalog.AUTHOR)
    _sub(channel, f"{{{ITUNES}}}type", "episodic")
    _sub(channel, f"{{{ITUNES}}}explicit", "false")
    _sub(channel, f"{{{ITUNES}}}image", href=artwork)
    _sub(channel, f"{{{ITUNES}}}keywords", ",".join(feed.keywords))
    if private:
        # Keep a listener's own feed out of Apple's directory and search.
        _sub(channel, f"{{{ITUNES}}}block", "Yes")
    owner = _sub(channel, f"{{{ITUNES}}}owner")
    _sub(owner, f"{{{ITUNES}}}name", catalog.OWNER_NAME)
    _sub(owner, f"{{{ITUNES}}}email", catalog.OWNER_EMAIL)
    category, subcategory = catalog.CATEGORY
    parent = _sub(channel, f"{{{ITUNES}}}category", text=category)
    _sub(parent, f"{{{ITUNES}}}category", text=subcategory)
    return rss, channel


def _item(channel, episode, audio_url, artwork, chapters=None):
    """One <item>. ``episode`` has the show notes, guid, size, and duration of a recorded episode."""
    item = _sub(channel, "item")
    _sub(item, "title", episode.title)
    _sub(item, f"{{{ITUNES}}}title", episode.title)
    _sub(item, "link", episode.follow_along_url)
    _sub(item, "description", episode.description_html)
    _sub(item, f"{{{CONTENT}}}encoded", episode.description_html)
    _sub(item, f"{{{ITUNES}}}summary", episode.summary)
    _sub(item, "guid", episode.guid, isPermaLink="false")
    _sub(item, "pubDate", format_datetime(episode.published_at))
    _sub(item, "enclosure", url=audio_url, length=episode.file_size, type="audio/mpeg")
    _sub(item, f"{{{ITUNES}}}duration", itunes_duration(episode.duration))
    _sub(item, f"{{{ITUNES}}}episodeType", "full")
    _sub(item, f"{{{ITUNES}}}explicit", "false")
    _sub(item, f"{{{ITUNES}}}image", href=artwork)
    if chapters:
        _sub(item, f"{{{PODCAST}}}chapters", url=chapters, type="application/json+chapters")
    return item


def _serialize(rss):
    ET.indent(rss, space="  ")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="utf-8")


def render_feed(feed, now=None):
    """The feed XML as bytes."""
    artwork = artwork_url(feed.slug)
    rss, channel = _channel(feed, feed_url(feed.slug), artwork)
    _sub(channel, f"{{{PODCAST}}}guid", podcast_guid(feed.slug))
    _sub(channel, f"{{{PODCAST}}}locked", "yes", owner=catalog.OWNER_EMAIL)
    _sub(channel, f"{{{PODCAST}}}medium", "podcast")
    _sub(channel, f"{{{PODCAST}}}funding", "Support the Daily Office", url=catalog.SUPPORT_URL)
    podroll = _sub(channel, f"{{{PODCAST}}}podroll")
    for other in catalog.FEEDS:
        if other.slug != feed.slug and other.group == feed.group and other.style == feed.style:
            _sub(podroll, f"{{{PODCAST}}}remoteItem", feedGuid=podcast_guid(other.slug), feedUrl=feed_url(other.slug))

    for episode in published_episodes(feed.slug, now):
        _item(
            channel,
            episode,
            episode_audio_url(episode),
            artwork,
            chapters=chapters_url(episode) if episode.chapters else None,
        )
    return _serialize(rss)


def custom_feed_url(token):
    return f"{base_url()}/podcasts/custom/{token}.xml"


def custom_episode_url(token, day, extension="mp3"):
    return f"{base_url()}/podcasts/custom/{token}/{day:%Y-%m-%d}.{extension}"


def render_custom_feed(feed, token, episodes):
    """A listener's own feed (see ``podcasts.custom``): private, with only ``episodes``.

    ``feed`` is the custom feed's ``PodcastFeed``; its ``slug`` names the public
    feed whose cover art it borrows. No hub, guid, or podroll: it is never listed.
    """
    artwork = artwork_url(feed.slug)
    rss, channel = _channel(feed, custom_feed_url(token), artwork, private=True)
    _sub(channel, f"{{{PODCAST}}}medium", "podcast")
    _sub(channel, f"{{{PODCAST}}}funding", "Support the Daily Office", url=catalog.SUPPORT_URL)
    for episode in episodes:
        _item(
            channel,
            episode,
            custom_episode_url(token, episode.date),
            artwork,
            chapters=custom_episode_url(token, episode.date, "json") if episode.chapters else None,
        )
    return _serialize(rss)

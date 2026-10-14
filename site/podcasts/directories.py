"""Tell podcast directories and apps that a feed has a new episode.

Apple Podcasts, Spotify, and the rest poll feeds on their own schedule; these
pings just make new episodes appear sooner. None needs an account:

* WebSub (the feed's ``atom:link rel="hub"``), used by Pocket Casts, Podcast
  Addict, and others that subscribe to the hub.
* Podcast Index ``hub/pubnotify``, which feeds every Podcasting 2.0 app.
* Overcast's ping endpoint.

Adding a new feed to Podcast Index (``add_to_podcast_index``) does need a
read-write API key: PODCAST_INDEX_API_KEY and PODCAST_INDEX_API_SECRET.
"""

import hashlib
import time

import requests
from django.conf import settings

from podcasts.rss import WEBSUB_HUB, feed_url

TIMEOUT = (10, 30)
PODCAST_INDEX_API = "https://api.podcastindex.org/api/1.0"


def ping_websub(url):
    response = requests.post(WEBSUB_HUB, data={"hub.mode": "publish", "hub.url": url}, timeout=TIMEOUT)
    response.raise_for_status()


def ping_podcast_index(url):
    response = requests.get(f"{PODCAST_INDEX_API}/hub/pubnotify", params={"url": url}, timeout=TIMEOUT)
    response.raise_for_status()


def ping_overcast(url):
    response = requests.get("https://overcast.fm/ping", params={"urlprefix": url}, timeout=TIMEOUT)
    response.raise_for_status()


PINGS = {"websub": ping_websub, "podcast_index": ping_podcast_index, "overcast": ping_overcast}


def notify(slug):
    """Ping every service for one feed; return {service: error or None}."""
    url = feed_url(slug)
    results = {}
    for name, ping in PINGS.items():
        try:
            ping(url)
            results[name] = None
        except requests.RequestException as exc:
            results[name] = str(exc)
    return results


def podcast_index_headers():
    key = getattr(settings, "PODCAST_INDEX_API_KEY", "")
    secret = getattr(settings, "PODCAST_INDEX_API_SECRET", "")
    if not key or not secret:
        raise ValueError("Set PODCAST_INDEX_API_KEY and PODCAST_INDEX_API_SECRET (free at api.podcastindex.org).")
    now = str(int(time.time()))
    return {
        "User-Agent": "dailyoffice2019.com",
        "X-Auth-Key": key,
        "X-Auth-Date": now,
        "Authorization": hashlib.sha1(f"{key}{secret}{now}".encode()).hexdigest(),
    }


def add_to_podcast_index(slug):
    """Submit a feed to Podcast Index; returns its Podcast Index feed id."""
    response = requests.post(
        f"{PODCAST_INDEX_API}/add/byfeedurl",
        params={"url": feed_url(slug)},
        headers=podcast_index_headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("feedId")

"""Short-lived server-side cache of rendered office API responses.

Office pages are the hottest and heaviest API calls: the same date and settings
are requested by many readers each morning. Entries live in the default Django
cache (memcached in production) for ``OFFICE_API_CACHE_SECONDS`` (60 s), keyed
on the full path and query string, so an edit in the admin or the database is
visible within about a minute.

The cache sits inside the view, so middleware -- including
``analytics.middleware.AnalyticsMiddleware`` -- still sees every request. No
``Cache-Control`` header is added: a browser or CDN copy would hide repeat
views from analytics and outlive an explicit clear.

Clearing:
  * ``python manage.py clear_office_cache`` (or ``clear()`` from a shell)
  * any Django admin add/change/delete (see ``OfficeConfig.ready``)
  * every deploy: ``deploy/server.sh`` flushes memcached
Clearing bumps a generation number embedded in every key, which is O(1) and
works with memcached, which cannot delete by prefix; old entries just expire.
"""

import base64
import hashlib
import logging
import time
import zlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger(__name__)

GENERATION_KEY = "office-api-cache:generation"


def enabled():
    return settings.OFFICE_API_CACHE_SECONDS > 0


def _generation():
    generation = cache.get(GENERATION_KEY)
    if generation is None:
        # A fresh, never-reused value, so an evicted counter cannot revive
        # entries from before the last clear.
        cache.add(GENERATION_KEY, time.time_ns(), timeout=None)
        generation = cache.get(GENERATION_KEY)
    return generation


def clear():
    """Invalidate every cached office response."""
    cache.set(GENERATION_KEY, time.time_ns(), timeout=None)


def key_for(request, fmt):
    """Cache key for this request's full path, query string, and format.

    Returns None (serve uncached) when caching is off or the cache is down.
    """
    if not enabled():
        return None
    digest = hashlib.sha256(request.get_full_path().encode()).hexdigest()
    try:
        return f"office-api:{_generation()}:{fmt}:{digest}"
    except Exception:
        logger.warning("Office response cache unavailable", exc_info=True)
        return None


def fetch(key):
    """Return a cached JSON response, or None. Cache outages are not errors."""
    try:
        content = cache.get(key)
    except Exception:
        logger.warning("Office response cache read failed", exc_info=True)
        return None
    if content is None:
        return None
    response = HttpResponse(zlib.decompress(base64.b64decode(content)), content_type="application/json")
    response["X-Office-Cache"] = "hit"
    return response


def store(key, content):
    """Store rendered JSON bytes.

    Compressed because memcached items are capped at 1 MB; base64 text because
    the dev debug toolbar's cache panel cannot record binary values.
    """
    try:
        value = base64.b64encode(zlib.compress(content)).decode("ascii")
        cache.set(key, value, timeout=settings.OFFICE_API_CACHE_SECONDS)
    except Exception:
        logger.warning("Office response cache write failed", exc_info=True)

"""Let Cloudflare serve the API's public content from its edge.

Office, family, calendar, readings, and library responses are the same for
everyone who asks for the same URL (the settings are all in the query string),
and offline sync asks for many days of them at once. ``EdgeCacheMiddleware``
marks a successful GET of those paths

    Cache-Control: public, max-age=0, s-maxage=<EDGE_CACHE_SECONDS>
    Cache-Tag: content

so Cloudflare keeps one copy per URL while browsers always ask again. A view
that sets its own ``Cache-Control`` (audio that is still being built answers
``no-store``) is left alone.

Cloudflare only caches these JSON paths because of a Cache Rule on the zone
(hostname api.dailyoffice2019.com, path starting /api/v1/: eligible for cache,
edge TTL from the origin's Cache-Control, bypassing when there is none).
Without the rule the headers do nothing.

``purge()`` drops every ``content``-tagged copy, and runs wherever the office
response cache is cleared (``office.response_cache.clear``): admin edits,
``manage.py clear_office_cache``, and every deploy. Audio tracks are cached by
Cloudflare too, but untagged, so a purge leaves them alone. It needs
CLOUDFLARE_ZONE_ID and CLOUDFLARE_API_TOKEN (a token with Zone > Cache Purge);
without them it does nothing, and edits reach readers within EDGE_CACHE_SECONDS.
"""

import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TAG = "content"
PURGE_URL = "https://api.cloudflare.com/client/v4/zones/{zone}/purge_cache"

# (path pattern, short) -- short paths change on their own (site messages
# expire), so they keep only SHORT_EDGE_CACHE_SECONDS.
_DATE = r"\d{4}-\d{1,2}-\d{1,2}"
PATHS = [
    (re.compile(rf"^/api/v1/(office|family)/[a-z_]+/{_DATE}/?$"), False),
    (re.compile(r"^/api/v1/calendar/\d{4}(-\d{1,2}){0,2}/?$"), False),
    (re.compile(rf"^/api/v1/readings/{_DATE}/?$"), False),
    (re.compile(r"^/api/v1/commemorations/[0-9a-f-]+/?$"), False),
    (re.compile(r"^/api/v1/(available_settings|litany|collects|grouped_collects|collect_categories|about)/?$"), False),
    (re.compile(r"^/api/v1/psalms(/.*)?$"), False),
    (re.compile(r"^/api/v1/site_messages/?$"), True),
]
SHORT_EDGE_CACHE_SECONDS = 60


def edge_seconds(path):
    """Edge lifetime for this path, or None when it isn't edge-cached."""
    for pattern, short in PATHS:
        if pattern.match(path):
            return SHORT_EDGE_CACHE_SECONDS if short else settings.EDGE_CACHE_SECONDS
    return None


class EdgeCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method not in ("GET", "HEAD") or response.status_code != 200:
            return response
        if response.has_header("Cache-Control") or response.cookies:
            return response
        seconds = edge_seconds(request.path_info)
        if seconds:
            response["Cache-Control"] = f"public, max-age=0, s-maxage={seconds}"
            response["Cache-Tag"] = TAG
        return response


def purge():
    """Drop Cloudflare's copies of tagged content. Failures are logged, not raised."""
    zone, token = settings.CLOUDFLARE_ZONE_ID, settings.CLOUDFLARE_API_TOKEN
    if not zone or not token:
        return False
    try:
        response = requests.post(
            PURGE_URL.format(zone=zone),
            json={"tags": [TAG]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.warning("Cloudflare cache purge failed", exc_info=True)
        return False
    return True

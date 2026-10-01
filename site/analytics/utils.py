import datetime

from django.apps import apps
from django.core.cache import cache

try:  # Optional dependency: analytics must never break the site if it's missing.
    from user_agents import parse as parse_user_agent
except ImportError:  # pragma: no cover - exercised only when dep is absent
    parse_user_agent = None

from analytics.models import AnalyticsEvent

_SETTING_NAMES_CACHE_KEY = "analytics_known_setting_names"


def known_setting_names():
    """Return the set of valid office setting keys (``Setting.name``).

    These are exactly the query-param keys the client sends on an office
    request, so they let us capture the settings snapshot while ignoring other
    params (extra_collects, include_audio_links, cache-busters, etc.). Cached
    briefly since settings rarely change.
    """
    names = cache.get(_SETTING_NAMES_CACHE_KEY)
    if names is None:
        setting_model = apps.get_model("office", "Setting")
        names = set(setting_model.objects.values_list("name", flat=True))
        cache.set(_SETTING_NAMES_CACHE_KEY, names, 300)
    return names


# Platform is only trusted when the client explicitly reports it via the
# X-Client-Platform header (updated web/native builds). We deliberately do NOT
# infer native-vs-web from the User-Agent, because a Capacitor WebView is
# indistinguishable from mobile Safari/Chrome and guessing would mislabel most
# mobile web users as native. Old clients therefore land in "unknown"; the
# `os` breakdown (iOS/Android/desktop) still works for every version.
KNOWN_PLATFORMS = {
    AnalyticsEvent.PLATFORM_WEB,
    AnalyticsEvent.PLATFORM_IOS,
    AnalyticsEvent.PLATFORM_ANDROID,
    AnalyticsEvent.PLATFORM_ELECTRON,
}


def parse_client_meta(request, declared_platform=None):
    """Return ``(platform, browser, os)`` for an incoming request.

    ``platform`` prefers an explicit value (payload field or X-Client-Platform
    header); otherwise it is ``unknown``. ``browser`` and ``os`` are parsed from
    the User-Agent and are reliable across all app versions.
    """
    platform = (declared_platform or request.headers.get("X-Client-Platform") or "").strip().lower()
    if platform not in KNOWN_PLATFORMS:
        platform = AnalyticsEvent.PLATFORM_UNKNOWN

    browser = ""
    os_family = ""
    if parse_user_agent is not None:
        ua = parse_user_agent(request.META.get("HTTP_USER_AGENT", "") or "")
        browser = (ua.browser.family or "").strip()
        os_family = (ua.os.family or "").strip()

    return platform, browser, os_family


def parse_office_date(value):
    """Parse a loose ``YYYY-M-D`` string into a ``date`` (or ``None``)."""
    if not value:
        return None
    try:
        year, month, day = (int(part) for part in str(value).split("-")[:3])
        return datetime.date(year, month, day)
    except (ValueError, TypeError):
        return None


def office_date_from_kwargs(kwargs):
    try:
        return datetime.date(int(kwargs["year"]), int(kwargs["month"]), int(kwargs["day"]))
    except (KeyError, ValueError, TypeError):
        return None


def record_audio_loaded(request, is_initial_request):
    """Best-effort ``audio_loaded`` event for an MP3 serve.

    Only the initial (non-continuation) request is logged so range/seek requests
    for the same track don't inflate the count. This counts audio that was
    fetched by the player, which is an upper bound on plays because the client
    preloads audio; the dashboard labels it accordingly.
    """
    if not is_initial_request:
        return
    try:
        client_id = (request.headers.get("X-Client-Id") or request.GET.get("cid") or "").strip()
        platform, browser, os_family = parse_client_meta(request)
        AnalyticsEvent.objects.create(
            event_type=AnalyticsEvent.AUDIO_LOADED,
            client_id=client_id[:64],
            platform=platform,
            browser=browser[:50],
            os=os_family[:50],
        )
    except Exception:
        pass

"""Office views prayed offline, reported by the app once it is back online.

The app keeps days of offices on the device. Opening one offline makes no
request, so the middleware can't count it; the app queues the view and posts
it to ``/api/v1/analytics/offline_views`` (``analytics.views.OfflineOfficeViewsView``)
later:

    {"client_id": "...", "platform": "ios", "views": [
        {"view_id": "...", "service_type": "office", "office": "morning_prayer",
         "office_date": "2026-11-02", "translation": "esv",
         "viewed_at": "2026-11-02T07:14:00Z", "settings": {...}}, ...]}

Views are stored with ``offline=True`` and ``created`` set to when they were
viewed (within the last 60 days). At most ``MAX_VIEWS`` per request; views that
don't name a known office are skipped. Anyone can post here, so views need a
``client_id`` and each device counts at most ``MAX_PER_DAY`` a day (eight
offices, each opened twice). A device id is the client's own choice, so each
address also counts at most ``MAX_PER_IP_PER_DAY`` a day (room for a household
or a church on one connection). The rest are skipped. A ``view_id`` already stored
(a batch sent again after its answer was lost) is skipped too. Skipped views
still count as handled, so the app lets them go.
"""

import datetime

from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from analytics.middleware import OFFICE_VIEW_URL_NAMES
from analytics.models import AnalyticsEvent
from analytics.utils import clean_text, known_setting_names, parse_office_date

MAX_VIEWS = 100
MAX_PER_DAY = 16
MAX_PER_IP_PER_DAY = 300
MAX_AGE = datetime.timedelta(days=60)


def parse_viewed_at(value, default):
    """An ISO datetime from a client, made aware (UTC); ``default`` when unreadable."""
    try:
        parsed = parse_datetime(value) if isinstance(value, str) else None
    except ValueError:
        # Well formed but not a real time ("2026-02-30T07:00").
        parsed = None
    if parsed is None:
        return default
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, datetime.timezone.utc)
    return parsed


def ip_count_key(ip):
    return f"analytics_offline_views_ip:{ip}:{timezone.localdate().isoformat()}"


def record(views, client_id, ip, platform, browser, os_family):
    """Store the views worth counting; returns how many were stored.

    Raises ``IntegrityError`` when another request stored one of the same
    ``view_id``s at the same moment; nothing is stored then.
    """
    if not client_id:
        return 0
    ip_key = ip_count_key(ip or "unknown")
    room = MAX_PER_IP_PER_DAY - (cache.get(ip_key) or 0)
    if room <= 0:
        return 0
    views = [view for view in views[:MAX_VIEWS] if isinstance(view, dict)]
    allowed_settings = known_setting_names()
    known_offices = set(OFFICE_VIEW_URL_NAMES.values())
    now = timezone.now()
    # Views already counted for this device, by day.
    counted = (
        AnalyticsEvent.objects.filter(client_id=client_id, offline=True, created__gte=now - MAX_AGE)
        .annotate(day=TruncDate("created"))
        .values("day")
        .annotate(count=Count("id"))
    )
    per_day = {row["day"]: row["count"] for row in counted}
    view_ids = [clean_text(view.get("view_id"), 40) for view in views]
    seen = set(AnalyticsEvent.objects.filter(view_id__in=[v for v in view_ids if v]).values_list("view_id", flat=True))

    events = []
    for view, view_id in zip(views, view_ids):
        service_type = str(view.get("service_type") or "")
        office = str(view.get("office") or "")
        if (service_type, office) not in known_offices:
            continue
        if view_id and view_id in seen:
            continue
        if view_id:
            seen.add(view_id)
        viewed_at = parse_viewed_at(view.get("viewed_at"), now)
        viewed_at = min(max(viewed_at, now - MAX_AGE), now)
        day = timezone.localdate(viewed_at)
        if per_day.get(day, 0) >= MAX_PER_DAY:
            continue
        per_day[day] = per_day.get(day, 0) + 1
        raw_settings = view.get("settings") if isinstance(view.get("settings"), dict) else {}
        settings = {key: clean_text(str(value), 120) for key, value in raw_settings.items() if key in allowed_settings}
        event = AnalyticsEvent(
            event_type=AnalyticsEvent.OFFICE_VIEW,
            service_type=service_type,
            office=office,
            office_date=parse_office_date(view.get("office_date")),
            client_id=client_id,
            platform=platform,
            browser=browser[:50],
            os=os_family[:50],
            translation=clean_text(view.get("translation"), 20),
            settings=settings,
            offline=True,
            view_id=view_id,
        )
        events.append((event, viewed_at))
        if len(events) >= room:
            break

    if not events:
        return 0
    with transaction.atomic():
        created = AnalyticsEvent.objects.bulk_create([event for event, _ in events])
        # ``created`` is auto_now_add, so set the viewing time afterwards, in
        # one query (bulk_update leaves auto_now_add alone).
        for event, (_, viewed_at) in zip(created, events):
            event.created = viewed_at
        AnalyticsEvent.objects.bulk_update(created, ["created"])
    # Memcached adds atomically; the key lasts the day it counts.
    cache.add(ip_key, 0, timeout=24 * 3600)
    try:
        cache.incr(ip_key, len(created))
    except ValueError:
        # Gone between the two calls (evicted): start again from these.
        cache.set(ip_key, len(created), timeout=24 * 3600)
    return len(created)

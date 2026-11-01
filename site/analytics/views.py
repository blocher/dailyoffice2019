import datetime

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from analytics.middleware import OFFICE_VIEW_URL_NAMES
from analytics.models import AnalyticsEvent
from analytics.utils import known_setting_names, parse_client_meta, parse_office_date


def clean_text(value, length):
    """A client-sent string, trimmed and cut to ``length``; anything else is ``""``."""
    return value.strip()[:length] if isinstance(value, str) else ""


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


class AnalyticsEventThrottle(AnonRateThrottle):
    scope = "analytics_event"


class AnalyticsEventView(APIView):
    """Public, throttled ingest for client-confirmed events.

    Only ``audio_play`` is accepted here; ``office_view`` and ``audio_loaded``
    are generated server-side so they cannot be spoofed or inflated by clients.
    (Office views prayed offline come in through ``OfflineOfficeViewsView``,
    which caps them per device and day.)
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnalyticsEventThrottle]

    ALLOWED_EVENT_TYPES = {AnalyticsEvent.AUDIO_PLAY}

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}

        event_type = data.get("event_type")
        if event_type not in self.ALLOWED_EVENT_TYPES:
            return Response({"detail": "Unsupported event_type."}, status=400)

        platform, browser, os_family = parse_client_meta(
            request, declared_platform=clean_text(data.get("platform"), 20)
        )
        client_id = clean_text(data.get("client_id"), 64) or clean_text(request.headers.get("X-Client-Id"), 64)

        AnalyticsEvent.objects.create(
            event_type=event_type,
            service_type=clean_text(data.get("service_type"), 20),
            office=clean_text(data.get("office"), 50),
            office_date=parse_office_date(data.get("office_date")),
            client_id=client_id,
            platform=platform,
            browser=browser[:50],
            os=os_family[:50],
            translation=clean_text(data.get("translation"), 20),
        )
        return Response(status=204)


class OfflineOfficeViewsThrottle(AnonRateThrottle):
    scope = "analytics_offline_views"


class OfflineOfficeViewsView(APIView):
    """Office views prayed offline, reported in a batch once the app is back online.

    The app keeps days of offices on the device. Opening one offline makes no
    request, so the middleware can't count it; the app queues the view and
    posts it here later:

        {"client_id": "...", "platform": "ios", "views": [
            {"service_type": "office", "office": "morning_prayer", "office_date": "2026-11-02",
             "translation": "esv", "viewed_at": "2026-11-02T07:14:00Z", "settings": {...}}, ...]}

    Views are stored with ``offline=True`` and ``created`` set to when they
    were viewed (within the last 60 days). At most 100 per request; views that
    don't name a known office are skipped. Anyone can post here, so views
    need a ``client_id`` and each device counts at most ``MAX_PER_DAY`` a day
    (eight offices, each opened twice); the rest are skipped. Skipped views
    still get a 200, so the app lets them go. A ``view_id`` already stored
    (a batch sent again after its answer was lost) is skipped too.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OfflineOfficeViewsThrottle]

    MAX_VIEWS = 100
    MAX_PER_DAY = 16
    MAX_AGE = datetime.timedelta(days=60)

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        views = data.get("views")
        if not isinstance(views, list):
            return Response({"detail": "views must be a list."}, status=400)

        platform, browser, os_family = parse_client_meta(
            request, declared_platform=clean_text(data.get("platform"), 20)
        )
        client_id = clean_text(data.get("client_id"), 64) or clean_text(request.headers.get("X-Client-Id"), 64)
        if not client_id:
            return Response({"accepted": 0}, status=200)
        allowed_settings = known_setting_names()
        known_offices = set(OFFICE_VIEW_URL_NAMES.values())
        now = timezone.now()
        # Views already counted for this device, by day.
        counted = (
            AnalyticsEvent.objects.filter(client_id=client_id, offline=True, created__gte=now - self.MAX_AGE)
            .annotate(day=TruncDate("created"))
            .values("day")
            .annotate(count=Count("id"))
        )
        per_day = {row["day"]: row["count"] for row in counted}
        view_ids = [clean_text(view.get("view_id"), 40) for view in views[: self.MAX_VIEWS] if isinstance(view, dict)]
        seen = set(
            AnalyticsEvent.objects.filter(view_id__in=[v for v in view_ids if v]).values_list("view_id", flat=True)
        )

        events = []
        for view in views[: self.MAX_VIEWS]:
            if not isinstance(view, dict):
                continue
            service_type = str(view.get("service_type") or "")
            office = str(view.get("office") or "")
            if (service_type, office) not in known_offices:
                continue
            view_id = clean_text(view.get("view_id"), 40)
            if view_id and view_id in seen:
                continue
            if view_id:
                seen.add(view_id)
            viewed_at = parse_viewed_at(view.get("viewed_at"), now)
            viewed_at = min(max(viewed_at, now - self.MAX_AGE), now)
            day = timezone.localdate(viewed_at)
            if per_day.get(day, 0) >= self.MAX_PER_DAY:
                continue
            per_day[day] = per_day.get(day, 0) + 1
            raw_settings = view.get("settings") if isinstance(view.get("settings"), dict) else {}
            settings = {
                str(key)[:60]: str(value)[:120] for key, value in raw_settings.items() if key in allowed_settings
            }
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

        created = AnalyticsEvent.objects.bulk_create([event for event, _ in events])
        # ``created`` is auto_now_add, so set the viewing time afterwards, in
        # one query (bulk_update leaves auto_now_add alone).
        for event, (_, viewed_at) in zip(created, events):
            event.created = viewed_at
        AnalyticsEvent.objects.bulk_update(created, ["created"])
        return Response({"accepted": len(created)}, status=200)

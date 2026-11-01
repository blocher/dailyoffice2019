import datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from analytics.middleware import OFFICE_VIEW_URL_NAMES
from analytics.models import AnalyticsEvent
from analytics.utils import known_setting_names, parse_client_meta, parse_office_date


class AnalyticsEventThrottle(AnonRateThrottle):
    scope = "analytics_event"


class AnalyticsEventView(APIView):
    """Public, throttled ingest for client-confirmed events.

    Only ``audio_play`` is accepted here; ``office_view`` and ``audio_loaded``
    are generated server-side so they cannot be spoofed or inflated by clients.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnalyticsEventThrottle]

    ALLOWED_EVENT_TYPES = {AnalyticsEvent.AUDIO_PLAY}

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}

        event_type = data.get("event_type")
        if event_type not in self.ALLOWED_EVENT_TYPES:
            return Response({"detail": "Unsupported event_type."}, status=400)

        platform, browser, os_family = parse_client_meta(request, declared_platform=data.get("platform"))
        client_id = (data.get("client_id") or request.headers.get("X-Client-Id") or "").strip()

        AnalyticsEvent.objects.create(
            event_type=event_type,
            service_type=(data.get("service_type") or "")[:20],
            office=(data.get("office") or "")[:50],
            office_date=parse_office_date(data.get("office_date")),
            client_id=client_id[:64],
            platform=platform,
            browser=browser[:50],
            os=os_family[:50],
            translation=(data.get("translation") or "")[:20],
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
    don't name a known office are skipped.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OfflineOfficeViewsThrottle]

    MAX_VIEWS = 100
    MAX_AGE = datetime.timedelta(days=60)

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        views = data.get("views")
        if not isinstance(views, list):
            return Response({"detail": "views must be a list."}, status=400)

        platform, browser, os_family = parse_client_meta(request, declared_platform=data.get("platform"))
        client_id = (data.get("client_id") or request.headers.get("X-Client-Id") or "").strip()[:64]
        allowed_settings = known_setting_names()
        known_offices = set(OFFICE_VIEW_URL_NAMES.values())
        now = timezone.now()

        events = []
        for view in views[: self.MAX_VIEWS]:
            if not isinstance(view, dict):
                continue
            service_type = str(view.get("service_type") or "")
            office = str(view.get("office") or "")
            if (service_type, office) not in known_offices:
                continue
            viewed_at = parse_datetime(str(view.get("viewed_at") or "")) or now
            if timezone.is_naive(viewed_at):
                viewed_at = timezone.make_aware(viewed_at, datetime.timezone.utc)
            viewed_at = min(max(viewed_at, now - self.MAX_AGE), now)
            raw_settings = view.get("settings") if isinstance(view.get("settings"), dict) else {}
            settings = {
                str(key)[:60]: str(value)[:120] for key, value in raw_settings.items() if key in allowed_settings
            }
            events.append(
                (
                    AnalyticsEvent(
                        event_type=AnalyticsEvent.OFFICE_VIEW,
                        service_type=service_type,
                        office=office,
                        office_date=parse_office_date(view.get("office_date")),
                        client_id=client_id,
                        platform=platform,
                        browser=browser[:50],
                        os=os_family[:50],
                        translation=str(view.get("translation") or "")[:20],
                        settings=settings,
                        offline=True,
                    ),
                    viewed_at,
                )
            )

        created = AnalyticsEvent.objects.bulk_create([event for event, _ in events])
        # ``created`` is auto_now_add, so set the viewing time afterwards.
        for event, (_, viewed_at) in zip(created, events):
            AnalyticsEvent.objects.filter(pk=event.pk).update(created=viewed_at)
        return Response({"accepted": len(created)}, status=200)

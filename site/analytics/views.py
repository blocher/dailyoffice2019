from django.db import IntegrityError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from analytics import offline_views
from analytics.models import AnalyticsEvent
from analytics.utils import clean_text, parse_client_meta, parse_office_date


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
    posts it here later. See ``analytics.offline_views`` for the payload and
    the rules that keep it honest.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OfflineOfficeViewsThrottle]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        views = data.get("views")
        if not isinstance(views, list):
            return Response({"detail": "views must be a list."}, status=400)

        platform, browser, os_family = parse_client_meta(
            request, declared_platform=clean_text(data.get("platform"), 20)
        )
        client_id = clean_text(data.get("client_id"), 64) or clean_text(request.headers.get("X-Client-Id"), 64)
        try:
            accepted = offline_views.record(
                views, client_id=client_id, platform=platform, browser=browser, os_family=os_family
            )
        except IntegrityError:
            # Another request stored some of these views at the same moment
            # (two tabs back online together). The app sends the batch again
            # later and the views already stored are skipped.
            return Response({"detail": "Try again."}, status=503)
        return Response({"accepted": accepted}, status=200)

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from analytics.models import AnalyticsEvent
from analytics.utils import parse_client_meta, parse_office_date


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

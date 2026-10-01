from analytics.models import AnalyticsEvent
from analytics.utils import known_setting_names, office_date_from_kwargs, parse_client_meta

# Canonical office/family view names mapped to (service_type, office). The
# duplicate ".../audio" routes are intentionally excluded: they are only hit
# alongside include_audio_links and would double-count a view.
OFFICE_VIEW_URL_NAMES = {
    "morning_prayer_view": (AnalyticsEvent.SERVICE_OFFICE, "morning_prayer"),
    "evening_prayer_view": (AnalyticsEvent.SERVICE_OFFICE, "evening_prayer"),
    "midday_view": (AnalyticsEvent.SERVICE_OFFICE, "midday_prayer"),
    "compline_view": (AnalyticsEvent.SERVICE_OFFICE, "compline"),
    "family_morning_prayer_view": (AnalyticsEvent.SERVICE_FAMILY, "morning_prayer"),
    "family_early_evening_prayer_view": (AnalyticsEvent.SERVICE_FAMILY, "early_evening_prayer"),
    "family_midday_view": (AnalyticsEvent.SERVICE_FAMILY, "midday_prayer"),
    "family_close_of_day_view": (AnalyticsEvent.SERVICE_FAMILY, "close_of_day_prayer"),
}


class AnalyticsMiddleware:
    """Records one ``office_view`` per office API request, for every app version.

    Logging is best-effort and wrapped so it can never affect the response.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._maybe_log_office_view(request, response)
        except Exception:
            pass
        return response

    @staticmethod
    def _maybe_log_office_view(request, response):
        if request.method != "GET":
            return
        if getattr(response, "status_code", 0) // 100 != 2:
            return

        match = getattr(request, "resolver_match", None)
        if match is None or match.url_name not in OFFICE_VIEW_URL_NAMES:
            return

        # The second request per office (audio metadata) carries this flag;
        # skip it so we count exactly one view per office load.
        if request.GET.get("include_audio_links"):
            return

        service_type, office = OFFICE_VIEW_URL_NAMES[match.url_name]
        platform, browser, os_family = parse_client_meta(request)
        client_id = (request.headers.get("X-Client-Id") or "").strip()

        # Snapshot the chosen settings (only recognized keys) so the dashboard
        # can show the most common value per setting.
        allowed = known_setting_names()
        settings = {str(key)[:60]: str(value)[:120] for key, value in request.GET.items() if key in allowed}

        AnalyticsEvent.objects.create(
            event_type=AnalyticsEvent.OFFICE_VIEW,
            service_type=service_type,
            office=office,
            office_date=office_date_from_kwargs(match.kwargs),
            client_id=client_id[:64],
            platform=platform,
            browser=browser[:50],
            os=os_family[:50],
            translation=(request.GET.get("bible_translation") or "")[:20],
            settings=settings,
        )

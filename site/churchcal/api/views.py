from calendar import monthrange

from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear


class DayView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        date = timezone.now().replace(year=year, month=month, day=day)
        calendar_date = get_calendar_date(date)
        serializer = DaySerializer(calendar_date)
        return Response(serializer.data)


class MonthView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year):
        church_year = cache.get(str(year))
        if not church_year:
            church_year = ChurchYear(year)
            cache.set(str(year), church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year.date.m], many=True)
        return Response(serializer.data)


class YearView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year):
        church_year = cache.get(str(year))
        if not church_year:
            church_year = ChurchYear(year)
            cache.set(str(year), church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year], many=True)
        return Response(serializer.data)


class Settings(object):

    DEFAULT_SETTINGS = {
        "setting_psalter": "60",
        "setting_reading_cycle": "1",
        "setting_reading_length": "full",
        "setting_reading_audio": "off",
        "setting_canticle_rotation": "default",
        "setting_theme": "theme-auto",
        "setting_lectionary": "daily-office-readings",
        "setting_confession": "long-on-fast",
        "setting_absolution": "lay",
        "setting_morning_prayer_invitatory": "invitatory_traditional",
        "setting_reading_headings": "off",
        "setting_language_style": "traditional",
        "setting_national_holidays": "all",
        "setting_suffrages": "rotating",
        "setting_collects": "rotating",
        "setting_pandemic_prayers": "pandemic_yes",
        "setting_mp_great_litany": "mp_litany_off",
        "setting_ep_great_litany": "ep_litany_off",
        "setting_general_thanksgiving": "on",
        "setting_chrysostom": "on",
        "setting_grace": "rotating",
        "setting_o_antiphons": "literal",
    }

    def __init__(self, request):
        self.settings = self._get_settings(request)

    def get_setting(self, name):
        name = name.lower()
        try:
            return self.settings[name]
        except KeyError:
            return False

    def __getitem__(self, key):
        key = key.lower()
        try:
            return self.settings[key]
        except KeyError:
            return False

    def _get_settings(self, request):

        settings = self.DEFAULT_SETTINGS
        specified_settings = {k: v for (k, v) in request.query_params.items() if k in settings.keys()}
        for k, v in settings.items():
            if k in specified_settings.keys():
                settings[k] = specified_settings[k]
        return settings


class OfficeAPIView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        settings = Settings(request)
        return HttpResponse()


class MorningPrayer(OfficeAPIView):
    def get(self, request, year, month, day):
        return super().get(request, year, month, day)

from calendar import monthrange

from django.core.cache import cache
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

    def get(self, request, year, month):
        dayrange = monthrange(year, month)
        days = [
            get_calendar_date(timezone.now().replace(year=year, month=month, day=day))
            for day in range(1, dayrange[1] + 1)
        ]
        serializer = DaySerializer(days, many=True)
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

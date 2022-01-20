from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear, CalendarYear


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
        year = int(year)
        year_string = "calendar_{}".format(year)
        calendar_year = cache.get(year_string)
        if not calendar_year:
            calendar_year = CalendarYear(year)
            cache.set(year_string, calendar_year, 60 * 60 * 12)
        serializer = DaySerializer(
            [date for date in calendar_year if date.date.month == month and date.date.year == year], many=True
        )
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

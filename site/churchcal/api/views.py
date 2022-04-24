from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear, CalendarYear


def get_calendar_year(year):
    year = int(year)
    first_year = year - 1
    second_year = year
    first_church_year = cache.get(str(first_year))
    if not first_church_year:
        first_church_year = ChurchYear(first_year)
        cache.set(str(first_year), first_church_year, 60 * 60 * 12)
    second_church_year = cache.get(str(second_year))
    if not second_church_year:
        second_church_year = ChurchYear(second_year)
        cache.set(str(second_year), second_church_year, 60 * 60 * 12)
    return CalendarYear(year, first_church_year, second_church_year)


class DayView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month, day):
        try:
            date = timezone.now().replace(year=year, month=month, day=day)
        except ValueError:
            return Response(status=404)
        calendar_date = get_calendar_date(date)
        serializer = DaySerializer(calendar_date)
        return Response(serializer.data)


class MonthView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year, month):
        calendar_year = get_calendar_year(year)
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

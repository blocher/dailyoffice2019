import os

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import FileResponse
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from mutagen.mp3 import MP3
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear, CalendarYear
from website import settings


def get_calendar_year(year, calendar):
    year = int(year)
    first_year = year - 1
    second_year = year
    print(calendar)
    first_church_year = cache.get(f"{first_year}_{calendar}") if settings.USE_CALENDAR_CACHE else None
    if not first_church_year:
        first_church_year = ChurchYear(first_year, calendar)
        cache.set(f"{first_year}_{calendar}", first_church_year, 60 * 60 * 12)
    second_church_year = cache.get(f"{second_year}_{calendar}") if settings.USE_CALENDAR_CACHE else None
    if not second_church_year:
        second_church_year = ChurchYear(second_year, calendar)
    cache.set(f"{second_year}_{calendar}", second_church_year, 60 * 60 * 12)
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
        calendar_year = get_calendar_year(year, request.GET.get("calendar", "ACNA_BCP2019"))
        serializer = DaySerializer(
            [date for date in calendar_year if date.date.month == month and date.date.year == year], many=True
        )
        return Response(serializer.data)


class YearView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, year):
        calendar = request.GET.get("calendar", "ACNA_BCP2019")
        church_year = cache.get(f"{year}_{calendar}") if settings.USE_CALENDAR_CACHE else None
        if not church_year:
            church_year = ChurchYear(year, calendar)
            cache.set(f"{year}_{calendar}", church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year], many=True)
        return Response(serializer.data)


class AudioTrackView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        filename = kwargs["track"]
        
        # Use Django storage instead of direct filesystem access
        if not default_storage.exists(filename):
            return HttpResponseNotFound("Audio file not found.")

        try:
            # For getting metadata, we need to open the file temporarily
            with default_storage.open(filename, "rb") as file:
                audio = MP3(file)
                duration = int(audio.info.length)  # Duration in seconds
        except Exception:
            duration = "Unknown"  # Fallback if metadata cannot be read

        # Get file size
        file_size = default_storage.size(filename)
        
        # Handle Range header
        range_header = request.headers.get("Range")
        if range_header:
            # Extract the range value
            range_start, range_end = range_header.replace("bytes=", "").split("-")
            range_start = int(range_start)
            range_end = int(range_end) if range_end else file_size - 1

            # Ensure range is valid
            range_end = min(range_end, file_size - 1)
            content_length = range_end - range_start + 1

            # Open file and read the range
            with default_storage.open(filename, "rb") as audio_file:
                audio_file.seek(range_start)
                audio_data = audio_file.read(content_length)

            response = HttpResponse(audio_data, status=206, content_type="audio/mpeg")
            response["Content-Range"] = f"bytes {range_start}-{range_end}/{file_size}"
            response["Content-Length"] = str(content_length)
        else:
            # Serve the full file if no Range header is present
            audio_file = default_storage.open(filename, "rb")
            response = FileResponse(audio_file, content_type="audio/mpeg")
            response["Content-Length"] = str(file_size)

        # Set Content-Disposition for inline playback
        response["Content-Disposition"] = f'inline; filename="{filename}"'

        # Metadata (Adjust these as needed)
        response["X-Audio-Title"] = "The Daily Office"
        response["X-Audio-Year"] = "2025"
        response["X-Audio-Duration"] = str(duration)  # Add duration in seconds

        return response

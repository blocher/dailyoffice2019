import os

from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import StreamingHttpResponse
from django.utils import timezone
from mutagen.mp3 import MP3
from rest_framework.renderers import BaseRenderer, BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from churchcal.api.permissions import ReadOnly
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date, ChurchYear, CalendarYear
from churchcal.calendar_feeds import (
    ChurchCalendarFeedService,
    get_calendar_feed_filename,
    get_feed_scope_label,
)
from website import settings as site_settings


class CalendarFeedRenderer(BaseRenderer):
    media_type = "text/calendar"
    format = "ics"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        return str(data).encode(self.charset)


def get_calendar_year(year, calendar):
    year = int(year)
    first_year = year - 1
    second_year = year
    print(calendar)
    first_church_year = cache.get(f"{first_year}_{calendar}") if site_settings.USE_CALENDAR_CACHE else None
    if not first_church_year:
        first_church_year = ChurchYear(first_year, calendar)
        cache.set(f"{first_year}_{calendar}", first_church_year, 60 * 60 * 12)
    second_church_year = cache.get(f"{second_year}_{calendar}") if site_settings.USE_CALENDAR_CACHE else None
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
        church_year = cache.get(f"{year}_{calendar}") if site_settings.USE_CALENDAR_CACHE else None
        if not church_year:
            church_year = ChurchYear(year, calendar)
            cache.set(f"{year}_{calendar}", church_year, 60 * 60 * 12)
        serializer = DaySerializer([date for date in church_year], many=True)
        return Response(serializer.data)


class CalendarFeedView(APIView):
    permission_classes = [ReadOnly]
    renderer_classes = [CalendarFeedRenderer, JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, scope, canceled=False):
        try:
            feed_path = ChurchCalendarFeedService.get_feed_path(scope, canceled=canceled)
            get_feed_scope_label(scope)
        except ValueError:
            return Response(status=404)

        response = FileResponse(open(feed_path, "rb"), content_type="text/calendar; charset=utf-8")
        disposition = "attachment" if request.GET.get("download") == "1" else "inline"
        response["Content-Disposition"] = (
            f'{disposition}; filename="{get_calendar_feed_filename(scope, canceled=canceled)}"'
        )
        return response


class AudioTrackView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        filename = kwargs["track"]
        # `track` may include a provider subfolder (e.g. "fish/<uuid>.mp3").
        # Normalize and confine to MEDIA_ROOT to prevent path traversal.
        safe_rel = os.path.normpath(filename).lstrip("/\\")
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        file_path = os.path.abspath(os.path.join(media_root, safe_rel))

        if os.path.commonpath([media_root, file_path]) != media_root:
            return HttpResponseNotFound("Audio file not found.")

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return HttpResponseNotFound("Audio file not found.")

        try:
            audio = MP3(file_path)
            duration = int(audio.info.length)  # Duration in seconds
        except Exception:
            duration = "Unknown"  # Fallback if metadata cannot be read

        file_size = os.path.getsize(file_path)
        range_header = request.META.get("HTTP_RANGE", "").strip()
        start, end = self._parse_range(range_header, file_size)

        if start is not None:
            # Partial content: browsers require this to seek/"Jump To". We stream
            # only the requested byte window and advertise the range so the
            # <audio> element can map a timestamp to a byte offset.
            length = end - start + 1
            response = StreamingHttpResponse(
                self._iter_file(file_path, start, length),
                status=206,
                content_type="audio/mpeg",
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Length"] = str(length)
        else:
            response = FileResponse(open(file_path, "rb"), content_type="audio/mpeg")
            response["Content-Length"] = str(file_size)

        # Advertise range support on every response so the client knows it can seek.
        response["Accept-Ranges"] = "bytes"

        # Set Content-Disposition for inline playback
        response["Content-Disposition"] = f'inline; filename="{filename}"'

        # Metadata (Adjust these as needed)
        response["X-Audio-Title"] = "The Daily Office"
        response["X-Audio-Year"] = "2025"
        response["X-Audio-Duration"] = str(duration)  # Add duration in seconds

        return response

    @staticmethod
    def _parse_range(range_header, file_size):
        """Parse a single-range "bytes=start-end" header.

        Returns (start, end) inclusive byte offsets, or (None, None) when there
        is no usable range so the caller serves the full file.
        """
        if not range_header.startswith("bytes="):
            return None, None
        spec = range_header[len("bytes=") :].split(",")[0].strip()
        if "-" not in spec:
            return None, None
        start_str, end_str = spec.split("-", 1)
        try:
            if start_str:
                start = int(start_str)
                end = int(end_str) if end_str else file_size - 1
            else:
                # Suffix range: last N bytes.
                if not end_str:
                    return None, None
                length = int(end_str)
                start = max(file_size - length, 0)
                end = file_size - 1
        except ValueError:
            return None, None
        if start > end or start >= file_size:
            return None, None
        end = min(end, file_size - 1)
        return start, end

    @staticmethod
    def _iter_file(file_path, start, length, chunk_size=8192):
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

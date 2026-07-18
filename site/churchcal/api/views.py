import os

from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, StreamingHttpResponse
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
    """Serve office audio with HTTP Range support so the browser can Jump To / seek."""

    permission_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        filename = kwargs["track"]
        # Allow nested paths under MEDIA_ROOT (e.g. audio_v2/full/....mp3); block traversal.
        safe_name = os.path.normpath(filename).lstrip(os.sep)
        if safe_name.startswith("..") or "/../" in f"/{safe_name}/":
            return HttpResponseNotFound("Audio file not found.")
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        file_path = os.path.abspath(os.path.join(media_root, safe_name))
        if not file_path.startswith(media_root + os.sep) and file_path != media_root:
            return HttpResponseNotFound("Audio file not found.")

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return HttpResponseNotFound("Audio file not found.")

        file_size = os.path.getsize(file_path)
        try:
            audio = MP3(file_path)
            duration = int(audio.info.length)
        except Exception:
            duration = "Unknown"

        range_header = request.META.get("HTTP_RANGE", "").strip()
        start, end = 0, file_size - 1
        status = 200
        if range_header.startswith("bytes="):
            try:
                unit_range = range_header.split("=", 1)[1]
                # Only honor a single range; multi-range is uncommon for <audio>.
                unit_range = unit_range.split(",", 1)[0].strip()
                start_s, sep, end_s = unit_range.partition("-")
                if not sep:
                    raise ValueError("malformed range")
                if start_s == "" and end_s:
                    # Suffix range "bytes=-N": the final N bytes of the file.
                    suffix = int(end_s)
                    if suffix <= 0:
                        raise ValueError("empty suffix range")
                    start = max(file_size - suffix, 0)
                    end = file_size - 1
                else:
                    if start_s:
                        start = int(start_s)
                    if end_s:
                        end = int(end_s)
                end = min(end, file_size - 1)
                if start < 0 or start > end or start >= file_size:
                    response = HttpResponse(status=416)
                    response["Content-Range"] = f"bytes */{file_size}"
                    return response
                status = 206
            except ValueError:
                start, end = 0, file_size - 1
                status = 200

        length = end - start + 1

        def _iter_file_range(path, offset, nbytes, block_size=64 * 1024):
            with open(path, "rb") as handle:
                handle.seek(offset)
                remaining = nbytes
                while remaining > 0:
                    chunk = handle.read(min(block_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        response = StreamingHttpResponse(
            _iter_file_range(file_path, start, length),
            status=status,
            content_type="audio/mpeg",
        )
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(length)
        response["Content-Disposition"] = f'inline; filename="{os.path.basename(safe_name)}"'
        response["X-Audio-Title"] = "The Daily Office"
        response["X-Audio-Year"] = "2025"
        response["X-Audio-Duration"] = str(duration)
        if status == 206:
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        return response

"""Build podcast episodes from the office audio.

An episode is the office's own combined track (the file the in-app player
plays), rendered by the real API view with the feed's fixed settings, then
*copied* into the permanent archive under ``MEDIA_ROOT/podcasts/`` (re-encoded
at the podcast bitrate) with ID3 tags and chapters. The combined track itself stays a disposable cache; the
copy is what the feed links to, and nothing ever deletes or rewrites it (see
``office/audio_retention.py``).

Building is offline only: the daily ``build_podcast_episodes`` cron job (and
manual backfills) call it, never a web request.
"""

import fcntl
import json
import logging
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.test import RequestFactory
from django.urls import resolve
from mutagen.id3 import APIC, CHAP, COMM, CTOC, CTOCFlags, ID3, TALB, TCON, TDRC, TIT2, TPE1, TPE2, WOAR, WXXX
from mutagen.mp3 import MP3

from churchcal.calculations import get_calendar_date
from office.api.views.index import AUDIO_GENERATION_REQUIRED
from office.audio_retention import podcast_media_root
from office.readings_audio import has_proper_eucharist
from podcasts import episodes
from podcasts.catalog import AUTHOR
from podcasts.models import PodcastEpisode

logger = logging.getLogger(__name__)

ARTWORK_DIR = Path(__file__).parent / "artwork"


class EpisodeBuildError(Exception):
    pass


def episode_filename(feed, day):
    """Path of the episode under the podcast archive. Public; never change it."""
    return f"{feed.slug}/{day.year}/{feed.slug}-{day:%Y-%m-%d}.mp3"


def episode_path(filename):
    return os.path.join(podcast_media_root(), filename)


@contextmanager
def build_lock():
    """One builder at a time (cron and a manual backfill must not overlap)."""
    os.makedirs(podcast_media_root(), exist_ok=True)
    with open(os.path.join(podcast_media_root(), ".build.lock"), "a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise EpisodeBuildError("Another podcast build is running.") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def is_publishable(feed, calendar_date):
    return not feed.proper_days_only or has_proper_eucharist(calendar_date)


def render_office_audio(feed, day):
    """Run the office (or readings) API view with audio generation allowed.

    Returns the parsed JSON: ``modules`` and ``audio``. Raises when the audio
    could not be produced; the next run tries again.
    """
    path = f"{feed.api_path}/{day:%Y-%m-%d}"
    request = RequestFactory().get(path, data=feed.api_query())
    # Trusted, in-process: generate inline and skip the web date window.
    request._audio_prewarm = True
    match = resolve(path)
    token = AUDIO_GENERATION_REQUIRED.set(True)
    try:
        response = match.func(request, *match.args, **match.kwargs)
        if hasattr(response, "render") and callable(response.render):
            response = response.render()
    finally:
        AUDIO_GENERATION_REQUIRED.reset(token)
    if response.status_code != 200:
        raise EpisodeBuildError(f"{path} returned HTTP {response.status_code}.")
    data = json.loads(response.content)
    single_track = (data.get("audio") or {}).get("single_track")
    if not single_track:
        raise EpisodeBuildError(f"{path} produced no audio track.")
    return data


def source_track_path(single_track):
    media_path = single_track[1]
    relative = media_path.removeprefix(settings.MEDIA_URL).lstrip("/")
    path = os.path.join(settings.MEDIA_ROOT, relative)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise EpisodeBuildError(f"Combined track {relative} is missing.")
    return path


def artwork_bytes(feed):
    for name in (f"{feed.slug}-600.jpg", f"{feed.slug}.jpg"):
        path = ARTWORK_DIR / name
        if path.is_file():
            return path.read_bytes()
    return None


def tag_episode(path, feed, day, title, summary, follow, chapters, duration):
    """ID3v2.3 tags for apps that read the file itself, with chapters."""
    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TPE1(encoding=3, text=AUTHOR))
    tags.add(TPE2(encoding=3, text=AUTHOR))
    tags.add(TALB(encoding=3, text=feed.title))
    tags.add(TDRC(encoding=3, text=day.isoformat()))
    tags.add(TCON(encoding=3, text="Podcast"))
    tags.add(COMM(encoding=3, lang="eng", desc="", text=summary))
    tags.add(WOAR(url=follow))
    tags.add(WXXX(encoding=3, desc="Pray along", url=follow))
    artwork = artwork_bytes(feed)
    if artwork:
        tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=artwork))
    if chapters:
        ids = [f"chp{index}" for index in range(len(chapters))]
        tags.add(CTOC(element_id="toc", flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED, child_element_ids=ids))
        for index, chapter in enumerate(chapters):
            start = int(chapter["startTime"] * 1000)
            end = int((chapters[index + 1]["startTime"] if index + 1 < len(chapters) else duration) * 1000)
            tags.add(
                CHAP(
                    element_id=ids[index],
                    start_time=start,
                    end_time=max(end, start),
                    sub_frames=[TIT2(encoding=3, text=chapter["title"])],
                )
            )
    # Replacing every frame also drops ffmpeg's "Lavf" encoder tag (TSSE),
    # which is how cleanup_full_audio_files recognises disposable tracks.
    tags.save(path, v2_version=3)


def encode(source, target):
    """Re-encode the 160k combined track at the podcast bitrate (speech needs far less)."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", source,
            "-map", "0:a", "-c:a", "libmp3lame", "-b:a", getattr(settings, "PODCAST_BITRATE", "96k"),
            "-ac", "1", "-f", "mp3", target,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )  # fmt: skip
    if result.returncode != 0:
        raise EpisodeBuildError(f"ffmpeg could not encode {source}: {(result.stderr or '')[-500:]}")


def copy_into_archive(source, target, **tag_arguments):
    """Encode, tag, and atomically publish the episode file; return its duration."""
    os.makedirs(os.path.dirname(target), exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=os.path.dirname(target), suffix=".part")
    os.close(handle)
    try:
        encode(source, temporary)
        duration = MP3(temporary).info.length
        if not duration:
            raise EpisodeBuildError(f"{source} has no readable duration.")
        tag_episode(temporary, duration=duration, **tag_arguments)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
        return duration
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_episode(feed, day):
    """Build and record ``feed``'s episode for ``day``.

    Returns the episode (existing or new), or None when the feed has nothing to
    publish that day. An existing episode is never rebuilt.
    """
    existing = PodcastEpisode.objects.filter(feed_slug=feed.slug, date=day).first()
    if existing:
        return existing
    calendar_date = get_calendar_date(day.strftime("%Y-%m-%d"))
    if not is_publishable(feed, calendar_date):
        return None

    data = render_office_audio(feed, day)
    single_track = data["audio"]["single_track"]
    source = source_track_path(single_track)
    title = episodes.episode_title(feed, day, calendar_date)
    summary, description = episodes.show_notes(feed, day, calendar_date, data.get("modules"))
    chapters = episodes.chapters(single_track[2] if len(single_track) > 2 else [])
    follow = feed.follow_along_url(day)
    filename = episode_filename(feed, day)
    target = episode_path(filename)
    if PodcastEpisode.objects.filter(filename=filename).exists():
        raise EpisodeBuildError(f"{filename} already belongs to another episode.")
    duration = copy_into_archive(
        source,
        target,
        feed=feed,
        day=day,
        title=title,
        summary=summary,
        follow=follow,
        chapters=chapters,
    )
    return PodcastEpisode.objects.create(
        feed_slug=feed.slug,
        date=day,
        title=title,
        summary=summary,
        description_html=description,
        filename=filename,
        file_size=os.path.getsize(target),
        duration=duration,
        chapters=chapters,
        follow_along_url=follow,
        guid=f"dailyoffice2019-{feed.slug}-{day:%Y-%m-%d}",
        published_at=episodes.published_at(day),
    )

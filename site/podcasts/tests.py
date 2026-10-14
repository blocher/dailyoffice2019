import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone as dt_timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from mutagen.id3 import ID3

from office.audio_retention import is_permanent
from office.readings_audio import KINDS, first_per_reading_number, spoken_psalm
from podcasts import builder, catalog, episodes, rss
from podcasts.models import PodcastEpisode

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def make_mp3(path, seconds=2):
    """A real mp3 written by ffmpeg, so it carries the 'Lavf' encoder tag."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-f", "lavfi",
            "-i", "anullsrc=r=24000:cl=mono", "-t", str(seconds),
            "-c:a", "libmp3lame", "-b:a", "32k", str(path),
        ],
        check=True,
    )  # fmt: skip
    return path


class MediaRootMixin:
    def use_temporary_media_root(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        override = override_settings(MEDIA_ROOT=str(self.root) + "/", MEDIA_URL="/uploads/")
        override.enable()
        self.addCleanup(override.disable)


class CatalogTests(SimpleTestCase):
    def test_eighteen_feeds_with_unique_slugs(self):
        self.assertEqual(len(catalog.FEEDS), 18)
        self.assertEqual(len(catalog.FEEDS_BY_SLUG), 18)

    def test_offices_have_traditional_language_twins(self):
        offices = [feed for feed in catalog.FEEDS if not feed.is_readings]
        self.assertEqual(len(offices), 16)
        for feed in offices:
            if feed.style == catalog.TRADITIONAL:
                twin = catalog.get_feed(feed.slug.removesuffix("-traditional"))
                self.assertEqual(feed.title, f"{twin.title} (Traditional Language)")
                self.assertEqual(feed.service, twin.service)
        titles = {feed.title for feed in offices}
        self.assertTrue({"Morning Prayer", "Evening Prayer", "Midday Prayer", "Compline"} <= titles)
        self.assertIn("Morning Prayer (Traditional Language)", titles)

    def test_settings_match_the_requested_share_links(self):
        contemporary = catalog.get_feed("morning-prayer").settings
        traditional = catalog.get_feed("morning-prayer-traditional").settings
        self.assertEqual(contemporary["bible_translation"], "esv")
        self.assertEqual(contemporary["mp_great_litany"], "mp_litany_w_f_s")
        self.assertEqual(contemporary["language_style_for_our_father"], "traditional")
        changed = {key for key in contemporary if contemporary[key] != traditional[key]}
        self.assertEqual(changed, {"language_style", "psalm_translation", "bible_translation"})
        self.assertEqual(traditional["bible_translation"], "kjv")

    def test_follow_along_link_opens_the_office_with_the_feeds_settings(self):
        url = catalog.get_feed("family-close-of-day-prayer-traditional").follow_along_url(date(2026, 10, 13))
        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, "www.dailyoffice2019.com")
        self.assertEqual(parsed.path, "/family/close_of_day_prayer/2026/10/13")
        self.assertEqual(parse_qs(parsed.query)["language_style"], ["traditional"])
        office = urlparse(catalog.get_feed("compline").follow_along_url(date(2026, 1, 2)))
        self.assertEqual(office.path, "/compline/2026/1/2")

    def test_readings_feeds(self):
        daily = catalog.get_feed("daily-office-readings")
        eucharist = catalog.get_feed("holy-eucharist-readings")
        self.assertEqual(daily.api_path, "/api/v1/readings_audio/daily_office")
        self.assertTrue(eucharist.proper_days_only)
        self.assertEqual(eucharist.api_query()["position"], "principal")
        self.assertEqual(
            eucharist.follow_along_url(date(2026, 10, 18)),
            "https://www.dailyoffice2019.com/readings/holy_eucharist/2026/10/18",
        )


class RetentionTests(MediaRootMixin, SimpleTestCase):
    def setUp(self):
        self.use_temporary_media_root()

    def test_only_the_podcast_archive_is_permanent(self):
        self.assertTrue(is_permanent(self.root / "podcasts"))
        self.assertTrue(is_permanent(self.root / "podcasts" / "compline" / "2026" / "compline-2026-10-13.mp3"))
        self.assertFalse(is_permanent(self.root / "gemini" / "track.mp3"))
        self.assertFalse(is_permanent(self.root / "podcasts-old" / "x.mp3"))
        self.assertTrue(is_permanent(self.root / "gemini" / ".." / "podcasts" / "x.mp3"))


@skipUnless(HAS_FFMPEG, "ffmpeg is required")
class CleanupNeverDeletesEpisodesTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.use_temporary_media_root()
        self.episode = make_mp3(self.root / "podcasts" / "morning-prayer" / "2026" / "morning-prayer-2026-10-13.mp3")
        self.track = make_mp3(self.root / "00000000-0000-5000-8000-000000000001.mp3")
        self.assertIn("Lavf", str(ID3(self.episode).getall("TSSE")))

    def test_cleanup_full_audio_files_skips_the_archive(self):
        call_command("cleanup_full_audio_files", "--execute", stdout=StringIO())
        self.assertFalse(self.track.exists())
        self.assertTrue(self.episode.exists())

    def test_even_if_a_provider_folder_is_the_archive(self):
        provider = SimpleNamespace(media_subdir="podcasts/morning-prayer/2026")
        with (
            patch("office.management.commands.cleanup_full_audio_files.provider_names", return_value=["x"]),
            patch("office.management.commands.cleanup_full_audio_files.get_tts_provider", return_value=provider),
        ):
            call_command("cleanup_full_audio_files", "--execute", stdout=StringIO())
        self.assertTrue(self.episode.exists())

    def test_audit_combined_audio_skips_the_archive(self):
        # A truncated, track-named file inside the archive is still never deleted.
        bad = self.root / "podcasts" / "00000000-0000-5000-8000-000000000002.mp3"
        bad.write_bytes(b"not audio")
        call_command("audit_combined_audio", "--delete", stdout=StringIO())
        self.assertTrue(bad.exists())
        self.assertTrue(self.episode.exists())


class FakeCommemoration(SimpleNamespace):
    pass


def commemoration(name, rank="HOLY_DAY", about=""):
    return FakeCommemoration(name=name, rank=SimpleNamespace(name=rank), ai_one_sentence=about)


FERIA = commemoration(
    "Tuesday after the Twentieth Sunday after Pentecost, or the Nineteenth Sunday after Trinity (Proper 23)",
    rank="FERIA",
)
EDWARD = commemoration(
    "Edward the Confessor, King of England, 1066", rank="COMMEMORATION_ANGLICAN", about="A king known for piety[1]."
)


class EpisodeTextTests(SimpleTestCase):
    def setUp(self):
        self.feed = catalog.get_feed("morning-prayer")
        self.day = date(2026, 10, 13)

    def calendar(self, *days):
        return SimpleNamespace(all=list(days), all_evening=list(days), primary=days[0])

    def test_titles_lead_with_the_date_and_name_the_day(self):
        self.assertEqual(
            episodes.episode_title(self.feed, self.day, self.calendar(FERIA, EDWARD)),
            "Tuesday, October 13, 2026: Edward the Confessor, King of England, 1066",
        )
        self.assertEqual(
            episodes.episode_title(self.feed, self.day, self.calendar(FERIA)),
            "Tuesday, October 13, 2026: Week of the Twentieth Sunday after Pentecost",
        )
        sunday = commemoration(
            "The Twenty-first Sunday after Pentecost, or the Twentieth Sunday after Trinity", "SUNDAY"
        )
        self.assertEqual(
            episodes.episode_title(self.feed, date(2026, 10, 18), self.calendar(sunday)),
            "Sunday, October 18, 2026: The Twenty-first Sunday after Pentecost",
        )

    def test_readings_come_from_the_office_text(self):
        modules = [
            {"name": "Opening Sentence", "lines": [{"line_type": "citation", "content": "PSALM 19:14"}]},
            {
                "name": "Psalms",
                "lines": [
                    {"line_type": "heading", "content": "The Psalm Appointed"},
                    {"line_type": "heading", "content": "Psalm 107:1-22"},
                ],
            },
            {"name": "First Reading", "lines": [{"line_type": "subheading", "content": "II Kings 4"}]},
            {"name": "Second Reading", "lines": [{"line_type": "subheading", "content": "I John 2:7-29"}]},
        ]
        self.assertEqual(episodes.readings(modules), [("", ["Psalm 107:1-22", "II Kings 4", "I John 2:7-29"])])
        grouped = [
            {"name": "Morning Prayer: The Psalms", "lines": [{"line_type": "heading", "content": "Psalm 1"}]},
            {"name": "Morning Prayer: The First Lesson", "lines": [{"line_type": "subheading", "content": "Gen 1"}]},
            {"name": "Evening Prayer: The Psalms", "lines": [{"line_type": "heading", "content": "Psalm 2"}]},
        ]
        self.assertEqual(
            episodes.readings(grouped), [("Morning Prayer", ["Psalm 1", "Gen 1"]), ("Evening Prayer", ["Psalm 2"])]
        )

    def test_show_notes_link_to_the_office_and_credit_the_esv(self):
        summary, html = episodes.show_notes(self.feed, self.day, self.calendar(FERIA, EDWARD), [])
        self.assertIn("Daily Morning Prayer for Tuesday, October 13, 2026.", summary)
        self.assertIn("A king known for piety.", summary)  # citation markers removed
        self.assertIn(self.feed.follow_along_url(self.day).replace("&", "&amp;"), html)
        self.assertIn("synthesized", summary)
        self.assertIn("ESV®", summary)
        kjv_summary, _ = episodes.show_notes(
            catalog.get_feed("morning-prayer-traditional"), self.day, self.calendar(FERIA), []
        )
        self.assertNotIn("ESV®", kjv_summary)

    def test_published_at_three_in_the_morning_eastern(self):
        published = episodes.published_at(date(2026, 10, 13))
        self.assertEqual(published.astimezone(dt_timezone.utc), datetime(2026, 10, 13, 7, 0, tzinfo=dt_timezone.utc))

    def test_citations_are_set_in_title_case(self):
        self.assertEqual(episodes.citation("HEBREWS 13:20-21"), "Hebrews 13:20-21")
        self.assertEqual(episodes.citation("II KINGS 5"), "II Kings 5")
        self.assertEqual(episodes.citation("Song of Songs 2"), "Song of Songs 2")

    def test_chapters_from_sections(self):
        sections = [
            {"name": "Opening", "start_time": 0},
            {"name": "Opening", "start_time": 3},
            {"name": "Daily Office Module", "start_time": 30},
            {"name": "Psalms", "start_time": 61.234},
        ]
        self.assertEqual(
            episodes.chapters(sections),
            [{"startTime": 0, "title": "Opening"}, {"startTime": 61.23, "title": "Psalms"}],
        )


class ReadingsAudioHelperTests(TestCase):
    def test_psalms_are_announced_in_words(self):
        self.assertEqual(spoken_psalm("Psalm 96"), "Psalm ninety-six.")
        self.assertEqual(
            spoken_psalm("Psalm 119:1-24"), "Psalm one hundred and nineteen, verses one through twenty-four."
        )
        self.assertIsNone(spoken_psalm("The Psalm Appointed"))

    def test_one_reading_per_place_in_the_service(self):
        readings = [SimpleNamespace(reading_number=n, id=i) for i, n in enumerate([1, 1, 2, 3, 4, 4])]
        self.assertEqual([reading.id for reading in first_per_reading_number(readings)], [0, 2, 3, 4])

    def test_readings_audio_rejects_unknown_services(self):
        self.assertEqual(KINDS, ("morning_prayer", "evening_prayer", "daily_office", "holy_eucharist"))
        response = self.client.get("/api/v1/readings_audio/vespers/2026-10-13")
        self.assertEqual(response.status_code, 404)


@skipUnless(HAS_FFMPEG, "ffmpeg is required")
class BuildEpisodeTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.use_temporary_media_root()
        self.source = make_mp3(self.root / "gemini" / "00000000-0000-5000-8000-0000000000aa.mp3", seconds=3)
        self.feed = catalog.get_feed("evening-prayer")
        self.day = date(2026, 10, 13)
        self.data = {
            "modules": [{"name": "Psalms", "lines": [{"line_type": "heading", "content": "Psalm 108"}]}],
            "audio": {
                "single_track": [
                    "https://api.example/uploads/gemini/x.mp3",
                    f"/uploads/gemini/{self.source.name}",
                    [{"name": "Opening", "start_time": 0}, {"name": "Psalms", "start_time": 1.5}],
                    [],
                    [],
                ]
            },
        }
        calendar = SimpleNamespace(all=[FERIA, EDWARD], all_evening=[FERIA, EDWARD], primary=FERIA)
        self.mocks = {}
        for target, value in (
            ("podcasts.builder.get_calendar_date", calendar),
            ("podcasts.builder.render_office_audio", self.data),
        ):
            patcher = patch(target, return_value=value)
            self.mocks[target] = patcher.start()
            self.addCleanup(patcher.stop)

    def test_builds_a_permanent_tagged_copy(self):
        episode = builder.build_episode(self.feed, self.day)
        path = self.root / "podcasts" / "evening-prayer" / "2026" / "evening-prayer-2026-10-13.mp3"
        self.assertEqual(episode.filename, "evening-prayer/2026/evening-prayer-2026-10-13.mp3")
        self.assertTrue(path.is_file())
        self.assertTrue(is_permanent(path))
        self.assertEqual(episode.file_size, path.stat().st_size)
        self.assertAlmostEqual(episode.duration, 3, delta=0.2)
        self.assertEqual(episode.guid, "dailyoffice2019-evening-prayer-2026-10-13")
        self.assertEqual(episode.title, "Tuesday, October 13, 2026: Edward the Confessor, King of England, 1066")
        tags = ID3(path)
        self.assertEqual(tags.getall("TSSE"), [])  # not mistaken for a disposable track
        self.assertEqual(str(tags["TALB"]), "Evening Prayer")
        chapters = sorted(tags.getall("CHAP"), key=lambda chap: chap.start_time)
        self.assertEqual([str(chap.sub_frames["TIT2"]) for chap in chapters], ["Opening", "Psalms"])
        self.assertEqual([chap.start_time for chap in chapters], [0, 1500])
        # The source combined track is untouched and still disposable.
        self.assertTrue(self.source.exists())
        self.assertFalse(is_permanent(self.source))

    def test_existing_episodes_are_never_rebuilt(self):
        first = builder.build_episode(self.feed, self.day)
        render = self.mocks["podcasts.builder.render_office_audio"]
        render.reset_mock()
        self.assertEqual(builder.build_episode(self.feed, self.day), first)
        render.assert_not_called()
        self.assertEqual(PodcastEpisode.objects.count(), 1)

    def test_eucharist_feed_skips_days_without_proper_readings(self):
        with patch("podcasts.builder.has_proper_eucharist", return_value=False):
            self.assertIsNone(builder.build_episode(catalog.get_feed("holy-eucharist-readings"), self.day))
        self.mocks["podcasts.builder.render_office_audio"].assert_not_called()

    def test_command_reports_and_continues_after_failures(self):
        self.mocks["podcasts.builder.render_office_audio"].side_effect = [builder.EpisodeBuildError("no"), self.data]
        out, err = StringIO(), StringIO()
        with self.assertRaises(Exception):
            call_command(
                "build_podcast_episodes",
                "--start-date=2026-10-13",
                "--days=1",
                "--feed=evening-prayer",
                "--feed=compline",
                stdout=out,
                stderr=err,
            )
        self.assertIn("FAILED evening-prayer 2026-10-13", err.getvalue())
        self.assertTrue(PodcastEpisode.objects.filter(feed_slug="compline").exists())


@override_settings(PODCAST_BASE_URL="https://api.example.org")
class FeedTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.use_temporary_media_root()
        self.feed = catalog.get_feed("morning-prayer")
        now = timezone.now()
        self.published = self.episode("2026-10-12", now - timedelta(hours=1))
        self.scheduled = self.episode("2026-10-13", now + timedelta(hours=5))

    def episode(self, day, published):
        return PodcastEpisode.objects.create(
            feed_slug=self.feed.slug,
            date=date.fromisoformat(day),
            title=f"Episode {day}",
            summary="Summary",
            description_html="<p>Notes & more</p>",
            filename=f"morning-prayer/2026/morning-prayer-{day}.mp3",
            file_size=1234,
            duration=1500.4,
            chapters=[{"startTime": 0, "title": "Opening"}],
            follow_along_url="https://www.dailyoffice2019.com/morning_prayer/2026/10/12?a=1&b=2",
            guid=f"dailyoffice2019-morning-prayer-{day}",
            published_at=published,
        )

    def test_feed_lists_only_published_episodes(self):
        response = self.client.get("/podcasts/morning-prayer.xml")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/rss+xml"))
        channel = ET.fromstring(response.content).find("channel")
        self.assertEqual(channel.findtext("title"), "Morning Prayer")
        items = channel.findall("item")
        self.assertEqual([item.findtext("title") for item in items], ["Episode 2026-10-12"])
        enclosure = items[0].find("enclosure")
        self.assertEqual(
            enclosure.get("url"),
            "https://api.example.org/podcasts/episodes/morning-prayer/2026/morning-prayer-2026-10-12.mp3",
        )
        self.assertEqual(enclosure.get("length"), "1234")
        self.assertEqual(enclosure.get("type"), "audio/mpeg")
        self.assertEqual(items[0].findtext(f"{{{rss.ITUNES}}}duration"), "1500")
        self.assertEqual(
            channel.find(f"{{{rss.ITUNES}}}image").get("href"),
            "https://api.example.org/podcasts/artwork/morning-prayer.jpg",
        )
        self.assertEqual(channel.find(f"{{{rss.ITUNES}}}category").get("text"), "Religion & Spirituality")
        self.assertEqual(channel.findtext(f"{{{rss.PODCAST}}}guid"), rss.podcast_guid("morning-prayer"))

    def test_podcast_guid_is_stable(self):
        self.assertEqual(rss.podcast_guid("morning-prayer"), rss.podcast_guid("morning-prayer"))
        self.assertNotEqual(rss.podcast_guid("morning-prayer"), rss.podcast_guid("compline"))

    def test_unknown_feed_is_404(self):
        self.assertEqual(self.client.get("/podcasts/vespers.xml").status_code, 404)

    @skipUnless(HAS_FFMPEG, "ffmpeg is required")
    def test_episode_audio_supports_head_and_ranges(self):
        path = make_mp3(self.root / "podcasts" / self.published.filename)
        url = f"/podcasts/episodes/{self.published.filename}"
        head = self.client.head(url)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head["Content-Length"], str(path.stat().st_size))
        self.assertEqual(head["Accept-Ranges"], "bytes")
        partial = self.client.get(url, HTTP_RANGE="bytes=0-99")
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial["Content-Length"], "100")
        self.assertEqual(self.client.get("/podcasts/episodes/../gemini/x.mp3").status_code, 404)

    def test_chapters_only_for_published_episodes(self):
        response = self.client.get("/podcasts/chapters/morning-prayer/2026-10-12.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chapters"], [{"startTime": 0, "title": "Opening"}])
        self.assertEqual(self.client.get("/podcasts/chapters/morning-prayer/2026-10-13.json").status_code, 404)

    def test_catalog_for_the_landing_page(self):
        data = self.client.get("/api/v1/podcasts").json()
        self.assertEqual(len(data["feeds"]), 18)
        morning = next(feed for feed in data["feeds"] if feed["slug"] == "morning-prayer")
        self.assertEqual(morning["feed_url"], "https://api.example.org/podcasts/morning-prayer.xml")
        self.assertEqual(morning["episode_count"], 1)
        self.assertEqual(morning["latest_episode"]["date"], "2026-10-12")
        self.assertEqual([group["slug"] for group in data["groups"]], ["daily-office", "family", "readings"])
        self.assertEqual(data["live_alternative"]["host"], "Andrew Russell")

    @override_settings(PODCAST_NOTIFY_DIRECTORIES=False)
    def test_notify_does_nothing_outside_production(self):
        with patch("podcasts.directories.notify") as notify:
            call_command("notify_podcast_directories", stdout=StringIO(), stderr=StringIO())
        notify.assert_not_called()
        self.published.refresh_from_db()
        self.assertIsNone(self.published.notified_at)

    @override_settings(PODCAST_NOTIFY_DIRECTORIES=True)
    def test_notify_pings_each_new_feed_once(self):
        with patch("podcasts.directories.notify", return_value={"websub": None}) as notify:
            call_command("notify_podcast_directories", stdout=StringIO(), stderr=StringIO())
            call_command("notify_podcast_directories", stdout=StringIO(), stderr=StringIO())
        notify.assert_called_once_with("morning-prayer")
        self.published.refresh_from_db()
        self.scheduled.refresh_from_db()
        self.assertIsNotNone(self.published.notified_at)
        self.assertIsNone(self.scheduled.notified_at)

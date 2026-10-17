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

from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from mutagen.id3 import ID3

from office import audio_builds
from office.api.views import index
from office.api.views.index import Office, OfficeAudioSerializer, Settings
from office.api.views.tts import get_tts_provider
from office.models import Setting, SettingOption
from office.audio_retention import is_permanent
from office.readings_audio import KINDS, ReadingsAudioOffice, first_per_reading_number, spoken_psalm
from podcasts import builder, catalog, custom, episodes, rss, views
from podcasts.management.commands import build_podcast_artwork as artwork
from podcasts.models import CustomPodcastEpisode, CustomPodcastFeed, PodcastDirectoryListing, PodcastEpisode

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
    def test_twenty_feeds_with_unique_slugs(self):
        self.assertEqual(len(catalog.FEEDS), 20)
        self.assertEqual(len(catalog.FEEDS_BY_SLUG), 20)

    def test_every_feed_has_a_traditional_language_twin(self):
        traditional = [feed for feed in catalog.FEEDS if feed.style == catalog.TRADITIONAL]
        self.assertEqual(len(traditional), 10)
        for feed in traditional:
            twin = catalog.get_feed(feed.slug.removesuffix("-traditional"))
            self.assertEqual(twin.style, catalog.CONTEMPORARY)
            self.assertEqual(feed.title, f"{twin.title} (Traditional Language)")
            self.assertEqual((feed.service, feed.group), (twin.service, twin.group))
        offices = [feed for feed in catalog.FEEDS if not feed.is_readings]
        self.assertEqual(len(offices), 16)
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
            "https://www.dailyoffice2019.com/readings/holy_eucharist/2026/10/18?translation=esv&psalms=contemporary",
        )

    def test_traditional_readings_are_the_kjv(self):
        daily = catalog.get_feed("daily-office-readings-traditional")
        eucharist = catalog.get_feed("holy-eucharist-readings-traditional")
        self.assertEqual(daily.api_path, "/api/v1/readings_audio/daily_office")
        self.assertEqual(daily.settings["translation"], "kjv")
        self.assertEqual(daily.settings["psalms"], "traditional")
        self.assertEqual(catalog.get_feed("daily-office-readings").settings["translation"], "esv")
        self.assertTrue(eucharist.proper_days_only)
        self.assertEqual(eucharist.api_query()["translation"], "kjv")
        self.assertIn("King James Version", eucharist.description)
        self.assertIn("King James Version", daily.style_label)
        self.assertEqual(
            parse_qs(urlparse(daily.follow_along_url(date(2026, 10, 18))).query),
            {"translation": ["kjv"], "psalms": ["traditional"], "cycle": ["60"]},
        )


class ArtworkTests(SimpleTestCase):
    def test_every_feed_has_cover_art(self):
        for feed in catalog.FEEDS:
            for name in (f"{feed.slug}.jpg", f"{feed.slug}-600.jpg"):
                with self.subTest(name):
                    self.assertTrue((builder.ARTWORK_DIR / name).is_file())
            self.assertLessEqual((builder.ARTWORK_DIR / f"{feed.slug}.jpg").stat().st_size, 512 * 1024)

    def test_leather_follows_the_language_and_borders_the_section(self):
        self.assertEqual(set(artwork.LEATHER_TONE), {catalog.CONTEMPORARY, catalog.TRADITIONAL})
        self.assertIsNone(artwork.LEATHER_TONE[catalog.CONTEMPORARY])
        self.assertEqual(set(artwork.BORDERS), {group["slug"] for group in catalog.GROUPS})
        borders = [tuple(rules) for rules in artwork.BORDERS.values()]
        self.assertEqual(len(set(borders)), len(borders))


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

    def test_readings_audio_is_only_read_from_the_esv_or_kjv(self):
        class Built(Exception):
            pass

        def bare_office(office, request, year, month, day):
            office.settings = {"display_language": "english"}

        serializer = OfficeAudioSerializer()
        with (
            patch.object(Office, "__init__", bare_office),
            patch.object(OfficeAudioSerializer, "get_modules", side_effect=Built),
        ):
            for translation in ("esv", "kjv", "rsv", "nrsvce", "niv", "cuv"):
                with self.subTest(translation=translation):
                    request = SimpleNamespace(GET={"translation": translation})
                    office = ReadingsAudioOffice(request, 2026, 10, 13, kind="daily_office")
                    if translation in ("esv", "kjv"):
                        with self.assertRaises(Built):
                            serializer.get_audio(office)
                    else:
                        self.assertEqual(serializer.get_audio(office), [])


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

    def eucharist_days(self, *proper):
        """Give only the ``proper`` days (YYYY-MM-DD) their own Eucharistic readings."""
        calendar_date = self.mocks["podcasts.builder.get_calendar_date"]
        calendar_date.side_effect = lambda day: SimpleNamespace(**vars(calendar_date.return_value), day=day)
        patcher = patch("podcasts.builder.has_proper_eucharist", side_effect=lambda calendar: calendar.day in proper)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_first_episode_day_only_for_an_empty_feed_on_a_day_without_readings(self):
        self.eucharist_days("2026-10-11", "2026-10-14")
        eucharist = catalog.get_feed("holy-eucharist-readings")
        self.assertEqual(builder.first_episode_day(eucharist, date(2026, 10, 13)), date(2026, 10, 11))
        self.assertIsNone(builder.first_episode_day(eucharist, date(2026, 10, 14)))  # today has its own
        self.assertIsNone(builder.first_episode_day(self.feed, date(2026, 10, 13)))  # publishes every day
        builder.build_episode(eucharist, date(2026, 10, 11))
        self.assertIsNone(builder.first_episode_day(eucharist, date(2026, 10, 13)))  # already has one

    def test_an_empty_eucharist_feed_starts_with_the_most_recent_day_with_readings(self):
        self.eucharist_days("2026-10-04", "2026-10-11")
        with patch("django.utils.timezone.localdate", return_value=date(2026, 10, 14)):
            for _ in range(2):
                call_command("build_podcast_episodes", "--feed=holy-eucharist-readings", stdout=StringIO())
        self.assertEqual(list(PodcastEpisode.objects.values_list("date", flat=True)), [date(2026, 10, 11)])
        self.mocks["podcasts.builder.render_office_audio"].assert_called_once()

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
        self.assertEqual(len(data["feeds"]), 20)
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


@override_settings(PODCAST_BASE_URL="https://api.example.org")
class DirectoryListingTests(TestCase):
    APPLE_URL = "https://podcasts.apple.com/us/podcast/morning-prayer/id1234567890"

    def record(self, *args):
        out = StringIO()
        call_command("record_podcast_listing", *args, stdout=out)
        return out.getvalue()

    def test_record_listing_then_correct_it(self):
        self.assertIn(
            "Recorded: Morning Prayer on Apple Podcasts", self.record("morning-prayer", "apple", self.APPLE_URL)
        )
        self.assertIn("Already recorded", self.record("morning-prayer", "apple", self.APPLE_URL))
        corrected = "https://podcasts.apple.com/us/podcast/morning-prayer/id42"
        self.assertIn("Updated", self.record("morning-prayer", "apple", f" {corrected} "))
        listing = PodcastDirectoryListing.objects.get()
        self.assertEqual((listing.feed_slug, listing.platform, listing.url), ("morning-prayer", "apple", corrected))

    def test_rejects_a_link_that_is_not_the_directorys_show_page(self):
        for platform, url in [
            ("apple", "https://api.dailyoffice2019.com/podcasts/morning-prayer.xml"),
            ("spotify", "https://creators.spotify.com/pod/show/morning-prayer"),
            ("youtube_music", "https://studio.youtube.com/channel/UC123/podcasts"),
            ("apple", "http://podcasts.apple.com/us/podcast/morning-prayer/id1234567890"),
            ("apple", "not a url"),
        ]:
            with self.subTest(url=url), self.assertRaises(CommandError):
                self.record("morning-prayer", platform, url)
        self.assertFalse(PodcastDirectoryListing.objects.exists())

    def test_rejects_unknown_feeds_and_platforms(self):
        with self.assertRaises(CommandError):
            self.record("vespers", "apple", self.APPLE_URL)
        with self.assertRaises(CommandError):
            self.record("morning-prayer", "napster", self.APPLE_URL)

    def test_checklist_lists_the_feeds_still_missing_from_a_directory(self):
        self.record("morning-prayer", "apple", self.APPLE_URL)
        out = StringIO()
        call_command("podcast_submission_checklist", "--missing", "apple", stdout=out)
        rows = [line.split("\t") for line in out.getvalue().splitlines()]
        self.assertEqual(len(rows), len(catalog.FEEDS) - 1)
        self.assertNotIn("morning-prayer", [slug for slug, _, _ in rows])
        self.assertEqual(
            rows[0],
            [
                "morning-prayer-traditional",
                "Morning Prayer (Traditional Language)",
                "https://api.example.org/podcasts/morning-prayer-traditional.xml",
            ],
        )
        out = StringIO()
        call_command("podcast_submission_checklist", "--missing", "spotify", stdout=out)
        self.assertEqual(len(out.getvalue().splitlines()), len(catalog.FEEDS))

    def test_adding_to_podcast_index_records_the_listings(self):
        feed_ids = {feed.slug: index + 100 for index, feed in enumerate(catalog.FEEDS)}
        feed_ids["compline"] = None
        with patch("podcasts.directories.add_to_podcast_index", side_effect=feed_ids.get):
            call_command("notify_podcast_directories", "--add-to-podcast-index", stdout=StringIO())
            call_command("notify_podcast_directories", "--add-to-podcast-index", stdout=StringIO())
        listings = PodcastDirectoryListing.objects.filter(platform=PodcastDirectoryListing.PODCAST_INDEX)
        self.assertEqual(listings.count(), len(catalog.FEEDS) - 1)
        self.assertEqual(
            listings.get(feed_slug="morning-prayer").url,
            f"https://podcastindex.org/podcast/{feed_ids['morning-prayer']}",
        )
        self.assertFalse(listings.filter(feed_slug="compline").exists())


class StyleLabelTests(SimpleTestCase):
    def test_public_style_labels_are_unchanged(self):
        self.assertEqual(
            catalog.get_feed("morning-prayer").style_label,
            "Contemporary language, English Standard Version (ESV), Renewed Coverdale Psalter",
        )
        self.assertEqual(
            catalog.get_feed("compline-traditional").style_label,
            "Traditional prayer-book language, King James Version (KJV), Coverdale Psalter",
        )
        self.assertEqual(
            catalog.get_feed("daily-office-readings").style_label,
            "English Standard Version (ESV), Renewed Coverdale Psalter",
        )
        self.assertEqual(
            catalog.get_feed("holy-eucharist-readings-traditional").style_label,
            "King James Version (KJV), Coverdale Psalter",
        )


# --- EXPERIMENTAL custom podcasts --------------------------------------------

EASTERN = custom.EASTERN


def eastern(*args):
    return datetime(*args, tzinfo=EASTERN)


def create_setting_options(extra=None):
    """Setting rows for every office key: the two public values, plus ``extra`` {key: [values]}."""
    for order, key in enumerate(custom.OFFICE_SETTING_KEYS):
        setting = Setting.objects.create(name=key, title=key, order=order)
        values = list(dict.fromkeys([catalog.CONTEMPORARY_SETTINGS[key], catalog.TRADITIONAL_SETTINGS[key]]))
        values += [value for value in (extra or {}).get(key, []) if value not in values]
        for index, value in enumerate(values):
            SettingOption.objects.create(setting=setting, value=value, name=value, order=index)


class CustomFeedValidationTests(TestCase):
    def test_settings_are_normalized_known_keys_only_and_sorted(self):
        normalized = custom.normalize("office/morning_prayer", {"bible_translation": "kjv"})
        self.assertEqual(list(normalized), sorted(catalog.CONTEMPORARY_SETTINGS))
        self.assertEqual(normalized["bible_translation"], "kjv")
        self.assertEqual(normalized["psalter"], "60")  # defaults filled in
        readings = custom.normalize("readings/morning_prayer", {"translation": "kjv", "psalter": "30"})
        self.assertEqual(
            readings, {"psalms": "contemporary", "psalter": "30", "style": "whole_verse", "translation": "kjv"}
        )

    def test_audio_exists_only_in_english_from_the_esv_or_kjv(self):
        for service, settings_ in [
            ("office/morning_prayer", {"bible_translation": "rsv"}),
            ("office/morning_prayer", {"bible_translation": "niv"}),
            ("family/close_of_day_prayer", {"display_language": "spanish"}),
            ("readings/daily_office", {"translation": "nrsvce"}),
        ]:
            with self.subTest(settings_), self.assertRaisesMessage(custom.InvalidCustomFeed, custom.AUDIO_ONLY):
                custom.normalize(service, settings_)

    def test_unknown_keys_services_and_values_are_rejected(self):
        with self.assertRaisesMessage(custom.InvalidCustomFeed, "Unknown settings: theme"):
            custom.normalize("office/compline", {"theme": "dark"})
        with self.assertRaisesMessage(custom.InvalidCustomFeed, "Unknown settings: bible_translation"):
            custom.normalize("readings/daily_office", {"bible_translation": "esv"})  # readings use "translation"
        with self.assertRaises(custom.InvalidCustomFeed):
            custom.normalize("office/vespers", {})
        with self.assertRaises(custom.InvalidCustomFeed):
            custom.normalize("office/compline", {"psalter": ["60"]})
        with self.assertRaises(custom.InvalidCustomFeed):
            custom.normalize("readings/daily_office", {"style": "chant"})
        create_setting_options()
        with self.assertRaisesMessage(custom.InvalidCustomFeed, "Invalid value for psalter"):
            custom.normalize("office/compline", {"psalter": "45"})  # not an option the site offers

    def test_services_come_from_the_catalog_and_the_readings_audio_kinds(self):
        options = custom.builder_options()
        offices = {group["slug"]: [office["service"] for office in group["offices"]] for group in options["types"]}
        self.assertEqual(
            offices["daily-office"],
            ["office/morning_prayer", "office/midday_prayer", "office/evening_prayer", "office/compline"],
        )
        self.assertEqual(len(offices["family"]), 4)
        self.assertEqual(
            offices["readings"],
            ["readings/daily_office", "readings/holy_eucharist", "readings/morning_prayer", "readings/evening_prayer"],
        )
        self.assertEqual(options["audio"]["bible_translation"], ["esv", "kjv"])
        self.assertEqual(options["office_settings"]["keys"], sorted(catalog.CONTEMPORARY_SETTINGS))
        self.assertEqual(options["publish_hour"], 2)


@override_settings(PODCAST_BASE_URL="https://api.example.org")
class CustomFeedCreateTests(TestCase):
    URL = "/api/v1/podcasts/custom"

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        patcher = patch("podcasts.custom.audio_builds.schedule", return_value=True)
        self.schedule = patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, service="office/morning_prayer", settings_=None, **extra):
        body = {"service": service, "settings": settings_ or {}}
        return self.client.post(self.URL, body, content_type="application/json", **extra)

    def test_creates_a_short_token_feed_and_starts_building(self):
        response = self.post(settings_={"bible_translation": "kjv", "language_style": "traditional"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        feed = CustomPodcastFeed.objects.get()
        self.assertEqual(data["token"], feed.token)
        self.assertRegex(feed.token, r"^[A-Za-z0-9_-]{11}$")
        self.assertEqual(data["feed_url"], f"https://api.example.org/podcasts/custom/{feed.token}.xml")
        self.assertEqual(data["title"], "My Morning Prayer (Experimental) — The Daily Office")
        self.assertEqual(
            data["artwork_url"], "https://api.example.org/podcasts/artwork/morning-prayer-traditional-600.jpg"
        )
        self.assertEqual(feed.settings["bible_translation"], "kjv")
        self.assertEqual(feed.settings_hash, custom.settings_hash(feed.settings))
        # The window's seven days and tomorrow's, so episodes are ready when the app asks.
        self.assertEqual(self.schedule.call_count, 8)

    def test_the_same_service_and_settings_give_the_same_feed(self):
        first = self.post(settings_={"psalter": "30"}).json()
        again = self.post(settings_={"psalter": "30", "bible_translation": "esv"})  # esv is the default
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["token"], first["token"])
        self.assertFalse(again.json()["created"])
        other = self.post(service="office/compline", settings_={"psalter": "30"}).json()
        self.assertNotEqual(other["token"], first["token"])
        self.assertEqual(CustomPodcastFeed.objects.count(), 2)

    def test_invalid_requests_are_rejected(self):
        self.assertEqual(self.post(settings_={"bible_translation": "rsv"}).status_code, 400)
        self.assertEqual(self.post(settings_={"unknown": "x"}).status_code, 400)
        self.assertEqual(self.post(service="office/vespers").status_code, 400)
        self.assertFalse(CustomPodcastFeed.objects.exists())

    def test_rate_limited_per_ip(self):
        with patch.object(views.CustomPodcastThrottle, "rate", "2/hour", create=True):
            statuses = [self.post(settings_={"psalter": "30"}, REMOTE_ADDR="10.0.0.1").status_code for _ in range(3)]
            elsewhere = self.post(settings_={"psalter": "30"}, REMOTE_ADDR="10.0.0.2").status_code
        self.assertEqual(statuses, [201, 200, 429])
        self.assertEqual(elsewhere, 200)


class CustomFeedWindowTests(SimpleTestCase):
    def test_each_day_appears_at_two_in_the_morning_eastern(self):
        self.assertEqual(custom.window(eastern(2026, 10, 17, 1, 59))[0], date(2026, 10, 16))
        self.assertEqual(custom.window(eastern(2026, 10, 17, 2, 0))[0], date(2026, 10, 17))
        published = custom.publish_time(date(2026, 10, 17))
        self.assertEqual(published.astimezone(dt_timezone.utc), datetime(2026, 10, 17, 6, 0, tzinfo=dt_timezone.utc))
        # Public feeds keep their own hour.
        self.assertEqual(episodes.published_at(date(2026, 10, 17)).hour, 3)

    def test_seven_days_and_the_oldest_drops_off(self):
        days = custom.window(eastern(2026, 10, 17, 9, 0))
        self.assertEqual(days, [date(2026, 10, 17) - timedelta(days=offset) for offset in range(7)])
        self.assertEqual(custom.window(eastern(2026, 10, 18, 2, 0))[-1], date(2026, 10, 12))


@override_settings(PODCAST_BASE_URL="https://api.example.org")
class CustomFeedFetchTests(MediaRootMixin, TestCase):
    NOW = eastern(2026, 10, 17, 9, 0)

    def setUp(self):
        self.use_temporary_media_root()
        self.feed, _ = custom.get_or_create_feed("office/evening_prayer", {"psalter": "30"})
        for target, value in (
            ("django.utils.timezone.now", self.NOW),
            ("podcasts.custom.audio_builds.schedule", True),
        ):
            patcher = patch(target, return_value=value)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
        self.schedule = mock

    def ready(self, day, filename="openai/00000000-0000-5000-8000-0000000000aa.mp3"):
        return CustomPodcastEpisode.objects.create(
            feed=self.feed,
            date=day,
            track_filename=filename,
            file_size=4321,
            duration=900.2,
            chapters=[{"startTime": 0, "title": "Opening"}],
            title=f"Episode {day}",
            summary="Summary",
            description_html="<p>Notes</p>",
            follow_along_url="https://www.dailyoffice2019.com/evening_prayer/2026/10/16?psalter=30",
        )

    def fetch(self):
        response = self.client.get(f"/podcasts/custom/{self.feed.token}.xml")
        self.assertEqual(response.status_code, 200)
        return ET.fromstring(response.content).find("channel")

    def test_lists_only_ready_days_and_queues_the_rest(self):
        self.ready(date(2026, 10, 16))
        CustomPodcastEpisode.objects.create(feed=self.feed, date=date(2026, 10, 15))  # nothing that day
        channel = self.fetch()
        items = channel.findall("item")
        self.assertEqual([item.findtext("title") for item in items], ["Episode 2026-10-16"])
        enclosure = items[0].find("enclosure")
        self.assertEqual(
            enclosure.get("url"), f"https://api.example.org/podcasts/custom/{self.feed.token}/2026-10-16.mp3"
        )
        self.assertEqual(enclosure.get("length"), "4321")
        self.assertEqual(items[0].findtext("pubDate"), "Fri, 16 Oct 2026 02:00:00 -0400")
        queued = [call.args[0].rsplit(":", 1)[1] for call in self.schedule.call_args_list]
        self.assertEqual(queued, ["2026-10-17", "2026-10-14", "2026-10-13", "2026-10-12", "2026-10-11", "2026-10-18"])

    def test_a_private_feed_with_borrowed_art(self):
        channel = self.fetch()
        self.assertEqual(channel.findtext("title"), "My Evening Prayer (Experimental) — The Daily Office")
        self.assertEqual(channel.findtext(f"{{{rss.ITUNES}}}block"), "Yes")
        self.assertIsNone(channel.find(f"{{{rss.PODCAST}}}guid"))
        self.assertEqual(
            [link.get("rel") for link in channel.findall(f"{{{rss.ATOM}}}link")], ["self"]
        )  # no WebSub hub
        self.assertEqual(
            channel.find(f"{{{rss.ITUNES}}}image").get("href"),
            "https://api.example.org/podcasts/artwork/evening-prayer.jpg",
        )
        self.feed.refresh_from_db()
        self.assertEqual(self.feed.last_fetched_at, self.NOW)

    def test_old_days_are_deleted(self):
        self.ready(date(2026, 10, 10))
        self.ready(date(2026, 10, 11))
        channel = self.fetch()
        self.assertEqual([item.findtext("title") for item in channel.findall("item")], ["Episode 2026-10-11"])
        self.assertEqual(list(CustomPodcastEpisode.objects.values_list("date", flat=True)), [date(2026, 10, 11)])

    def test_builds_wait_while_the_queue_is_busy(self):
        with patch("podcasts.custom.audio_builds.pending_count", return_value=8):
            self.fetch()
        self.schedule.assert_not_called()

    def test_follow_along_link_carries_the_custom_settings(self):
        podcast = custom.as_podcast_feed(self.feed)
        query = parse_qs(urlparse(podcast.follow_along_url(date(2026, 10, 16))).query)
        self.assertEqual(query["psalter"], ["30"])
        self.assertEqual(urlparse(podcast.follow_along_url(date(2026, 10, 16))).path, "/evening_prayer/2026/10/16")
        self.assertIn("Contemporary language", podcast.description)

    def test_unknown_token_is_404(self):
        self.assertEqual(self.client.get("/podcasts/custom/nope.xml").status_code, 404)


@skipUnless(HAS_FFMPEG, "ffmpeg is required")
@override_settings(PODCAST_BASE_URL="https://api.example.org")
class CustomEpisodeAudioTests(MediaRootMixin, TestCase):
    NOW = eastern(2026, 10, 17, 9, 0)
    DAY = date(2026, 10, 16)

    def setUp(self):
        self.use_temporary_media_root()
        self.feed, _ = custom.get_or_create_feed("office/morning_prayer", {})
        self.track = make_mp3(self.root / "openai" / "00000000-0000-5000-8000-0000000000bb.mp3", seconds=2)
        self.original = self.track.read_bytes()
        self.data = {
            "modules": [],
            "audio": {"single_track": ["https://x/a.mp3", f"/uploads/openai/{self.track.name}", [], [], []]},
        }
        calendar = SimpleNamespace(all=[FERIA, EDWARD], all_evening=[FERIA, EDWARD], primary=FERIA)
        self.mocks = {}
        for target, value in (
            ("django.utils.timezone.now", self.NOW),
            ("podcasts.custom.get_calendar_date", calendar),
            ("podcasts.custom.audio_builds.schedule", True),
            ("podcasts.builder.render_office_audio", self.data),
        ):
            patcher = patch(target, return_value=value)
            self.mocks[target] = patcher.start()
            self.addCleanup(patcher.stop)
        self.render = self.mocks["podcasts.builder.render_office_audio"]
        self.schedule = self.mocks["podcasts.custom.audio_builds.schedule"]
        self.url = f"/podcasts/custom/{self.feed.token}/{self.DAY:%Y-%m-%d}.mp3"

    def test_serves_the_shared_track_untouched_with_ranges(self):
        custom.record(
            self.feed,
            custom.as_podcast_feed(self.feed),
            self.DAY,
            self.mocks["podcasts.custom.get_calendar_date"].return_value,
            self.data,
        )
        self.render.reset_mock()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.original)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        partial = self.client.get(self.url, HTTP_RANGE="bytes=0-99")
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial["Content-Length"], "100")
        self.render.assert_not_called()  # a recorded, present track needs no office render
        self.assertEqual(self.track.read_bytes(), self.original)  # never tagged or re-encoded
        self.assertFalse((self.root / "podcasts").exists())

    def test_a_new_day_renders_without_synthesizing(self):
        def render(feed, day):
            # In the request: speech is deferred, but existing clips may be joined.
            self.assertTrue(audio_builds.generation_deferred())
            self.assertTrue(audio_builds.ASSEMBLY_ALLOWED.get())
            return self.data

        self.render.side_effect = render
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.original)
        episode = CustomPodcastEpisode.objects.get()
        self.assertEqual(episode.track_filename, f"openai/{self.track.name}")
        self.assertEqual(episode.file_size, len(self.original))
        self.assertAlmostEqual(episode.duration, 2, delta=0.2)
        self.assertEqual(episode.title, "Friday, October 16, 2026: Edward the Confessor, King of England, 1066")
        self.schedule.assert_not_called()

    def test_a_cleaned_up_track_is_reassembled(self):
        custom.record(
            self.feed,
            custom.as_podcast_feed(self.feed),
            self.DAY,
            self.mocks["podcasts.custom.get_calendar_date"].return_value,
            self.data,
        )
        self.track.unlink()

        def reassemble(feed, day):
            self.track.write_bytes(self.original)
            return self.data

        self.render.side_effect = reassemble
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.render.assert_called_once()

    def test_503_and_one_background_build_when_clips_are_missing(self):
        self.render.side_effect = audio_builds.AudioNotReady()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "60")
        self.schedule.assert_called_once()
        self.assertEqual(self.schedule.call_args.args[0], custom.build_identity(self.feed, self.DAY))
        self.assertFalse(CustomPodcastEpisode.objects.exists())

    def test_only_days_in_the_window(self):
        self.assertEqual(self.client.get(f"/podcasts/custom/{self.feed.token}/2026-10-18.mp3").status_code, 404)
        self.assertEqual(self.client.get(f"/podcasts/custom/{self.feed.token}/2026-10-09.mp3").status_code, 404)
        self.render.assert_not_called()

    def test_background_build_records_the_day(self):
        self.assertTrue(custom.build_episode(self.feed.pk, self.DAY))
        self.render.assert_called_once()
        self.assertTrue(CustomPodcastEpisode.objects.filter(date=self.DAY).exclude(track_filename="").exists())
        self.assertTrue(custom.build_episode(self.feed.pk, self.DAY))
        self.render.assert_called_once()  # already recorded
        self.assertFalse((self.root / "podcasts").exists())

    def test_eucharist_days_without_readings_have_no_episode(self):
        eucharist, _ = custom.get_or_create_feed("readings/holy_eucharist", {})
        with patch("podcasts.builder.has_proper_eucharist", return_value=False):
            self.assertTrue(custom.build_episode(eucharist.pk, self.DAY))
            response = self.client.get(f"/podcasts/custom/{eucharist.token}/{self.DAY:%Y-%m-%d}.mp3")
        self.assertEqual(response.status_code, 404)
        self.render.assert_not_called()
        self.assertEqual(eucharist.episodes.get().track_filename, "")


def fake_modules(office):
    """Two modules; the Lord's Prayer follows ``language_style_for_our_father``."""
    our_father = (
        "Our Father, who art in heaven, hallowed be thy Name."
        if office.settings["language_style_for_our_father"] == "traditional"
        else "Our Father in heaven, hallowed be your Name."
    )
    return [
        SimpleNamespace(
            json={
                "name": "Opening Sentence",
                "lines": [
                    {"id": "opening_1", "line_type": "leader", "content": "O Lord, open our lips;"},
                    {
                        "id": "opening_2",
                        "line_type": "congregation",
                        "content": "And our mouth shall proclaim your praise.",
                    },
                ],
            }
        ),
        SimpleNamespace(
            json={
                "name": "The Lord's Prayer",
                "lines": [{"id": "pater_1", "line_type": "leader", "content": our_father}],
            }
        ),
    ]


@skipUnless(HAS_FFMPEG, "ffmpeg is required")
@override_settings(PODCAST_BASE_URL="https://api.example.org")
class SharedClipTests(MediaRootMixin, TestCase):
    """Custom feeds go through the real office view and audio pipeline, sharing every clip.

    Only the office text (two small modules) and the TTS provider are faked;
    the view, settings, clip keys, silence gaps, and combined track are real.
    """

    def setUp(self):
        self.use_temporary_media_root()
        create_setting_options(extra={"language_style_for_our_father": ["contemporary"]})
        cache.clear()
        self.addCleanup(cache.clear)
        self.fixture = make_mp3(self.root / "fixture" / "clip.mp3", seconds=1)
        self.spoken = []

        def synthesize(voice, text, file_path):
            self.spoken.append(text)
            shutil.copyfile(self.fixture, file_path)
            return []

        def bare_office(office, request, year, month, day):
            office.settings = Settings(request)
            office.date = SimpleNamespace(primary=FERIA, all=[FERIA], all_evening=[FERIA])

        provider = get_tts_provider("openai")
        calendar = SimpleNamespace(all=[FERIA], all_evening=[FERIA], primary=FERIA)
        for patcher in (
            patch.object(index, "TTS_PROVIDER", provider),
            patch.object(provider, "synthesize", side_effect=synthesize),
            patch.object(index.Office, "__init__", bare_office),
            patch.object(index.MorningPrayer, "get_modules", fake_modules),
            patch("podcasts.custom.get_calendar_date", return_value=calendar),
            # Background builds run at once, in this thread.
            patch("podcasts.custom.audio_builds.schedule", side_effect=lambda identity, build: build() or True),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.day = custom.window()[0]

    def custom_audio(self, raw_settings):
        feed, _ = custom.get_or_create_feed("office/morning_prayer", raw_settings)
        return feed, self.client.get(f"/podcasts/custom/{feed.token}/{self.day:%Y-%m-%d}.mp3")

    def test_same_settings_as_a_public_feed_play_its_combined_track(self):
        public = builder.render_office_audio(catalog.get_feed("morning-prayer"), self.day)["audio"]
        public_track = self.root / public["single_track"][1].removeprefix("/uploads/")
        before = public_track.read_bytes()
        spoken = len(self.spoken)
        self.assertEqual(spoken, 3)

        feed, response = self.custom_audio(dict(catalog.CONTEMPORARY_SETTINGS))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), before)
        self.assertEqual(feed.episodes.get().track_filename, public["single_track"][1].removeprefix("/uploads/"))
        self.assertEqual(len(self.spoken), spoken)  # nothing new was synthesized
        self.assertEqual(public_track.read_bytes(), before)  # and the shared track is untouched
        self.assertFalse((self.root / "podcasts").exists())

    def test_one_different_setting_reuses_every_other_clip(self):
        public = builder.render_office_audio(catalog.get_feed("morning-prayer"), self.day)["audio"]
        self.spoken.clear()

        feed, response = self.custom_audio({"language_style_for_our_father": "contemporary"})
        self.assertEqual(response.status_code, 503)  # one clip to synthesize, in the background
        self.assertEqual(self.spoken, ["Our Father in heaven, hallowed be your Name."])
        response = self.client.get(f"/podcasts/custom/{feed.token}/{self.day:%Y-%m-%d}.mp3")
        self.assertEqual(response.status_code, 200)

        mine = builder.render_office_audio(custom.as_podcast_feed(feed), self.day)["audio"]
        public_clips = [track["path"] for track in public["tracks"]]
        my_clips = [track["path"] for track in mine["tracks"]]
        self.assertEqual(my_clips[:2], public_clips[:2])  # the same clip files (same keys)
        self.assertNotEqual(my_clips[2], public_clips[2])
        self.assertNotEqual(mine["single_track"][1], public["single_track"][1])
        self.assertEqual(feed.episodes.get().track_filename, mine["single_track"][1].removeprefix("/uploads/"))
        self.assertEqual(len(self.spoken), 1)
        self.assertFalse((self.root / "podcasts").exists())


class CustomCatalogTests(TestCase):
    def test_the_landing_page_gets_the_builder_options(self):
        data = self.client.get("/api/v1/podcasts").json()
        self.assertEqual([group["slug"] for group in data["custom"]["types"]], ["daily-office", "family", "readings"])
        self.assertEqual(data["custom"]["readings_settings"]["choices"]["translation"], ["esv", "kjv"])

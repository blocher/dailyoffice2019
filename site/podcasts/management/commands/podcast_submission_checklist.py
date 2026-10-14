from django.core.management.base import BaseCommand

from podcasts import catalog, rss
from podcasts.models import PodcastDirectoryListing, PodcastEpisode

# Directories that need a one-time submission by the show's owner, in the
# order to do them. Each sends a code to the feed's owner email
# (feedback@dailyoffice2019.com) or needs an account. Apps not listed (Overcast,
# Castro, Pocket Casts, Podcast Addict, AntennaPod, Goodpods, Player FM, ...)
# find shows through Apple Podcasts and Podcast Index once those list them.
# scripts/podcast-directories.sh walks through them.
DIRECTORIES = [
    (
        "podcast_index",
        "Podcast Index",
        "notify_podcast_directories --add-to-podcast-index (or https://podcastindex.org/add)",
    ),
    ("apple", "Apple Podcasts", "https://podcastsconnect.apple.com/ → + → New Show → Add a show with an RSS feed"),
    ("spotify", "Spotify", "https://creators.spotify.com/ → Add a new show → Find an existing show → Somewhere else"),
    ("youtube_music", "YouTube Music", "https://studio.youtube.com/ → Create → New podcast → Submit RSS feed"),
    ("amazon", "Amazon Music / Audible", "https://podcasters.amazon.com/ → Add your podcast"),
    ("iheart", "iHeartRadio", "https://www.iheart.com/content/submit-your-podcast/"),
    ("pocket_casts", "Pocket Casts", "https://pocketcasts.com/submit/"),
    ("deezer", "Deezer", "https://podcasters.deezer.com/"),
]


class Command(BaseCommand):
    help = "Print each directory's submission steps with every feed URL, and which listings are recorded."

    def add_arguments(self, parser):
        parser.add_argument(
            "--missing",
            metavar="PLATFORM",
            choices=[platform for platform, _ in PodcastDirectoryListing.PLATFORM_CHOICES],
            help="Only list the feeds not yet listed on PLATFORM, one per line: slug, title, and feed URL, "
            "separated by tabs (for scripts).",
        )

    def handle(self, *args, missing=None, **options):
        listed = set(PodcastDirectoryListing.objects.values_list("feed_slug", "platform"))
        if missing:
            for feed in catalog.FEEDS:
                if (feed.slug, missing) not in listed:
                    self.stdout.write(f"{feed.slug}\t{feed.title}\t{rss.feed_url(feed.slug)}")
            return
        self.stdout.write("Feeds (submit each one; every directory treats a feed as one show):\n")
        for feed in catalog.FEEDS:
            episodes = PodcastEpisode.objects.filter(feed_slug=feed.slug).count()
            self.stdout.write(f"  {feed.title:48} {rss.feed_url(feed.slug)}  ({episodes} episodes)")
        for platform, name, steps in DIRECTORIES:
            missing_feeds = [feed for feed in catalog.FEEDS if (feed.slug, platform) not in listed]
            done = len(catalog.FEEDS) - len(missing_feeds)
            self.stdout.write(f"\n{name}: {done}/{len(catalog.FEEDS)} listed\n  {steps}")
            for feed in missing_feeds:
                self.stdout.write(f"  [ ] {feed.title}: {rss.feed_url(feed.slug)}")
        self.stdout.write(
            "\nWhen a directory approves a show, record its public URL with "
            "`python manage.py record_podcast_listing <feed> <platform> <url>` (or in the admin under "
            "Podcasts › Podcast directory listings); the landing page then links to it."
        )

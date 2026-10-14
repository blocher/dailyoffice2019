import kronos
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from podcasts import catalog, directories
from podcasts.models import PodcastEpisode


@kronos.register("10 * * * *")
class Command(BaseCommand):
    help = (
        "Ping WebSub, Podcast Index, and Overcast for feeds with newly published episodes (production only: "
        "PODCAST_NOTIFY_DIRECTORIES). "
        "--add-to-podcast-index submits every feed to Podcast Index (needs an API key)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Ping every feed, not just those with new episodes.")
        parser.add_argument(
            "--add-to-podcast-index",
            action="store_true",
            help="Submit all feeds to Podcast Index (PODCAST_INDEX_API_KEY/SECRET).",
        )

    def handle(self, *args, **options):
        if options["add_to_podcast_index"]:
            for feed in catalog.FEEDS:
                try:
                    feed_id = directories.add_to_podcast_index(feed.slug)
                except Exception as exc:
                    raise CommandError(f"{feed.slug}: {exc}") from exc
                self.stdout.write(f"{feed.slug}: Podcast Index feed {feed_id}")
            return

        if not settings.PODCAST_NOTIFY_DIRECTORIES:
            self.stdout.write("Directory pings are off outside production (PODCAST_NOTIFY_DIRECTORIES).")
            return
        now = timezone.now()
        pending = PodcastEpisode.objects.filter(published_at__lte=now, notified_at__isnull=True)
        slugs = (
            list(catalog.FEEDS_BY_SLUG) if options["all"] else sorted(set(pending.values_list("feed_slug", flat=True)))
        )
        for slug in slugs:
            failures = {name: error for name, error in directories.notify(slug).items() if error}
            for name, error in failures.items():
                self.stderr.write(f"{slug}: {name} ping failed: {error}")
            self.stdout.write(f"{slug}: notified" + (f" ({len(failures)} failed)" if failures else ""))
        # Pings are a courtesy (directories also poll), so one failure is not retried forever.
        pending.filter(feed_slug__in=slugs).update(notified_at=now)

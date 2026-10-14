from datetime import date, timedelta

import bugsnag
import kronos
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from podcasts import catalog
from podcasts.builder import EpisodeBuildError, build_episode, build_lock


@kronos.register("30 10 * * *")
class Command(BaseCommand):
    help = (
        "Build missing podcast episodes (see site/podcasts/). By default, yesterday through three days "
        "ahead, so each episode exists well before it is published. Existing episodes are never rebuilt."
    )

    def add_arguments(self, parser):
        parser.add_argument("--start-date", type=date.fromisoformat, help="First day (YYYY-MM-DD).")
        parser.add_argument("--days", type=int, default=5, help="Number of days (default: 5).")
        parser.add_argument(
            "--feed", action="append", choices=list(catalog.FEEDS_BY_SLUG), help="Only these feeds (repeatable)."
        )

    def handle(self, *args, **options):
        if options["days"] < 1:
            raise CommandError("--days must be at least 1.")
        start = options["start_date"] or timezone.localdate() - timedelta(days=1)
        days = [start + timedelta(days=offset) for offset in range(options["days"])]
        feeds = [catalog.get_feed(slug) for slug in options["feed"]] if options["feed"] else catalog.FEEDS
        built = skipped = failed = 0
        try:
            with build_lock():
                for day in days:
                    for feed in feeds:
                        label = f"{feed.slug} {day:%Y-%m-%d}"
                        try:
                            episode = build_episode(feed, day)
                        except Exception as exc:
                            failed += 1
                            self.stderr.write(f"FAILED {label}: {type(exc).__name__}: {exc}")
                            try:
                                bugsnag.notify(
                                    exc,
                                    context="build_podcast_episodes",
                                    metadata={"podcast": {"feed": feed.slug, "date": day.isoformat()}},
                                )
                            except Exception:
                                self.stderr.write("Bugsnag notification failed; continuing.")
                            continue
                        if episode is None:
                            skipped += 1
                            self.stdout.write(f"No episode {label} (no proper readings)")
                        else:
                            built += 1
                            self.stdout.write(f"Ready {label}: {episode.title}")
        except EpisodeBuildError as exc:
            raise CommandError(str(exc)) from exc
        summary = f"Podcast episodes: {built} ready, {skipped} not applicable, {failed} failed."
        self.stdout.write(summary)
        if failed:
            raise CommandError(summary)

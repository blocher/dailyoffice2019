from django.core.management.base import BaseCommand

from office.audio_builds import AudioNotReady
from podcasts import catalog
from podcasts.builder import EpisodeBuildError, add_transcript, build_lock
from podcasts.models import PodcastEpisode


class Command(BaseCommand):
    help = (
        "Add timed transcripts (and chapter titles with their psalms, lessons, and canticles) to published "
        "episodes built before transcripts existed. Episode audio is never touched or rebuilt, and nothing is "
        "synthesized: an episode whose clips are gone, or whose office no longer lines up with it, is skipped. "
        "New episodes get their transcript when they are built."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--feed", action="append", choices=list(catalog.FEEDS_BY_SLUG), help="Only these feeds (repeatable)."
        )
        parser.add_argument("--limit", type=int, help="At most this many episodes.")

    def handle(self, *args, **options):
        queryset = PodcastEpisode.objects.filter(transcript=[]).order_by("-date", "feed_slug")
        if options["feed"]:
            queryset = queryset.filter(feed_slug__in=options["feed"])
        if options["limit"]:
            queryset = queryset[: options["limit"]]
        added = skipped = 0
        with build_lock():
            for episode in queryset:
                try:
                    add_transcript(episode)
                except (EpisodeBuildError, AudioNotReady) as exc:
                    skipped += 1
                    reason = str(exc) or "its clips are no longer all on disk"
                    self.stderr.write(f"SKIPPED {episode.feed_slug} {episode.date}: {reason}")
                    continue
                added += 1
                self.stdout.write(f"{episode.feed_slug} {episode.date}: {len(episode.transcript)} cues")
        self.stdout.write(self.style.SUCCESS(f"Transcripts added: {added}, skipped: {skipped}."))

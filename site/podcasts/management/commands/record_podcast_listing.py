from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from podcasts import catalog
from podcasts.models import PodcastDirectoryListing


class Command(BaseCommand):
    help = (
        "Record where a feed is listed once a directory approves it (or correct the link), "
        "so the landing page's Subscribe sheet links to it."
    )

    def add_arguments(self, parser):
        parser.add_argument("feed_slug", choices=list(catalog.FEEDS_BY_SLUG))
        parser.add_argument("platform", choices=[platform for platform, _ in PodcastDirectoryListing.PLATFORM_CHOICES])
        parser.add_argument("url", help="The show's public page, such as https://podcasts.apple.com/us/podcast/…")

    def handle(self, *args, feed_slug, platform, url, **options):
        feed = catalog.get_feed(feed_slug)
        listing = PodcastDirectoryListing.objects.filter(feed_slug=feed_slug, platform=platform).first()
        previous = listing.url if listing else None
        listing = listing or PodcastDirectoryListing(feed_slug=feed_slug, platform=platform)
        listing.url = url.strip()
        try:
            listing.full_clean()
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        where = f"{feed.title} on {listing.get_platform_display()}"
        if listing.url == previous:
            self.stdout.write(f"Already recorded: {where}, {listing.url}")
            return
        listing.save()
        self.stdout.write(f"{'Updated' if previous else 'Recorded'}: {where}, {listing.url}")

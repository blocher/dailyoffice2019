import kronos
from django.core.management.base import BaseCommand
from django.utils import timezone

from churchcal.calendar_feeds import ChurchCalendarFeedService


@kronos.register("5 0 * * *")
class Command(BaseCommand):
    help = "Generate ACNA calendar ICS feed artifacts."

    def handle(self, *args, **options):
        today = timezone.localdate()
        manifest = ChurchCalendarFeedService.ensure_current(today=today, force=True)
        self.stdout.write(
            self.style.SUCCESS(
                "Generated calendar feeds for {} ({})".format(
                    manifest.get("build_date"),
                    ", ".join(str(year) for year in manifest.get("window_start_years", [])),
                )
            )
        )

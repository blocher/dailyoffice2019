import datetime

from django.core.management.base import BaseCommand, CommandError

from office import offline_content


def parse_dates(value):
    """``2026-12-01`` or ``2026-12-01:2026-12-07``."""
    parts = value.split(":")
    if len(parts) > 2:
        raise CommandError("Use --dates FIRST or --dates FIRST:LAST (YYYY-MM-DD).")
    try:
        dates = [datetime.date.fromisoformat(part) for part in parts]
    except ValueError as error:
        raise CommandError(f"Not a date: {error}")
    return dates[0], dates[-1]


class Command(BaseCommand):
    help = (
        "Tell devices to refresh what they downloaded for offline use (see office/offline_content.py). "
        "Admin edits already record a soft change; use this for edits made outside the admin, a deploy "
        "that changes how offices are put together, or to refresh everything now with --urgent."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument("--all", action="store_true", help="Every date.")
        scope.add_argument("--dates", help="One date or a range: 2026-12-01 or 2026-12-01:2026-12-07.")
        parser.add_argument(
            "--urgent",
            action="store_true",
            help="Refresh every downloaded day at the next sync, not only as each day comes near.",
        )
        parser.add_argument("--note", default="", help="Why, for the admin list.")

    def handle(self, *args, **options):
        start = end = None
        if options["dates"]:
            start, end = parse_dates(options["dates"])
        change = offline_content.record_change(
            start_date=start, end_date=end, urgent=options["urgent"], note=options["note"]
        )
        self.stdout.write(f"Recorded offline content change {change}.")

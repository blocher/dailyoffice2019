import kronos
from django.core.management.base import BaseCommand

from patrons.sms import send_due_reminders


@kronos.register("*/30 * * * *")
class Command(BaseCommand):
    help = "Send scheduled patron reminder text messages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Count due messages without sending or logging.")

    def handle(self, *args, **options):
        count = send_due_reminders(dry_run=options["dry_run"])
        action = "Would send" if options["dry_run"] else "Processed"
        self.stdout.write("{} {} patron reminder message(s).".format(action, count))

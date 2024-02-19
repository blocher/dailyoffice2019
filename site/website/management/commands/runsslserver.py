from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run server with SSL"

    def handle(self, *args, **options):
        call_command("runserver_plus", cert="/tmp/cert.crt")

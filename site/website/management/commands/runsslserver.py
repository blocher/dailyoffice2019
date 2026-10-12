from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run server with SSL"

    def add_arguments(self, parser):
        parser.add_argument(
            "addrport", nargs="?", help="Optional port number, or ipaddr:port (default 127.0.0.1:8000)"
        )

    def handle(self, *args, **options):
        addrport = [options["addrport"]] if options.get("addrport") else []
        call_command("runserver_plus", *addrport, cert="/tmp/cert.crt")

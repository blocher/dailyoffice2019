from django.core.cache import cache
from django.core.management.base import BaseCommand

from office import response_cache


class Command(BaseCommand):
    help = (
        "Clear the short-lived office API response cache (OFFICE_API_CACHE_SECONDS) so database "
        "edits show up immediately. Deploys already do this by flushing memcached."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clear the entire default cache (also church-calendar and audio-build entries).",
        )

    def handle(self, *args, **options):
        if options["all"]:
            cache.clear()
            self.stdout.write("Cleared the entire default cache.")
            return
        response_cache.clear()
        self.stdout.write("Cleared cached office API responses.")

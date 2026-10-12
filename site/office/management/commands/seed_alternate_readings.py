from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from office.migrations._alternate_readings_0033 import forward
from office.models import AlternateReading


class Command(BaseCommand):
    help = "Apply the reviewed alternate-reading seed after importing an Office lectionary (local text only)."

    def handle(self, *args, **options):
        with transaction.atomic(), connection.schema_editor() as editor:
            forward(apps, editor)
        self.stdout.write(
            self.style.SUCCESS(f"{AlternateReading.objects.count()} reviewed alternate mappings available.")
        )

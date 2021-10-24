from django.core.management.base import BaseCommand
from office.models import StandardOfficeDay


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        days = StandardOfficeDay.objects.order_by("month", "day").all()
        for day in days:
            print(day.ep_reading_2)

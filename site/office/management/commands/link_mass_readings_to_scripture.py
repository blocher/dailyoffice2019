from django.core.management.base import BaseCommand

from churchcal.models import MassReading
from office.models import Scripture


class Command(BaseCommand):
    help = "Link mass readings to scriptures with foriegn key"

    def handle(self, *args, **options):
        mass_readings = MassReading.objects.all()
        for mass_reading in mass_readings:
            mass_reading.long_scripture = Scripture.objects.filter(passage__iexact=mass_reading.long_citation).first()
            if mass_reading.short_citation:
                mass_reading.short_scripture = Scripture.objects.filter(
                    passage__iexact=mass_reading.short_citation
                ).first()
            mass_reading.save()

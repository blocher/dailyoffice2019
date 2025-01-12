from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from office.models import SettingOption
import csv
import os


class Command(BaseCommand):
    help = "Seeds the setting_string_order field in SettingOption model from a JSON file"

    def handle(self, *args, **options):
        file_name = "office/management/data/settingoption-abbreviation.csv"
        file_path = os.path.join(settings.BASE_DIR, file_name)

        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for item in reader:
                    obj = SettingOption.objects.filter(uuid=item["uuid"]).first()
                    if obj:
                        obj.abbreviation = item["abbreviation"]
                        obj.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully updated SettingOption record with uuid {obj.uuid}")
                        )
                    else:
                        self.stdout.write(self.style.WARNING(f'SettingOption with uuid {item["uuid"]} not found'))
        except FileNotFoundError:
            raise CommandError('File "%s" does not exist' % file_path)

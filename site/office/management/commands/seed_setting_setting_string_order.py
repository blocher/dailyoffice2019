from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from office.models import Setting
import csv
import os


class Command(BaseCommand):
    help = "Seeds the setting_string_order field in Setting model from a JSON file"

    def handle(self, *args, **options):
        file_name = "office/management/data/setting-setting_string_order.csv"
        file_path = os.path.join(settings.BASE_DIR, file_name)

        try:
            with open(file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for item in reader:
                    obj = Setting.objects.filter(name=item["name"]).first()
                    if obj:
                        obj.setting_string_order = item["setting_string_order"]
                        obj.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully updated Setting record with name {obj.name}")
                        )
                    else:
                        self.stdout.write(self.style.WARNING(f'Setting with name {item["name"]} not found'))
        except FileNotFoundError:
            raise CommandError('File "%s" does not exist' % file_path)

import csv
import os
from django.core.management.base import BaseCommand
from office.models import Collect


class Command(BaseCommand):
    help = "Import liturgical prayers from CSV file"

    def handle(self, *args, **options):
        # Define the path to the CSV file
        importer_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "collect_importer"
        )
        csv_file_path = os.path.join(importer_dir, "liturgical_prayers.csv")

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        self.stdout.write(f"Reading from {csv_file_path}")

        with open(csv_file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            updated_count = 0
            not_found_count = 0

            for row in reader:
                uuid = row.get("uuid")
                if not uuid:
                    continue

                try:
                    collect = Collect.objects.get(uuid=uuid)
                except Collect.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Collect not found for UUID: {uuid}"))
                    not_found_count += 1
                    continue

                collect.spanish_title = row.get("spanish_title")

                spanish_content = row.get("spanish_content")
                if spanish_content:
                    if not spanish_content.startswith("<p>"):
                        collect.spanish_text = f"<p>{spanish_content}</p>"
                    else:
                        collect.spanish_text = spanish_content

                english_page = row.get("english_page")
                spanish_page = row.get("spanish_page")

                if english_page != spanish_page:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Page numbers mismatch for {collect.title} ({uuid}): English {english_page}, Spanish {spanish_page}. Using English."
                        )
                    )

                if english_page and english_page != "N/A":
                    try:
                        collect.page_number = int(english_page)
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f"Invalid page number for {collect.title} ({uuid}): {english_page}")
                        )

                collect.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished. Updated: {updated_count}, Not Found: {not_found_count}"))

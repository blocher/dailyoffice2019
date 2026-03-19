"""Import Chinese Bible translations for all scripture passages.

Fetches CUV, CUVS (from BibleGateway) and SIGAO, ZNSIGAO (from CCReadBible)
for all passages that don't already have Chinese translations.
"""
import time

from django.core.management.base import BaseCommand

from bible.passage import Passage
from bible.sources import PassageNotFoundException
from office.models import Scripture


class Command(BaseCommand):
    help = "Import Chinese Bible translations for scripture passages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--translations",
            nargs="+",
            default=["cuvs", "cuv"],
            help="Which translations to import (default: cuvs cuv)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of passages to import (0 = all)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=1.0,
            help="Sleep time between API calls in seconds",
        )

    def handle(self, *args, **options):
        translations = options["translations"]
        limit = options["limit"]
        sleep_time = options["sleep"]

        scriptures = Scripture.objects.all()
        total = scriptures.count()
        imported = 0
        errors = 0
        skipped = 0

        self.stdout.write(f"Processing {total} passages for translations: {translations}")

        for i, scripture in enumerate(scriptures):
            if limit and imported >= limit:
                break

            passage = scripture.passage
            changed = False

            for translation in translations:
                existing = getattr(scripture, translation)
                if existing and existing.strip() not in ("", "-"):
                    continue  # Already has data

                try:
                    result = Passage(passage, source=translation).html
                    if result and result.strip() and result.strip() != "-":
                        setattr(scripture, translation, result.strip())
                        changed = True
                        self.stdout.write(f"  [{i+1}/{total}] {passage} ({translation}): OK")
                    else:
                        setattr(scripture, translation, "-")
                        changed = True
                        self.stdout.write(f"  [{i+1}/{total}] {passage} ({translation}): empty")
                except PassageNotFoundException:
                    setattr(scripture, translation, "-")
                    changed = True
                    self.stdout.write(f"  [{i+1}/{total}] {passage} ({translation}): not found")
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  [{i+1}/{total}] {passage} ({translation}): ERROR - {e}")

                time.sleep(sleep_time)

            if changed:
                scripture.save()
                imported += 1
            else:
                skipped += 1

            if (i + 1) % 50 == 0:
                self.stdout.write(f"Progress: {i+1}/{total} processed, {imported} imported, {skipped} skipped, {errors} errors")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {imported} imported, {skipped} skipped, {errors} errors out of {total} passages."
            )
        )

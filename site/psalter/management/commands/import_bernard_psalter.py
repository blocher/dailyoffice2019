"""Point the psalter from the St. Bernard Psalter, with its tones.

    python manage.py import_bernard_psalter path/to/Bernard-PSALTER.pdf
    python manage.py import_bernard_psalter book.pdf --psalms 23 95 100-102
    python manage.py import_bernard_psalter book.pdf --dry-run --verbose

The St. Bernard Psalter (ed. Ben Jefferies, Nashotah House Press, 2023) points
the 2019 New Coverdale Psalter for plainsong, one tone to each office. It is
copyright and used by permission, so it isn't kept in the repository: give
this command a copy of the PDF (on the server too). Reading it takes about ten
seconds. Running it again is safe; verses an editor has approved are left
alone unless --force is given.

Each verse is stored with the book's marks (bold, italic) copied onto the
app's own text, and the tone of its office. Verses whose wording differs from
the book, or whose marks the tone can't follow exactly, are marked "check" for
a look in the admin (Psalter > Psalm verse pointings).
"""

from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from psalter.chant.bernard import read_book
from psalter.chant.pointing import describe, point_verse
from psalter.chant.service import import_book
from psalter.chant.tones import get_tone
from psalter.management.commands.point_psalms import parse_selection


class Command(BaseCommand):
    help = "Point the psalter (contemporary text) from a PDF of the St. Bernard Psalter."

    def add_arguments(self, parser):
        parser.add_argument("pdf", help="The St. Bernard Psalter as a PDF.")
        parser.add_argument("--psalms", nargs="*", help="Only these psalms, e.g. 23 95 100-102 (default: all).")
        parser.add_argument("--force", action="store_true", help="Replace pointing an editor has approved.")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be stored without saving.")
        parser.add_argument("--verbose", action="store_true", help="Print every verse, not only those to check.")

    def handle(self, *args, **options):
        try:
            book = read_book(options["pdf"])
        except FileNotFoundError as error:
            raise CommandError(str(error)) from error
        if len(book) < 150 and not options["psalms"]:
            self.stderr.write(self.style.WARNING(f"Found only {len(book)} psalms in the PDF."))
        numbers = parse_selection(options["psalms"]) if options["psalms"] else None
        results = import_book(book, numbers, force=options["force"], save=not options["dry_run"])

        totals = Counter()
        tones = Counter()
        for number, verses in results.items():
            if verses:
                tones[get_tone(verses[0].tone).label] += 1
            for result in verses:
                totals["kept (approved)" if result.skipped else result.status] += 1
                if not (options["verbose"] or result.notes):
                    continue
                tone = get_tone(result.tone)
                first, second = point_verse(
                    result.first_half, result.second_half, tone, first_verse=result.verse.number == 1
                )
                style = self.style.SUCCESS if result.status == "book" else self.style.WARNING
                self.stdout.write(
                    f"{number}:{result.verse.number} {style(f'[{result.status}]')} {tone.code} "
                    f"{describe(first)} * {describe(second)}"
                )
                for note in result.notes:
                    self.stdout.write(f"        {note}")

        verb = "Would store" if options["dry_run"] else "Stored"
        summary = ", ".join(f"{count} {status}" for status, count in sorted(totals.items())) or "nothing"
        self.stdout.write(self.style.SUCCESS(f"{verb}: {summary}, in {len(results)} psalms."))
        self.stdout.write(
            "Psalms by tone of their first verse: " + ", ".join(f"{t} {c}" for t, c in tones.most_common())
        )

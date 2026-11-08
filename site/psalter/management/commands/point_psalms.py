"""Point chosen psalms for plainsong with AI stress marking and the dictionary.

    python manage.py point_psalms 23 95 100-102
    python manage.py point_psalms 23 --tone 8.G --runs 3
    python manage.py point_psalms 23 --no-ai --dry-run

Nothing runs without a list of psalms (or --all, which must be asked for).
Results appear in the admin under Psalter > Psalm verse pointings.
"""

from django.core.management.base import BaseCommand, CommandError

from psalter.chant import ai
from psalter.chant.notation import NotationError
from psalter.chant.pointing import describe, point_verse
from psalter.chant.service import point_psalm, publish_changes
from psalter.chant.tones import TONES, get_tone
from psalter.models import Psalm


def parse_selection(values):
    numbers = set()
    for value in values:
        for piece in str(value).replace(" ", "").split(","):
            if not piece:
                continue
            if "-" in piece:
                start, end = piece.split("-", 1)
                if not (start.isdigit() and end.isdigit()) or int(start) > int(end):
                    raise CommandError(f"Not a range of psalms: {piece!r}")
                numbers.update(range(int(start), int(end) + 1))
            elif piece.isdigit():
                numbers.add(int(piece))
            else:
                raise CommandError(f"Not a psalm number: {piece!r}")
    bad = sorted(n for n in numbers if not 1 <= n <= 150)
    if bad:
        raise CommandError(f"Psalms run from 1 to 150: {bad}")
    return sorted(numbers)


class Command(BaseCommand):
    help = "Point chosen psalms (contemporary text) for plainsong tones."

    def add_arguments(self, parser):
        parser.add_argument("psalms", nargs="*", help="Psalm numbers or ranges, e.g. 23 95 100-102")
        parser.add_argument("--all", action="store_true", help="Point the whole psalter (150 psalms).")
        parser.add_argument("--verses", help="Only these verses, e.g. 1-4,7 (with a single psalm).")
        parser.add_argument("--tone", choices=sorted(TONES), help="Set each psalm's tone before pointing.")
        parser.add_argument("--runs", type=int, default=2, help="How many times to ask the AI (default 2).")
        parser.add_argument("--no-ai", action="store_true", help="Use the dictionary only.")
        parser.add_argument("--model", help=f"AI model (default {ai.model_name()}).")
        parser.add_argument("--force", action="store_true", help="Re-point verses already approved.")
        parser.add_argument("--dry-run", action="store_true", help="Show the results without saving them.")

    def handle(self, *args, **options):
        if options["all"] and options["psalms"]:
            raise CommandError("Give psalm numbers or --all, not both.")
        if options["all"]:
            numbers = list(range(1, 151))
        elif options["psalms"]:
            numbers = parse_selection(options["psalms"])
        else:
            raise CommandError("Say which psalms to point, e.g. `point_psalms 23 95 100-102`, or pass --all.")

        verse_numbers = None
        if options["verses"]:
            if len(numbers) != 1:
                raise CommandError("--verses works with a single psalm.")
            verse_numbers = parse_selection(options["verses"]) if options["verses"] else None

        if options["runs"] < 1 and not options["no_ai"]:
            raise CommandError("--runs must be at least 1 (or pass --no-ai).")

        psalms = {p.number: p for p in Psalm.objects.filter(number__in=numbers)}
        missing = [n for n in numbers if n not in psalms]
        if missing:
            raise CommandError(f"These psalms are not in the database: {missing}")

        totals = {}
        for number in numbers:
            psalm = psalms[number]
            if options["tone"] and not options["dry_run"] and psalm.chant_tone != options["tone"]:
                psalm.chant_tone = options["tone"]
                psalm.save(update_fields=["chant_tone"])
                publish_changes(f"Psalm {number} set to tone {options['tone']}")
            tone = get_tone(options["tone"] or psalm.chant_tone)
            self.stdout.write(self.style.MIGRATE_HEADING(f"Psalm {number} — {tone.label}"))
            try:
                results = point_psalm(
                    psalm,
                    runs=options["runs"],
                    use_ai=not options["no_ai"],
                    force=options["force"],
                    verse_numbers=verse_numbers,
                    model=options["model"],
                    save=not options["dry_run"],
                )
            except ai.StressMarkingError as error:
                raise CommandError(str(error)) from error
            if not results:
                self.stdout.write("  Nothing to point (all approved, or no verses).")
            for result in results:
                totals[result.status] = totals.get(result.status, 0) + 1
                try:
                    first, second = point_verse(
                        result.first_half, result.second_half, tone, first_verse=result.verse.number == 1
                    )
                    line = f"{describe(first)} * {describe(second)}"
                except NotationError:
                    line = f"{result.first_half} * {result.second_half}"
                style = self.style.SUCCESS if result.status in ("agreed", "approved") else self.style.WARNING
                self.stdout.write(f"  {result.verse.number:>3} {style(f'[{result.status}]')} {line}")
                for note in result.notes:
                    self.stdout.write(f"        {note}")

        summary = ", ".join(f"{count} {status}" for status, count in sorted(totals.items())) or "nothing"
        verb = "Would save" if options["dry_run"] else "Saved"
        self.stdout.write(self.style.SUCCESS(f"{verb}: {summary}."))

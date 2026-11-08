"""Export a pointed psalm for singing-voice software.

    python manage.py export_chant 23
    python manage.py export_chant 23 --format musicxml --tenor 62 --tempo slow

Writes psalm-23-tone-8-G.js (a Synthesizer V Studio script) or
psalm-23-tone-8-G.musicxml in the current directory, or to --out.
See psalter/chant/export.py.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from psalter.chant.export import DEFAULT_TENOR, psalm_notes, to_musicxml, to_synthv_script
from psalter.chant.tones import TONES, get_tone
from psalter.management.commands.point_psalms import parse_selection
from psalter.models import Psalm

# Seconds per pulse (one syllable), as in the app's player.
TEMPOS = {"slow": 0.44, "normal": 0.34, "brisk": 0.27}


class Command(BaseCommand):
    help = "Export a pointed psalm as a Synthesizer V script or MusicXML."

    def add_arguments(self, parser):
        parser.add_argument("psalm", type=int)
        parser.add_argument("--format", choices=["synthv", "musicxml"], default="synthv")
        parser.add_argument("--tone", choices=sorted(TONES), help="Override the psalm's tone.")
        parser.add_argument("--verses", help="Only these verses, e.g. 1-3.")
        parser.add_argument(
            "--tenor",
            type=int,
            default=DEFAULT_TENOR,
            help=f"MIDI pitch of the reciting note (default {DEFAULT_TENOR}, A3).",
        )
        parser.add_argument("--tempo", choices=sorted(TEMPOS), default="normal")
        parser.add_argument("--out", help="File to write.")

    def handle(self, *args, **options):
        psalm = Psalm.objects.filter(number=options["psalm"]).first()
        if not psalm:
            raise CommandError(f"Psalm {options['psalm']} is not in the database.")
        tone = get_tone(options["tone"] or psalm.chant_tone)
        verses = parse_selection([options["verses"]]) if options["verses"] else None
        notes, _ = psalm_notes(psalm, tone=tone, tenor=options["tenor"], verse_numbers=verses)
        if not notes:
            raise CommandError(f"Psalm {psalm.number} has no pointed verses. Run point_psalms {psalm.number} first.")
        pulse = TEMPOS[options["tempo"]]
        if options["format"] == "synthv":
            content, suffix = to_synthv_script(psalm, notes, tone=tone, pulse_seconds=pulse), "js"
        else:
            content, suffix = to_musicxml(psalm, notes, tone=tone, pulse_seconds=pulse), "musicxml"
        path = Path(options["out"] or f"psalm-{psalm.number}-tone-{tone.code.replace('.', '-')}.{suffix}")
        path.write_text(content, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {path} ({len(notes)} notes, {tone.label})."))

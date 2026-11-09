"""Export a pointed psalm for singing-voice software.

    python manage.py export_chant 23
    python manage.py export_chant 23 --format musicxml --tenor 62 --tempo slow
    python manage.py export_chant 23 --format musescore

Writes psalm-23-tone-8-G.js (a Synthesizer V Studio script),
psalm-23-tone-8-G.musicxml, or psalm-23-tone-8-G.mscz (a MuseScore Studio
score set to sing with Cantai's men's choir, or with the voice of
--sound-from, a score saved with another voice chosen in MuseScore's mixer)
in the current directory, or to --out. The MuseScore score needs MuseScore
Studio installed; open it there and Cantai renders the voice.
See psalter/chant/export.py.
"""

import subprocess
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from psalter.chant.export import (
    CANTAI_MALE_CHOIR,
    DEFAULT_TENOR,
    MSCORE,
    psalm_notes,
    set_musescore_sound,
    sound_from_score,
    to_musicxml,
    to_synthv_script,
)
from psalter.chant.tones import TONES, get_tone
from psalter.management.commands.point_psalms import parse_selection
from psalter.models import Psalm

# Seconds per pulse (one syllable), as in the app's player.
TEMPOS = {"slow": 0.44, "normal": 0.38, "brisk": 0.3}


class Command(BaseCommand):
    help = "Export a pointed psalm as a Synthesizer V script or MusicXML."

    def add_arguments(self, parser):
        parser.add_argument("psalm", type=int)
        parser.add_argument("--format", choices=["synthv", "musicxml", "musescore"], default="synthv")
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
        parser.add_argument("--sound-from", help="A MuseScore score whose voice to use (with --format musescore).")
        parser.add_argument("--mscore", default=MSCORE, help="MuseScore Studio's command-line program.")

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
            content = to_musicxml(psalm, notes, tone=tone, pulse_seconds=pulse)
            suffix = "mscz" if options["format"] == "musescore" else "musicxml"
        path = Path(options["out"] or f"psalm-{psalm.number}-tone-{tone.code.replace('.', '-')}.{suffix}")
        if options["format"] == "musescore":
            self.write_musescore(path, content, options)
        else:
            path.write_text(content, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {path} ({len(notes)} notes, {tone.label})."))

    def write_musescore(self, path, musicxml, options):
        sound = sound_from_score(options["sound_from"]) if options["sound_from"] else CANTAI_MALE_CHOIR
        if not Path(options["mscore"]).exists():
            raise CommandError(f"MuseScore Studio is not at {options['mscore']}; pass --mscore.")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "psalm.musicxml"
            source.write_text(musicxml, encoding="utf-8")
            path.unlink(missing_ok=True)
            result = subprocess.run(
                [options["mscore"], str(source), "-o", str(path.resolve())], capture_output=True, text=True
            )
        if not path.exists():
            raise CommandError(f"MuseScore could not convert the score: {result.stderr[-500:]}")
        set_musescore_sound(path, sound)

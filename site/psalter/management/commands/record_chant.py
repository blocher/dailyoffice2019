"""Record pointed psalms sung by Cantai, for the app's chant player.

    python manage.py record_chant 23
    python manage.py record_chant 1-10 --tempo slow
    python manage.py record_chant 23 --sound-from my-voice.mscz

For each psalm: writes a MuseScore score of the pointed verses (as
export_chant --format musescore), has MuseScore Studio render it with Cantai
(Muse Hub signed in; a minute or two a psalm), encodes it as MP3 with ffmpeg,
and stores it on the psalm (media folder, chant/) with the pulse it was sung
at. The API offers the recording only while the pointing, rhythm and pulse
still match what was sung, so re-record after changing any of them.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from psalter.chant.export import (
    CANTAI_MALE_CHOIR,
    MSCORE,
    psalm_notes,
    recording_key,
    sound_from_score,
    to_musicxml,
    write_musescore_score,
)
from psalter.chant.tones import get_tone
from psalter.management.commands.export_chant import TEMPOS
from psalter.management.commands.point_psalms import parse_selection
from psalter.models import Psalm

RENDER_TIMEOUT = 15 * 60


class Command(BaseCommand):
    help = "Record pointed psalms sung by Cantai for the app's chant player."

    def add_arguments(self, parser):
        parser.add_argument("psalms", nargs="+", help="Psalm numbers or ranges, e.g. 23 or 1-10.")
        parser.add_argument("--tempo", choices=sorted(TEMPOS), default="normal")
        parser.add_argument("--sound-from", help="A MuseScore score whose voice to use (default: Cantai men's choir).")
        parser.add_argument("--voice", default="Cantai men's choir", help="How the app names the voice.")
        parser.add_argument("--mscore", default=MSCORE, help="MuseScore Studio's command-line program.")

    def handle(self, *args, **options):
        if not shutil.which("ffmpeg"):
            raise CommandError("ffmpeg is needed to encode the recordings.")
        sound = sound_from_score(options["sound_from"]) if options["sound_from"] else CANTAI_MALE_CHOIR
        pulse = TEMPOS[options["tempo"]]
        for number in parse_selection(options["psalms"]):
            psalm = Psalm.objects.filter(number=number).first()
            if not psalm:
                self.stderr.write(f"Psalm {number} is not in the database.")
                continue
            self.record(psalm, sound, pulse, options)

    def record(self, psalm, sound, pulse, options):
        tone = get_tone(psalm.chant_tone)
        notes, _ = psalm_notes(psalm, tone=tone)
        if not notes:
            self.stderr.write(f"Psalm {psalm.number} has no pointed verses; skipped.")
            return
        verses = list(psalm.psalmverse_set.select_related("pointing").order_by("number"))
        with tempfile.TemporaryDirectory() as directory:
            score = Path(directory) / "psalm.mscz"
            wav = Path(directory) / "psalm.wav"
            mp3 = Path(directory) / "psalm.mp3"
            try:
                write_musescore_score(
                    score,
                    to_musicxml(psalm, notes, tone=tone, pulse_seconds=pulse),
                    sound=sound,
                    mscore=options["mscore"],
                )
            except (FileNotFoundError, RuntimeError) as error:
                raise CommandError(str(error))
            self.stdout.write(f"Psalm {psalm.number}: rendering with MuseScore…")
            subprocess.run(
                [options["mscore"], str(score), "-o", str(wav)], capture_output=True, timeout=RENDER_TIMEOUT
            )
            if not wav.exists() or wav.stat().st_size == 0:
                raise CommandError(f"MuseScore did not render Psalm {psalm.number}.")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(wav),
                    "-codec:a",
                    "libmp3lame",
                    "-b:a",
                    "128k",
                    str(mp3),
                ],
                check=True,
            )
            if psalm.chant_recording:
                psalm.chant_recording.delete(save=False)
            key = recording_key(psalm, verses, pulse)
            with mp3.open("rb") as handle:
                psalm.chant_recording.save(f"psalm-{psalm.number}-{key[:8]}.mp3", File(handle), save=False)
        psalm.chant_recording_pulse = pulse
        psalm.chant_recording_key = key
        psalm.chant_recording_voice = options["voice"]
        psalm.save(
            update_fields=["chant_recording", "chant_recording_pulse", "chant_recording_key", "chant_recording_voice"]
        )
        self.stdout.write(self.style.SUCCESS(f"Psalm {psalm.number}: saved {psalm.chant_recording.name}."))

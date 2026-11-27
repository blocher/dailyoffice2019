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

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
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
RENDER_SECONDS_PER_VERSE = 15
MUSESCORE_LOGS = Path.home() / "Library/Application Support/MuseScore/MuseScore4/logs"
# Cantai sings on Muse's servers. When it can't reach them MuseScore still
# writes the audio, without the choir; these lines in its log say so.
CANTAI_FAILURES = ("Cantai preparation failed", "Cantai render failed")
# Loudness of saved recordings (EBU R128): -16 LUFS integrated, the usual
# level for spoken and sung audio on phones, with true peaks under -1.5 dBTP.
LOUDNESS = -16
TRUE_PEAK = -1.5
LOUDNESS_RANGE = 11


def encode_mp3(wav, mp3):
    """Encode ``wav`` as a 128k MP3 at a standard loudness.

    Cantai renders quietly (peaks near -20 dBFS). Two passes of ffmpeg's
    EBU R128 filter: the first measures, the second raises the whole
    recording by one amount (linear), keeping the choir's dynamics.
    """
    measure = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(wav),
            "-af",
            f"loudnorm=I={LOUDNESS}:TP={TRUE_PEAK}:LRA={LOUDNESS_RANGE}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stderr
    measured = json.loads(measure[measure.rindex("{") : measure.rindex("}") + 1])
    normalize = (
        f"loudnorm=I={LOUDNESS}:TP={TRUE_PEAK}:LRA={LOUDNESS_RANGE}"
        f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
        f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
        f":offset={measured['target_offset']}:linear=true"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav),
            "-af",
            normalize,
            "-ar",
            "44100",  # loudnorm works at 192 kHz; come back down
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(mp3),
        ],
        check=True,
    )


def cantai_failure(since, logs=MUSESCORE_LOGS):
    """Why Cantai didn't sing in the render MuseScore logged after ``since``
    (a timestamp), or "" if it did.

    Cantai logs a line whenever it sings ("Cantai convert cache ..."). With
    none, MuseScore couldn't load the voice (say, after signing in to Muse Hub
    again) and quietly played its basic sound instead, which has no words.
    """
    if not logs.is_dir():
        return ""
    sang = False
    for log in sorted(logs.glob("*.log"), key=lambda path: path.stat().st_mtime):
        if log.stat().st_mtime < since:
            continue
        for line in log.read_text(errors="replace").splitlines():
            for failure in CANTAI_FAILURES:
                if failure in line:
                    return line[line.index(failure) :][:160]
            sang = sang or "Cantai convert" in line
    if not sang:
        return "MuseScore didn't load Cantai and used its basic sound, which has no words"
    return ""


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
        notes, _ = psalm_notes(psalm)  # each verse to its own tone
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
            started = time.time()
            # Cantai takes a few seconds a verse; Psalm 119 needs longer.
            timeout = max(RENDER_TIMEOUT, len(verses) * RENDER_SECONDS_PER_VERSE)
            try:
                subprocess.run([options["mscore"], str(score), "-o", str(wav)], capture_output=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                failure = cantai_failure(started) or "no log line"
                raise CommandError(
                    f"Psalm {psalm.number}: MuseScore was still rendering after {timeout // 60} minutes, "
                    f"so nothing was saved ({failure})."
                )
            if not wav.exists() or wav.stat().st_size == 0:
                raise CommandError(f"MuseScore did not render Psalm {psalm.number}.")
            failure = cantai_failure(started)
            if failure:
                raise CommandError(
                    f"Psalm {psalm.number}: Cantai didn't sing it, so nothing was saved ({failure}). "
                    "Is Muse Hub open and signed in? Try again in a while."
                )
            encode_mp3(wav, mp3)
            if psalm.chant_recording:
                psalm.chant_recording.delete(save=False)
            key = recording_key(psalm, verses, pulse)
            with mp3.open("rb") as handle:
                # Named by its sound, so a new recording (another voice or
                # reverb) never comes from a cache of the old one.
                digest = hashlib.sha1(handle.read()).hexdigest()[:10]
                handle.seek(0)
                psalm.chant_recording.save(f"psalm-{psalm.number}-{digest}.mp3", File(handle), save=False)
        psalm.chant_recording_pulse = pulse
        psalm.chant_recording_key = key
        psalm.chant_recording_voice = options["voice"]
        psalm.save(
            update_fields=["chant_recording", "chant_recording_pulse", "chant_recording_key", "chant_recording_voice"]
        )
        self.stdout.write(self.style.SUCCESS(f"Psalm {psalm.number}: saved {psalm.chant_recording.name}."))

"""Export a pointed psalm for singing-voice software.

Builds one timeline of sung notes from the pointing, with the same rhythm as
the app's player (app/src/helpers/chantPlayer.js): the lengths and the breaths
at commas from ``pointing.rhythm``, two pulses' rest at the asterisk and one
between verses. It writes it as:

* a Synthesizer V Studio script (JavaScript) that writes the notes and
  lyrics into the open project when run from its Scripts menu, or
* MusicXML, which Synthesizer V and most notation programs import, or
* a MuseScore Studio score (MusicXML converted by MuseScore's command line)
  set to sing with a Cantai voice; see ``set_musescore_sound``.

Lyrics follow Synthesizer V's conventions: a word sung over several notes
has the whole word on its first syllable's note and ``+`` on each later
syllable's; a syllable held over several notes has ``-`` on the extra ones.
"""

import json
import re
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

from psalter.chant.notation import is_valid
from psalter.chant.pointing import point_verse, rhythm
from psalter.chant.service import verse_texts
from psalter.chant.tones import gabc_pitches, get_tone

REST_AT_ASTERISK = 2
REST_BETWEEN_VERSES = 1
DEFAULT_TENOR = 57  # A below middle C: comfortable for most voices

_LETTERS = re.compile(r"[^A-Za-zÀ-ɏ']+")
# The psalter prints LORD as "Lᴏʀᴅ" with small-capital letters, which lie
# outside the Latin ranges above; fold them (and curly apostrophes) first.
_FOLD = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ’‘", "abcdefghijklmnopqrstuvwyz''")


@dataclass
class SungNote:
    onset: float  # in pulses from the start, on a quarter-pulse grid
    pulses: float
    pitch: int  # MIDI
    lyric: str  # word, "+" (next syllable of the word) or "-" (held)
    syllable: str  # the syllable as printed, for MusicXML and checking
    syllabic: str  # MusicXML: single, begin, middle, end; "" for held notes
    verse: int
    half: int


def _words(pointed):
    words = {}
    for syllable in pointed.syllables:
        words.setdefault(syllable.word_index, []).append(syllable)
    return words


def _clean(text):
    return _LETTERS.sub("", text.translate(_FOLD)).strip("'")


def psalm_notes(psalm, *, tone=None, tenor=DEFAULT_TENOR, verse_numbers=None):
    """The psalm's sung notes and its length in pulses.

    Only verses that have been pointed are included. ``tenor`` puts the
    reciting note at that MIDI pitch.
    """
    tone = tone or get_tone(psalm.chant_tone)
    transpose = tenor - gabc_pitches(tone.mediation.tenor, tone.clef)[0][0]
    verses = psalm.psalmverse_set.select_related("pointing").order_by("number")
    if verse_numbers:
        verses = verses.filter(number__in=verse_numbers)

    notes = []
    time = 0
    pointed_verses = []
    for verse in verses:
        pointing = getattr(verse, "pointing", None)
        first_text, second_text = verse_texts(verse)
        if pointing is None or not (
            is_valid(pointing.first_half_stress, first_text) and is_valid(pointing.second_half_stress, second_text)
        ):
            continue
        pointed_verses.append((verse, pointing))

    for position, (verse, pointing) in enumerate(pointed_verses):
        halves = point_verse(pointing.first_half_stress, pointing.second_half_stress, tone, first_verse=position == 0)
        for half_index, pointed in enumerate(halves):
            words = _words(pointed)
            for syllable, (scale, pause) in zip(pointed.syllables, rhythm(pointed)):
                word = words[syllable.word_index]
                place = word.index(syllable)
                if len(word) == 1:
                    syllabic = "single"
                elif place == 0:
                    syllabic = "begin"
                elif place == len(word) - 1:
                    syllabic = "end"
                else:
                    syllabic = "middle"
                first_lyric = _clean("".join(s.text for s in word)) if place == 0 else "+"
                for i, (pitch, pulses) in enumerate(gabc_pitches(syllable.notes, tone.clef)):
                    pulses *= scale
                    notes.append(
                        SungNote(
                            onset=time,
                            pulses=pulses,
                            pitch=pitch + transpose,
                            lyric=first_lyric if i == 0 else "-",
                            syllable=_clean(syllable.text) if i == 0 else "",
                            syllabic=syllabic if i == 0 else "",
                            verse=verse.number,
                            half=half_index,
                        )
                    )
                    time += pulses
                time += pause
            if half_index == 0:
                time += REST_AT_ASTERISK
        if position < len(pointed_verses) - 1:
            time += REST_BETWEEN_VERSES
    return notes, time


# --- Synthesizer V Studio script --------------------------------------------

SYNTHV_TEMPLATE = """// Psalm {number}, {tone_label}: pointed for plainsong by the Daily Office
// (manage.py export_chant). In Synthesizer V Studio: Scripts > Open Scripts
// Folder, put this file there, Scripts > Rescan, then run it from the Scripts
// menu with a voice on the current track. It adds the psalm's notes and words
// to the track's main group, after anything already there.
//
// Each pulse is an eighth note at {bpm} BPM ({pulse_seconds} s a syllable).

var NOTES = {notes_json};
var PULSE = SV.QUARTER / 2;

function getClientInfo() {{
  return {{
    name: "Daily Office: Psalm {number} ({tone_label})",
    category: "Daily Office",
    author: "The Daily Office",
    versionNumber: 1,
    minEditorVersion: 65540
  }};
}}

function main() {{
  var project = SV.getProject();
  var group = SV.getMainEditor().getCurrentGroup().getTarget();
  var start = 0;
  for (var i = 0; i < group.getNumNotes(); i++) {{
    start = Math.max(start, group.getNote(i).getEnd());
  }}
  if (start > 0) start += SV.QUARTER * 2;
  project.getTimeAxis().addTempoMark(0, {bpm});
  for (var j = 0; j < NOTES.length; j++) {{
    var n = NOTES[j];
    var note = SV.create("Note");
    note.setTimeRange(Math.round(start + n[0] * PULSE), Math.round(n[1] * PULSE));
    note.setPitch(n[2]);
    note.setLyrics(n[3]);
    group.addNote(note);
  }}
  SV.showMessageBox("Psalm {number}", "Added " + NOTES.length + " notes.");
  SV.finish();
}}
"""


def to_synthv_script(psalm, notes, *, tone, pulse_seconds):
    bpm = round(60 / (pulse_seconds * 2), 2)
    compact = [[n.onset, n.pulses, n.pitch, n.lyric] for n in notes]
    return SYNTHV_TEMPLATE.format(
        number=psalm.number,
        tone_label=tone.label,
        bpm=bpm,
        pulse_seconds=pulse_seconds,
        notes_json=json.dumps(compact, separators=(",", ":")),
    )


# --- MusicXML ----------------------------------------------------------------

_STEPS = [
    ("C", 0),
    ("C", 1),
    ("D", 0),
    ("E", -1),
    ("E", 0),
    ("F", 0),
    ("F", 1),
    ("G", 0),
    ("A", -1),
    ("A", 0),
    ("B", -1),
    ("B", 0),
]
# Durations are written in quarter pulses (a pulse is an eighth note), so a
# quarter note is eight divisions. Lengths with no single note value are tied.
_UNITS_PER_PULSE = 4
_TYPES = {
    32: ("whole", 0),
    24: ("half", 1),
    16: ("half", 0),
    12: ("quarter", 1),
    8: ("quarter", 0),
    6: ("eighth", 1),
    4: ("eighth", 0),
    3: ("16th", 1),
    2: ("16th", 0),
    1: ("32nd", 0),
}


def _pitch_xml(midi):
    step, alter = _STEPS[midi % 12]
    octave = midi // 12 - 1
    alter_xml = f"<alter>{alter}</alter>" if alter else ""
    return f"<pitch><step>{step}</step>{alter_xml}<octave>{octave}</octave></pitch>"


def _type_xml(units):
    name, dots = _TYPES[units]
    return f"<type>{name}</type>" + "<dot/>" * dots


def _split(pulses):
    """Note values, in divisions, that add up to a length in pulses."""
    remaining = round(pulses * _UNITS_PER_PULSE)
    parts = []
    while remaining > 0:
        value = next(v for v in _TYPES if v <= remaining)
        parts.append(value)
        remaining -= value
    return parts


def to_musicxml(psalm, notes, *, tone, pulse_seconds):
    """One measure per half-verse, no time signature (chant is unmeasured);
    a pulse is an eighth note."""
    bpm = round(60 / (pulse_seconds * 2), 2)
    measures = []
    current_key = None
    current = []
    time = 0
    for note in notes:
        key = (note.verse, note.half)
        if key != current_key:
            if current:
                measures.append(current)
            current, current_key = [], key
            # Rests between halves and verses go at the start of the next measure.
            if note.onset > time:
                current.append(("rest", note.onset - time))
        current.append(("note", note))
        time = note.onset + note.pulses
    if current:
        measures.append(current)

    parts = []
    for index, measure in enumerate(measures, start=1):
        body = []
        if index == 1:
            body.append(
                f"<attributes><divisions>{_UNITS_PER_PULSE * 2}</divisions><key><fifths>0</fifths></key>"
                '<time print-object="no" symbol="normal"><senza-misura/></time>'
                "<clef><sign>G</sign><line>2</line><clef-octave-change>-1</clef-octave-change></clef></attributes>"
                f'<direction placement="above"><direction-type><words>Psalm {psalm.number}, {escape(tone.label)}</words>'
                f'</direction-type><sound tempo="{bpm}"/></direction>'
            )
        for kind, item in measure:
            if kind == "rest":
                for units in _split(item):
                    body.append(f"<note><rest/><duration>{units}</duration>{_type_xml(units)}</note>")
                continue
            lyric = ""
            if item.syllable:
                lyric = (
                    f'<lyric number="1"><syllabic>{item.syllabic}</syllabic>'
                    f"<text>{escape(item.syllable)}</text></lyric>"
                )
            parts_of_note = _split(item.pulses)
            for i, units in enumerate(parts_of_note):
                ties = []
                if i > 0:
                    ties.append("stop")
                if i < len(parts_of_note) - 1:
                    ties.append("start")
                tie = "".join(f'<tie type="{t}"/>' for t in ties)
                tied = "".join(f'<tied type="{t}"/>' for t in ties)
                notations = f"<notations>{tied}</notations>" if tied else ""
                body.append(
                    f"<note>{_pitch_xml(item.pitch)}<duration>{units}</duration>{tie}{_type_xml(units)}"
                    f"{notations}{lyric if i == 0 else ''}</note>"
                )
        barline = (
            '<barline location="right"><bar-style>light-heavy</bar-style></barline>' if index == len(measures) else ""
        )
        parts.append(f'<measure number="{index}">{"".join(body)}{barline}</measure>')

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
        '<score-partwise version="4.0">'
        f"<work><work-title>Psalm {psalm.number}</work-title></work>"
        '<part-list><score-part id="P1"><part-name>Tenor</part-name>'
        '<score-instrument id="P1-I1"><instrument-name>Tenor</instrument-name>'
        "<instrument-sound>voice.tenor</instrument-sound></score-instrument></score-part></part-list>"
        f'<part id="P1">{"".join(parts)}</part></score-partwise>\n'
    )


# --- MuseScore Studio with Cantai --------------------------------------------

MSCORE = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"

# The Cantai men's choir as MuseScore stores it in a score's audiosettings.json
# (Mixer > Sound > MuseSounds > Cantai > Choir > Choir (Male)).
CANTAI_MALE_CHOIR = {
    "resourceMeta": {
        "attributes": {
            "isOnline": "1",
            "museCategory": "Choir",
            "museName": "Choir (Male)",
            "musePack": "Cantai",
            "museUID": "50406",
            "museVendorName": "Cantai",
            "playbackSetupData": "",
        },
        "hasNativeEditorSupport": False,
        "id": "50406",
        "type": "muse_sampler_sound_pack",
        "vendor": "MuseSounds",
    },
    "unitConfiguration": {},
}

_REVERB = {
    "out": {
        "balance": 0,
        "fxChain": {
            "0": {
                "active": True,
                "chainOrder": 0,
                "resourceMeta": {
                    "attributes": {},
                    "hasNativeEditorSupport": True,
                    "id": "Muse Reverb",
                    "type": "muse_plugin",
                    "vendor": "Muse",
                },
                "unitConfiguration": {},
            }
        },
        "volumeDb": 0,
    },
    "soloMuteState": {"mute": False, "solo": False},
}


def sound_from_score(path):
    """The sound of the first part of a saved MuseScore score, so a voice
    chosen once in MuseScore's mixer can be reused for every psalm."""
    with zipfile.ZipFile(path) as archive:
        settings = json.loads(archive.read("audiosettings.json"))
    for track in settings.get("tracks", []):
        if track.get("instrumentId") != "metronome":
            return track["in"]
    raise ValueError(f"{path} has no sound set for its part.")


def set_musescore_sound(path, sound=CANTAI_MALE_CHOIR, *, instrument="tenor", part="1"):
    """Set the sound of a single-part MuseScore score (.mscz) in place, with
    the hall reverb MuseScore gives new scores."""
    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    settings = {}
    for info, data in entries:
        if info.filename == "audiosettings.json":
            settings = json.loads(data)
    settings["activeSoundProfile"] = "MuseSounds"
    settings["aux"] = [
        _REVERB,
        {"out": {"balance": 0, "fxChain": {}, "volumeDb": 0}, "soloMuteState": {"mute": False, "solo": False}},
    ]
    settings["tracks"] = [
        {
            "instrumentId": instrument,
            "partId": part,
            "in": sound,
            "out": {
                "auxSends": [{"active": True, "signalAmount": 0.3}, {"active": True, "signalAmount": 0.3}],
                "balance": 0,
                "fxChain": {},
                "volumeDb": 0,
            },
            "soloMuteState": {"mute": False, "solo": False},
        }
    ]
    data = json.dumps(settings, indent=4).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        written = False
        for info, content in entries:
            if info.filename == "audiosettings.json":
                content, written = data, True
            archive.writestr(info, content)
        if not written:
            archive.writestr("audiosettings.json", data)

"""The eight Gregorian psalm tones (and the tonus peregrinus), modern forms.

Pitches follow the Solesmes / Liber Usualis forms as transcribed in GABC by
Benjamin Bloomfield's public-domain jgabc project (psalmtone.js). Each part is
written in a small token language borrowed from that project:

* tokens are separated by spaces and hold one or more GABC notes;
* a leading ``'`` marks a note that must fall on an accented syllable;
* a trailing ``r`` marks an "open" note that can carry any number of syllables
  (the reciting note itself, or the return after an accent);
* tokens before the first open note are the intonation.

How English words are fitted to those notes follows the rules for English
pointing in Briggs & Frere, *A Manual of Plainsong* (1902), Introduction II:
the inflection is deferred as late as possible, the accent of an ending may be
followed by one redundant syllable (a dactyl) but no more, and when the last
accent is further back the penultimate note simply takes the penultimate
syllable. See ``psalter.chant.pointing``.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Token:
    notes: str
    accent: bool = False
    open: bool = False


@dataclass(frozen=True)
class TonePart:
    """One half of a tone: the mediation or the ending (termination)."""

    gabc: str
    intonation: tuple = field(default_factory=tuple)
    tenor: str = ""
    cadence: tuple = field(default_factory=tuple)


def parse_part(gabc):
    tokens = []
    for raw in gabc.split():
        accent = raw.startswith("'")
        raw = raw.lstrip("'")
        is_open = raw.endswith("r")
        notes = raw[:-1] if is_open else raw
        tokens.append(Token(notes=notes, accent=accent, open=is_open))
    intonation, tenor, cadence = [], "", []
    seen_tenor = False
    for token in tokens:
        if not seen_tenor:
            if token.open and not token.accent:
                tenor = token.notes
                seen_tenor = True
            else:
                intonation.append(token)
            continue
        # Consecutive open notes after an accent ("jr jr") are one return.
        if token.open and cadence and cadence[-1].open:
            continue
        cadence.append(token)
    return TonePart(gabc=gabc, intonation=tuple(intonation), tenor=tenor, cadence=tuple(cadence))


@dataclass(frozen=True)
class Tone:
    code: str
    label: str
    clef: str
    mediation: TonePart
    ending: TonePart

    def as_dict(self):
        return {
            "code": self.code,
            "label": self.label,
            "clef": self.clef,
            "demo": tone_demo(self),
            # The reciting note, so the player can put it at a comfortable pitch.
            "tenor": gabc_pitches(self.mediation.tenor, self.clef)[0][0],
        }


_TONE_SOURCES = {
    # number: (clef, mediation, {ending: termination})
    "1": (
        "c4",
        "f gh hr 'ixi hr 'g hr h.",
        {
            "D": "hr g f 'gh gr gvFED.",
            "D2": "hr g f gr 'gf d.",
            "f": "hr g f 'gh gr gf..",
            "g": "hr g f 'gh gr g.",
            "g2": "hr g f 'g gr ghg.",
            "a": "hr g f 'g hr h.",
        },
    ),
    "2": ("f3", "e f hr 'i hr h.", {"D": "hr g 'e fr f."}),
    "3": (
        "c4",
        "g hj jr 'k jr jr 'ih j.",
        {
            "b": "jr h 'j jr i.",
            "a": "jr h 'j jr ih..",
            "a2": "jr ji hi 'h gr gh..",
            "g": "jr ji hi 'h gr g.",
        },
    ),
    "4": ("c4", "h gh hr g h 'i hr h.", {"g": "hr 'h gr g.", "E": "hr g h ih gr 'gf e."}),
    "5": ("c3", "d f hr 'i hr h.", {"a": "hr 'i gr 'h fr f."}),
    "6": ("c4", "f gh hr 'ixi hr 'g hr h.", {"F": "hr f gh 'g fr f."}),
    "7": (
        "c3",
        "hg hi ir 'k jr 'i jr j.",
        {
            "a": "ir 'j ir 'h hr gf..",
            "b": "ir 'j ir 'h hr g.",
            "c": "ir 'j ir 'h hr gh..",
            "c2": "ir 'j ir 'h hr ih..",
            "d": "ir 'j ir 'h hr gi..",
        },
    ),
    "8": ("c4", "g h jr 'k jr j.", {"G": "jr i j 'h gr g.", "G*": "jr i j 'h gr gh..", "c": "jr h j 'k jr j."}),
}

_ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII"}

TONES = {}
for _number, (_clef, _mediation, _endings) in _TONE_SOURCES.items():
    for _ending, _termination in _endings.items():
        _code = f"{_number}.{_ending}"
        TONES[_code] = Tone(
            code=_code,
            label=f"Tone {_ROMAN[_number]}.{_ending}",
            clef=_clef,
            mediation=parse_part(_mediation),
            ending=parse_part(_termination),
        )

TONES["per"] = Tone(
    code="per",
    label="Tonus peregrinus",
    clef="c4",
    mediation=parse_part("ixhi hr g ixi h 'g fr f."),
    ending=parse_part("gr d 'f fr ed.."),
)

DEFAULT_TONE = "8.G"

TONE_CHOICES = [(code, tone.label) for code, tone in TONES.items()]


def get_tone(code):
    return TONES.get(code or DEFAULT_TONE) or TONES[DEFAULT_TONE]


# --- Pitches -----------------------------------------------------------------
#
# GABC names staff positions a (below the bottom line) to m; the clef says
# which line holds do (c3, c4) or fa (f3). Chant has no fixed pitch, so the
# numbers below put do at middle C (MIDI 60) and the player transposes to a
# comfortable reciting pitch.

_STAFF = "abcdefghijklm"
_LINE_LETTER = {1: "d", 2: "f", 3: "h", 4: "j"}
_DIATONIC = [0, 2, 4, 5, 7, 9, 11]  # do re mi fa sol la ti


def _letter_to_midi(letter, clef, flat=False):
    clef = clef or "c4"
    kind, line = clef[0], int(clef[-1])
    reference = _STAFF.index(_LINE_LETTER[line])
    # Scale degree of the reference line: do (0) for a C clef, fa (3) for F.
    reference_degree = 0 if kind == "c" else 3
    steps = _STAFF.index(letter.lower()) - reference + reference_degree
    octave, degree = divmod(steps, 7)
    midi = 60 + 12 * octave + _DIATONIC[degree]
    return midi - 1 if flat else midi


def gabc_pitches(notes, clef):
    """[(midi, pulses), ...] for the GABC notes sung on one syllable.

    Understands note letters (either case), ``x`` (a flat on the position
    just named, which is not itself sung) and ``.`` (a dot of length: one
    more pulse). Shape and ornament marks (v, w, _, /, ...) are ignored.
    """
    result = []
    flats = set()
    i = 0
    while i < len(notes):
        char = notes[i]
        lower = char.lower()
        if lower in _STAFF:
            if i + 1 < len(notes) and notes[i + 1] == "x":
                flats.add(lower)
                i += 2
                continue
            if i + 1 < len(notes) and notes[i + 1] == "y":
                flats.discard(lower)
                i += 2
                continue
            result.append([_letter_to_midi(lower, clef, flat=lower in flats), 1])
        elif char == "." and result:
            result[-1][1] += 1
        i += 1
    return [tuple(n) for n in result]


def tone_demo(tone, recitation=3):
    """The bare tone, for learning it: intonation, a few reciting notes and
    the mediation; then a few reciting notes and the ending.

    Returns {"first_half": [{"p": [...], "d": [...]}], "second_half": [...]},
    one entry per note group, as the player expects for syllables.
    """

    def half(part, with_intonation):
        groups = []
        if with_intonation:
            groups += [token.notes for token in part.intonation]
        groups += [part.tenor] * recitation
        groups += [token.notes for token in part.cadence]
        out = []
        for notes in groups:
            pitches = gabc_pitches(notes, tone.clef)
            if pitches:
                out.append({"p": [p for p, _ in pitches], "d": [d for _, d in pitches]})
        return out

    return {"first_half": half(tone.mediation, True), "second_half": half(tone.ending, False)}

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
        return {"code": self.code, "label": self.label, "clef": self.clef}


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

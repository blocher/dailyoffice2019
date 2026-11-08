"""Fit a stressed half-verse to a part of a psalm tone.

The engine works back from the end of the half-verse, as a cantor does:

* the final note takes the last syllable;
* each accented note takes the nearest accented syllable before it, and the
  unaccented syllables between it and the next note go on the open "return"
  note that follows it in the tone;
* plain notes before an accent (preparatory notes) take one syllable each,
  stressed or not;
* everything before the inflection is sung on the reciting note, after an
  intonation on the first verse.

The rules for English come from Briggs & Frere, *A Manual of Plainsong*
(1902), Introduction II:

* In an ending, the last accent may be followed by one redundant syllable
  (``dwell together in unity``) but no more. When the last accent lies further
  back (``testimonies``, ``Name of the Lord``) the penultimate note takes the
  penultimate syllable anyway, sung softly.
* A stressed final syllable in an ending simply takes the final note.
* In a mediation, a stressed final monosyllable takes the rising note (the
  "abrupt" mediation), and the return to the reciting note is dropped.
* An earlier accent (the Fifth and Seventh Tones) may stand as far back as the
  sixth syllable from the end, so it allows up to two redundant syllables.
"""

from dataclasses import dataclass, field

from psalter.chant.notation import parse

RECITE = "recite"
INTONATION = "intonation"
PREPARATORY = "preparatory"
ACCENT = "accent"
RETURN = "return"
FINAL = "final"

ENDING_LAST_ACCENT_MAX_RETURN = 1
EARLIER_ACCENT_MAX_RETURN = 2


@dataclass
class PointedSyllable:
    text: str
    accent: bool
    word_index: int
    word_start: bool
    role: str = RECITE
    notes: str = ""


@dataclass
class PointedHalf:
    syllables: list
    inflection_start: int  # index of the first syllable of the inflection
    warnings: list = field(default_factory=list)

    def roles(self):
        return [s.role for s in self.syllables]


def point(notation, part, *, mediation, first_verse=False):
    """Point one notated half-verse to a TonePart. Returns a PointedHalf."""
    syllables = [
        PointedSyllable(text=s.text, accent=s.accent, word_index=s.word_index, word_start=s.word_start)
        for s in parse(notation)
    ]
    for s in syllables:
        s.notes = part.tenor
    warnings = []
    cadence = list(part.cadence)
    position = len(syllables) - 1
    index = len(cadence) - 1

    # The abrupt mediation: a stressed last syllable takes the last accent
    # (with the final note), and the return is dropped.
    if mediation and syllables and syllables[-1].accent:
        last_accent = max((i for i, t in enumerate(cadence) if t.accent), default=None)
        if last_accent is not None and all(not t.accent for t in cadence[last_accent + 1 :]):
            notes = cadence[last_accent].notes + "".join(t.notes for t in cadence[last_accent + 1 :] if not t.open)
            syllables[-1].role = ACCENT
            syllables[-1].notes = notes
            position -= 1
            index = last_accent - 1

    is_last_accent = True
    while index >= 0 and position >= 0:
        token = cadence[index]
        if token.open:
            follows_accent = index > 0 and cadence[index - 1].accent
            if not follows_accent:
                index -= 1
                continue
            accent_token = cadence[index - 1]
            if is_last_accent and mediation:
                max_return = position + 1
            elif is_last_accent:
                max_return = ENDING_LAST_ACCENT_MAX_RETURN
            else:
                max_return = EARLIER_ACCENT_MAX_RETURN
            found = None
            for candidate in range(position, max(-1, position - max_return - 1), -1):
                if syllables[candidate].accent:
                    found = candidate
                    break
            if found is None:
                found = position
                # In an ending this is the Manual's rallentando and is correct;
                # elsewhere an unaccented syllable on a rising note is worth a look.
                if not syllables[found].accent and (mediation or not is_last_accent):
                    warnings.append(f"No accent for the inflection; '{syllables[found].text}' takes it unaccented.")
            for i in range(found + 1, position + 1):
                syllables[i].role = RETURN
                syllables[i].notes = token.notes
            syllables[found].role = ACCENT
            syllables[found].notes = accent_token.notes
            position = found - 1
            index -= 2
            is_last_accent = False
        elif token.accent:
            if not syllables[position].accent and is_last_accent and not mediation:
                pass  # The Manual's rallentando: the penultimate syllable takes it.
            elif not syllables[position].accent:
                warnings.append(f"'{syllables[position].text}' takes an accented note unaccented.")
            syllables[position].role = ACCENT
            syllables[position].notes = token.notes
            position -= 1
            index -= 1
            is_last_accent = False
        else:
            final = index == len(cadence) - 1
            syllables[position].role = FINAL if final else PREPARATORY
            syllables[position].notes = token.notes
            position -= 1
            index -= 1

    if index >= 0 and any(not t.open for t in cadence[: index + 1]):
        warnings.append("Too few syllables for the whole inflection; the first notes are left out.")

    inflection_start = position + 1

    if first_verse and part.intonation:
        needed = len(part.intonation)
        if position + 1 > needed:
            for i, token in enumerate(part.intonation):
                syllables[i].role = INTONATION
                syllables[i].notes = token.notes

    return PointedHalf(syllables=syllables, inflection_start=inflection_start, warnings=warnings)


def point_verse(first_notation, second_notation, tone, *, first_verse=False):
    first = point(first_notation, tone.mediation, mediation=True, first_verse=first_verse)
    second = point(second_notation, tone.ending, mediation=False)
    return first, second


def segments(pointed):
    """Display segments for a pointed half: [{"t": text, "r": role}, ...].

    Roles are "" (sung on the reciting note), "bar" (an empty marker where the
    inflection begins), "intonation", "preparatory", "accent", "return" and
    "final". Spaces and punctuation are plain text so only letters are marked.
    """
    from psalter.chant.notation import split_punctuation

    out = []

    def add(text, role):
        if not text:
            return
        if out and out[-1]["r"] == role and role in ("", RETURN, FINAL):
            out[-1]["t"] += text
        else:
            out.append({"t": text, "r": role})

    for i, syllable in enumerate(pointed.syllables):
        if i and syllable.word_start:
            add(" ", "")
        if i == pointed.inflection_start:
            out.append({"t": "", "r": "bar"})
        role = "" if syllable.role == RECITE else syllable.role
        lead, core, trail = split_punctuation(syllable.text)
        add(lead, "")
        add(core, role)
        add(trail, "")
    return out


def describe(pointed):
    """A plain-text rendering for the terminal and the admin.

    ``|`` marks the start of the inflection, accented notes are in capitals and
    preparatory notes in [brackets]; syllables on the return are joined with
    a dot to the accent before them.
    """
    words = []
    current = ""
    for i, syllable in enumerate(pointed.syllables):
        if i and syllable.word_start:
            words.append(current)
            current = ""
        text = syllable.text
        if syllable.role == ACCENT:
            text = text.upper()
        elif syllable.role in (PREPARATORY, INTONATION):
            text = f"[{text}]"
        if i == pointed.inflection_start:
            text = "| " + text if syllable.word_start else "|" + text
        current += ("-" if current and not syllable.word_start and not current.endswith("|") else "") + text
    words.append(current)
    return " ".join(w for w in words if w)

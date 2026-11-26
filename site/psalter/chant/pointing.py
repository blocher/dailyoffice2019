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

# Rhythm, in pulses (a pulse is one syllable at the chosen tempo). Good
# psalmody moves through the reciting note at the pace of careful speech,
# breathes at the commas, and broadens into the cadence. Lengths stay on a
# quarter-pulse grid so that the MusicXML export can write them as plain notes.
RECITING_LENGTH = 0.75  # each syllable on the reciting note
CADENCE_LENGTH = 1.5  # scales the tone's own lengths from the inflection on
FINAL_LENGTH = 1.25  # the last note: still broadened, but not dragged
PAUSE_AFTER_PUNCTUATION = 0.5  # a breath at a comma or stop inside a half-verse
_PAUSING_PUNCTUATION = set(",;:.!?")


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
    book: bool = False  # pointed from a printed psalter's marks

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


# --- Pointing from a printed psalter --------------------------------------
#
# Book tones (``Tone.book``) are pointed the way the St. Bernard Psalter
# prints them: a bold syllable goes to a ticked note, an italic one to a
# slur, a note in parentheses takes any extra syllables, and every other note
# takes exactly one. ``point_marked`` finds the placement of the syllables on
# the notes that best agrees with the marks (a small dynamic programme over
# syllables and notes); where no placement agrees exactly, it says what it
# had to bend, and the verse is flagged.

POINTED = "pointed"  # on a ticked note: bold in the book
SLUR = "slur"  # over a group of notes: italic in the book
NOTE = "note"  # on a plain note of the inflection

_COST_MARKED_ON_OPEN = 0.3  # bold carried on to a note in parentheses: the book does this
_COST_MARKED_ELSEWHERE = 1.0
_COST_UNMARKED_ON_TICK = 1.0
_COST_SLUR_MISMATCH = 0.5
_COST_MERGE = 4.0  # two notes on one syllable without the book's underline
_COST_DROP_LAST_MEDIATION = 0.5  # the book leaves off the last note of a short mediation
_COST_DROP = 6.0
_COST_STRESS_ON_TICK = 0.6  # without book marks: an unstressed syllable on a ticked note
_COST_STRESS_OFF_TICK = 0.3


def _is_group(token):
    from psalter.chant.tones import gabc_pitches

    return len(gabc_pitches(token.notes, "c4")) > 1


def _syllable_cost(syllable, token, use_marks, final=False):
    """How far putting ``syllable`` on ``token`` disagrees with the marks.

    In the book a bold syllable goes to a ticked note (or runs on to the
    note in parentheses after it), an italic one to a slur (ticked or not),
    and an unmarked one to any other note. The last note may go unmarked.
    """
    group = _is_group(token)
    if use_marks:
        cost = 0.0
        if syllable.pointed or syllable.double:
            if not token.accent:
                cost += _COST_MARKED_ON_OPEN if token.open else _COST_MARKED_ELSEWHERE
        elif syllable.slur:
            if not group:
                cost += _COST_SLUR_MISMATCH + (0 if token.accent else _COST_MARKED_ELSEWHERE)
        elif token.accent and not final:
            cost += _COST_UNMARKED_ON_TICK
        if group and not syllable.slur and not syllable.double:
            cost += _COST_SLUR_MISMATCH
        return cost
    if token.accent and not syllable.accent:
        return _COST_STRESS_ON_TICK
    if syllable.accent and not token.accent:
        return _COST_STRESS_OFF_TICK
    return 0.0


def _align(syllables, cadence, mediation, use_marks):
    """Best placement of ``syllables`` on the ``cadence`` tokens.

    Returns (cost, steps): steps is a list of (kind, syllable index or None,
    token indexes), kind being "take", "merge" or "drop".
    """
    from functools import lru_cache

    n, m = len(syllables), len(cadence)

    @lru_cache(maxsize=None)
    def best(i, j):
        if j == m:
            return (0.0, ()) if i == n else (float("inf"), ())
        token = cadence[j]
        options = []
        if token.open:
            # Parentheses may take nothing more...
            cost, steps = best(i, j + 1)
            options.append((cost, (("skip", None, (j,)),) + steps))
            # ...or another syllable, staying on the same note.
            if i < n:
                cost, steps = best(i + 1, j)
                options.append((cost + _syllable_cost(syllables[i], token, use_marks), (("take", i, (j,)),) + steps))
        else:
            if i < n:
                cost, steps = best(i + 1, j + 1)
                final = j == m - 1
                options.append(
                    (
                        cost + _syllable_cost(syllables[i], token, use_marks, final),
                        (("take", i, (j,)),) + steps,
                    )
                )
                # Two notes on one syllable (skipping any parentheses between).
                k = j + 1
                while k < m and cadence[k].open:
                    k += 1
                if k < m:
                    cost, steps = best(i + 1, k + 1)
                    merge = 0.0 if (use_marks and syllables[i].double) else _COST_MERGE
                    options.append(
                        (
                            cost + merge + _syllable_cost(syllables[i], token, use_marks),
                            (("merge", i, tuple(range(j, k + 1))),) + steps,
                        )
                    )
            # Leave the note out: the book's short mediation, or a last resort.
            drop = _COST_DROP_LAST_MEDIATION if (mediation and j == m - 1) else _COST_DROP
            cost, steps = best(i, j + 1)
            options.append((cost + drop, (("drop", None, (j,)),) + steps))
        return min(options, key=lambda option: option[0])

    return best(0, 0)


def point_marked(notation, part, *, mediation, first_verse=False):
    """Point a half-verse marked from a printed psalter to a book tone's part.

    Without book marks (a verse the book doesn't have, say), it falls back on
    the ``+`` stresses, which is a guess to be reviewed.
    """
    from psalter.chant.notation import has_book_marks

    parsed = parse(notation)
    syllables = [
        PointedSyllable(text=s.text, accent=s.accent, word_index=s.word_index, word_start=s.word_start) for s in parsed
    ]
    for s in syllables:
        s.notes = part.tenor
    use_marks = has_book_marks(notation)
    cadence = list(part.cadence)
    n = len(parsed)
    warnings = []
    if not use_marks:
        warnings.append("No marks from the book; placed by stress alone.")

    # The inflection starts where the marks start (the first note of every
    # book tone is ticked); try every start and keep the cheapest, preferring
    # the latest, as the inflection is deferred as long as it can be. On the
    # first verse the book marks the intonation's slur too; those marks are
    # the intonation's, not the inflection's.
    intoned = len(part.intonation) if first_verse else 0
    best = None
    for start in range(n, -1, -1):
        on_tenor = sum(_COST_MARKED_ELSEWHERE for s in parsed[intoned:start] if use_marks and s.marked)
        cost, steps = _align(tuple(parsed[start:]), tuple(cadence), mediation, use_marks)
        if best is None or cost + on_tenor < best[0]:
            best = (cost + on_tenor, start, steps)
    total, start, steps = best

    for kind, i, token_indexes in steps:
        if i is None:
            if kind == "drop" and not (mediation and token_indexes[0] == len(cadence) - 1):
                warnings.append("Too few syllables for the tone; a note is left out.")
            continue
        index = start + i
        tokens = [cadence[t] for t in token_indexes]
        syllable = syllables[index]
        syllable.notes = "".join(t.notes for t in tokens)
        last = token_indexes[-1] == len(cadence) - 1
        if len(tokens) > 1 or _is_group(tokens[0]):
            syllable.role = SLUR
        elif tokens[0].accent:
            syllable.role = POINTED
        elif last:
            syllable.role = FINAL
        elif tokens[0].open:
            syllable.role = RETURN
        else:
            syllable.role = NOTE
        if use_marks:
            marked = parsed[index]
            if _syllable_cost(marked, tokens[0], True, last) >= _COST_MARKED_ELSEWHERE:
                if marked.marked:
                    warnings.append(f"'{marked.text}' is marked but falls on an unpointed note.")
                else:
                    warnings.append(f"'{marked.text}' falls on a pointed note but isn't marked.")
            if kind == "merge" and not marked.double:
                warnings.append(f"'{marked.text}' takes two notes.")
    if use_marks:
        for s in parsed[intoned:start]:
            if s.marked:
                warnings.append(f"'{s.text}' is marked but is sung on the reciting note.")

    if first_verse and part.intonation:
        needed = len(part.intonation)
        if start > needed:
            for i, token in enumerate(part.intonation):
                syllables[i].role = INTONATION
                syllables[i].notes = token.notes

    return PointedHalf(syllables=syllables, inflection_start=start, warnings=warnings, book=True)


def rhythm(pointed):
    """(length scale, pause after) for each syllable of a pointed half.

    The scale multiplies the tone's lengths for the syllable's notes: shorter
    on the reciting note, broader from the inflection on, and a little less
    broad on the last note so the end doesn't drag. The pause,
    in pulses, follows a syllable that ends in a comma or a stop, except at the
    end of the half-verse, where the asterisk or the end of the verse already
    gives a rest.
    """
    from psalter.chant.notation import split_punctuation

    timing = []
    last = len(pointed.syllables) - 1
    for i, syllable in enumerate(pointed.syllables):
        if syllable.role == RECITE:
            scale = RECITING_LENGTH
        elif syllable.role == INTONATION:
            scale = 1
        elif syllable.role == FINAL or (pointed.book and i == last):
            scale = FINAL_LENGTH
        else:
            scale = CADENCE_LENGTH
        trail = split_punctuation(syllable.text)[2]
        pause = PAUSE_AFTER_PUNCTUATION if i < last and _PAUSING_PUNCTUATION & set(trail) else 0
        timing.append((scale, pause))
    return timing


def point_verse(first_notation, second_notation, tone, *, first_verse=False):
    method = point_marked if tone.book else point
    first = method(first_notation, tone.mediation, mediation=True, first_verse=first_verse)
    second = method(second_notation, tone.ending, mediation=False)
    return first, second


def segments(pointed, clef=None):
    """Display and playback segments for a pointed half.

    Each syllable is its own segment, ``{"t": text, "r": role}``, and with a
    ``clef`` also carries what is sung on it: ``"p"`` (MIDI pitches, do at
    middle C), ``"d"`` (pulses for each, in quarter pulses; see ``rhythm``)
    and, after a comma, ``"w"`` (pulses of rest before the next syllable).
    Spaces and punctuation are separate plain segments with no notes, so only
    letters are marked.

    Roles are "" (sung on the reciting note), "bar" (an empty marker where the
    inflection begins), "intonation", "preparatory", "accent", "return" and
    "final"; book tones use "pointed" (bold in the book), "slur" (italic)
    and "note" instead of "accent" and "preparatory".
    """
    from psalter.chant.notation import split_punctuation
    from psalter.chant.tones import gabc_pitches

    out = []

    def plain(text):
        if not text:
            return
        if out and out[-1]["r"] == "" and "p" not in out[-1]:
            out[-1]["t"] += text
        else:
            out.append({"t": text, "r": ""})

    timing = rhythm(pointed)
    for i, syllable in enumerate(pointed.syllables):
        if i and syllable.word_start:
            plain(" ")
        if i == pointed.inflection_start:
            out.append({"t": "", "r": "bar"})
        role = "" if syllable.role == RECITE else syllable.role
        lead, core, trail = split_punctuation(syllable.text)
        if not core:
            lead, core, trail = "", syllable.text, ""
        plain(lead)
        segment = {"t": core, "r": role}
        if clef:
            pitches = gabc_pitches(syllable.notes, clef)
            scale, pause = timing[i]
            segment["p"] = [p for p, _ in pitches]
            segment["d"] = [d * scale for _, d in pitches]
            if pause:
                segment["w"] = pause
        out.append(segment)
        plain(trail)
    return out


def _upper(text):
    # Small capitals ("Lᴏʀᴅ") have odd upper cases; leave them be.
    return "".join(c.upper() if c.isascii() else c for c in text)


def describe(pointed):
    """A plain-text rendering for the terminal and the admin.

    ``|`` marks the start of the inflection, accented (or, for a book tone,
    pointed) notes are in capitals and preparatory notes in [brackets]; a
    slur is in capitals with a ``~`` after it.
    """
    words = []
    current = ""
    for i, syllable in enumerate(pointed.syllables):
        if i and syllable.word_start:
            words.append(current)
            current = ""
        text = syllable.text
        if syllable.role in (ACCENT, POINTED):
            text = _upper(text)
        elif syllable.role == SLUR:
            text = _upper(text) + "~"
        elif syllable.role in (PREPARATORY, INTONATION):
            text = f"[{text}]"
        if i == pointed.inflection_start:
            text = "| " + text if syllable.word_start else "|" + text
        current += ("-" if current and not syllable.word_start and not current.endswith("|") else "") + text
    words.append(current)
    return " ".join(w for w in words if w)

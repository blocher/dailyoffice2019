"""Stress notation for half-verses.

A half-verse's syllables and accents are stored as the verse text itself with
two marks added, so an editor can read and correct it in the admin:

* ``/`` divides a word into syllables;
* ``+`` comes before an accented (stressed) syllable.

    "the +Lord is my +shep/herd;"
    "and +bring me +forth in the +paths of +right/eous/ness for his +Name's +sake."

Removing both marks must give back the verse text exactly (ignoring runs of
whitespace). Neither character appears in the psalter's text.
"""

import re
from dataclasses import dataclass

MARKS = "+/"
_WORD_CHAR = re.compile(r"[A-Za-z0-9À-ɏ]")


class NotationError(ValueError):
    pass


@dataclass
class Syllable:
    text: str  # as printed, including any punctuation attached to it
    accent: bool
    word_index: int
    word_start: bool  # first syllable of its word
    has_letters: bool = True


def normalize_text(text):
    return " ".join((text or "").split())


def strip_marks(notation):
    return normalize_text(notation).replace("+", "").replace("/", "")


def parse(notation):
    """Split a notated half-verse into syllables.

    Punctuation-only tokens (a dash standing alone, say) attach to the
    preceding syllable so every syllable carries letters.
    """
    syllables = []
    for word_index, word in enumerate(normalize_text(notation).split(" ")):
        if not word:
            continue
        parts = word.split("/")
        first = True
        for part in parts:
            accent = "+" in part
            text = part.replace("+", "")
            if not text:
                continue
            has_letters = bool(_WORD_CHAR.search(text))
            if not has_letters and syllables:
                # Join stray punctuation to the previous syllable.
                previous = syllables[-1]
                joiner = " " if first else ""
                previous.text = f"{previous.text}{joiner}{text}"
                continue
            syllables.append(
                Syllable(text=text, accent=accent, word_index=word_index, word_start=first, has_letters=has_letters)
            )
            first = False
    return syllables


def validate(notation, text):
    """Raise NotationError unless the notation matches the text and is well formed."""
    if strip_marks(notation) != normalize_text(text):
        raise NotationError("The marked text does not match the verse text once + and / are removed.")
    for word in normalize_text(notation).split(" "):
        for part in word.split("/"):
            if part.count("+") > 1:
                raise NotationError(f"More than one + in the syllable {part!r}.")
            if "+" in part and not _WORD_CHAR.search(part.replace("+", "")):
                raise NotationError(f"A + marks a syllable with no letters in {word!r}.")
        if "//" in word or word.startswith("/") or word.endswith("/"):
            raise NotationError(f"Empty syllable in {word!r}.")
    if not parse(notation):
        raise NotationError("No syllables found.")


def is_valid(notation, text):
    try:
        validate(notation, text)
    except NotationError:
        return False
    return True


def word_patterns(notation):
    """Per word: (letters, syllable count, accented syllable indexes)."""
    words = {}
    order = []
    for syllable in parse(notation):
        if syllable.word_index not in words:
            words[syllable.word_index] = [[], 0, []]
            order.append(syllable.word_index)
        entry = words[syllable.word_index]
        if syllable.accent:
            entry[2].append(entry[1])
        entry[0].append(syllable.text)
        entry[1] += 1
    return [("".join(words[i][0]), words[i][1], tuple(words[i][2])) for i in order]


def tail_signature(notation, syllable_count=6):
    """The accents of the last few syllables, the part that decides the pointing.

    For example ``"..x..x"``: one character per syllable from the end of the
    half-verse, ``x`` accented. Two notations that agree here point the same
    way in every tone.
    """
    syllables = parse(notation)[-syllable_count:]
    return "".join("x" if s.accent else "." for s in syllables)


def split_punctuation(text):
    """(leading punctuation, core, trailing punctuation) of a printed syllable."""
    match = re.match(r"^([^A-Za-z0-9À-ɏ]*)(.*?)([^A-Za-z0-9À-ɏ]*)$", text)
    return match.group(1), match.group(2), match.group(3)

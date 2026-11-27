"""Psalm 119's sections, headed by the letters of the Hebrew alphabet.

The 2019 psalter prints each eight-verse section under its letter's name
(Aleph above verse 1, Beth above verse 9, ... Taw above verse 169). The
name belongs to no verse: it is kept as the ``section_heading`` of the verse
the section opens with, never in the verse text, so the text matches the
printed psalter and its chant pointing.
"""

import re

HEBREW_LETTERS = (
    "Aleph",
    "Beth",
    "Gimel",
    "Daleth",
    "He",
    "Waw",
    "Zayin",
    "Heth",
    "Teth",
    "Yodh",
    "Kaph",
    "Lamedh",
    "Mem",
    "Nun",
    "Samekh",
    "Ayin",
    "Pe",
    "Sadhe",
    "Qoph",
    "Resh",
    "Shin",
    "Taw",
)

SECTIONED_PSALM = 119
SECTION_LENGTH = 8

_TRAILING_LETTER = re.compile(r"^(.*\S) ({})\s*$".format("|".join(HEBREW_LETTERS)), re.DOTALL)


def section_letter(verse_number):
    """The letter heading the section that opens with this verse of Psalm 119, or None."""
    if verse_number % SECTION_LENGTH != 1:
        return None
    index = verse_number // SECTION_LENGTH
    return HEBREW_LETTERS[index] if index < len(HEBREW_LETTERS) else None


def split_trailing_letter(text):
    """Split a letter name printed after a verse's last words: ("text", "Beth"), or (text, None)."""
    match = _TRAILING_LETTER.match(text or "")
    if not match:
        return text, None
    return match.group(1), match.group(2)

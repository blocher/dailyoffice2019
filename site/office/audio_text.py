"""Speech-only text preparation; never rewrite the displayed office content."""

import re

from bs4 import BeautifulSoup
from num2words import num2words


NUMBER_MARKER_CLASSES = {"verse-num", "versenum", "verse-number", "chapter-num", "chapternum", "chapter-number"}
# Leave ambiguous numeric dates and chapter:verse references to the speech engine.
# Match them first so their components cannot be mistaken for ordinary quantities.
SPOKEN_NUMBER = re.compile(
    r"(?<![\w])(?:"
    r"(?P<reference>\d+:\d+(?:[-–]\d+(?::\d+)?)?)|"
    r"(?P<date>\d{1,4}(?P<date_separator>[/-])\d{1,2}(?P=date_separator)\d{1,4})|"
    r"(?P<number>\d{1,3}(?:,\d{3})+|\d+)(?P<fraction>\.\d+)?(?P<ordinal>st|nd|rd|th)?"
    r")(?![\w])"
)


def _spoken_number(match):
    if match.group("reference") or match.group("date"):
        return match.group()
    integer = int(match.group("number").replace(",", ""))
    if match.group("ordinal") and not match.group("fraction"):
        return num2words(integer, to="ordinal", lang="en")
    words = num2words(integer, lang="en")
    if match.group("fraction"):
        # Preserve trailing zeroes and avoid float rounding.
        words += " point " + " ".join(num2words(int(digit), lang="en") for digit in match.group("fraction")[1:])
    return words


def reading_text(text):
    """Remove explicit verse/chapter labels, retaining all quantities."""
    soup = BeautifulSoup(str(text or ""), "html.parser")
    for marker in soup.select(", ".join(f".{name}" for name in NUMBER_MARKER_CLASSES)):
        marker.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return text


def expand_spoken_numbers(text):
    """Spell out English quantities after pronunciation overrides, before TTS."""
    return SPOKEN_NUMBER.sub(_spoken_number, text)

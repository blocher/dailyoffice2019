"""Read the pointing and tones of the St. Bernard Psalter from its PDF.

The St. Bernard Psalter (ed. Ben Jefferies, Nashotah House Press, 2nd ed.
2023) prints the 2019 New Coverdale Psalter pointed for plainsong. Its marks
are typefaces: a syllable in **bold** goes to a ticked note of the tone, one in
*italic* to a slur, and one underlined in bold italic takes two notes in a
half-verse too short for the tone. Each office of the thirty-day cycle is sung
to one tone, named at its head ("tone iv.4").

The book is copyright, so its text is not kept in this repository; the
``import_bernard_psalter`` command reads a copy of the PDF and stores the
pointing in the database (``PsalmVersePointing``), with each verse's tone.

The importer keeps the app's own verse text and copies the book's marks onto
it word by word, so small differences of punctuation or spelling don't matter;
words that differ are reported.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from psalter.chant import dictionary
from psalter.chant.tones import BOOK_TONE_NAMES

REGULAR, BOLD, ITALIC, DOUBLE = "r", "b", "i", "u"
MARK_FOR_STYLE = {BOLD: "^", ITALIC: "~", DOUBLE: "="}


@dataclass
class BookWord:
    text: str
    styles: list  # the book's style for each letter
    tone: str  # code in psalter.chant.tones
    page: int
    office: str = ""
    half_break: bool = False  # the book's asterisk follows this word


def _style(fontname):
    font = fontname.split("+")[-1]
    if ("Bold" in font or "Semibold" in font) and "Italic" in font:
        return DOUBLE
    if "Bold" in font:
        return BOLD
    if "Italic" in font:
        return ITALIC
    return REGULAR


def _lines(page):
    """The page's characters grouped into lines, top to bottom.

    Characters share a line when their baselines are within two points (the
    small capitals of "Lord" are smaller but sit on the same baseline; verse
    numbers sit a little higher). A drop capital is a line of its own.
    """
    rows = defaultdict(list)
    for char in page.chars:
        if "ChristensenCaps" in char["fontname"]:
            rows[("cap", char["top"])].append(char)
            continue
        baseline = page.height - char["matrix"][5]
        key = None
        for line in rows:
            if not isinstance(line, tuple) and abs(line - baseline) < 2.0:
                key = line
                break
        rows[key if key is not None else baseline].append(char)
    lines = []
    for chars in rows.values():
        chars.sort(key=lambda c: c["x0"])
        lines.append((min(c["top"] for c in chars), chars))
    lines.sort(key=lambda line: line[0])
    return [chars for _, chars in lines]


_OFFICE = re.compile(r"day\s*(\d+)\s*:\s*(morning|evening)\s*prayer", re.I)
_TONE = re.compile(r"^\s*tone\s+(\S+)\s*$|^\s*(tonus\s+peregrinus)\s*$", re.I)
_RUNNING = re.compile(r"psalter\s*\|\s*day|day\s*\d+\s*\|\s*psalter", re.I)
_PART = re.compile(r"^part\s+[ivxl]+$", re.I)


def read_book(path):
    """{psalm number: [BookWord, ...]}: the book's psalter as marked words.

    Verse numbers, headings, the Gloria Patri and notes are left out; each
    psalm's words run on across offices (Psalm 119 is in several). The app's
    own verse divisions are matched to these words later (``match_psalm``).
    """
    import pdfplumber

    psalms = defaultdict(list)
    psalm = None
    tone = ""
    office = ""
    in_gloria = False
    started = False
    drop_cap = ""

    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_number = page_index + 1
            for chars in _lines(page):
                stripped = " ".join("".join(c["text"] for c in chars).split())
                if not stripped:
                    continue
                if "ChristensenCaps" in chars[0]["fontname"]:
                    drop_cap = stripped
                    in_gloria = False
                    continue
                office_match = _OFFICE.search(stripped)
                if office_match:
                    office = f"Day {office_match.group(1)} {office_match.group(2).title()} Prayer"
                    started = True
                    in_gloria = False
                    continue
                if not started:
                    continue
                if stripped.lower().startswith("selected uses of the psalms"):
                    return dict(psalms)
                sizes = [c["size"] for c in chars if c["text"].strip()]
                tone_match = _TONE.match(stripped)
                if tone_match:
                    tone = BOOK_TONE_NAMES.get((tone_match.group(1) or tone_match.group(2)).lower(), tone)
                    continue
                if stripped.isdigit() and max(sizes) >= 18:
                    psalm = int(stripped)
                    in_gloria = False
                    continue
                if _RUNNING.search(stripped) or _PART.match(stripped) or "|" in stripped:
                    continue  # running heads, "part ii", the Latin incipit and its "lens"
                if stripped.isdigit() and max(sizes) < 18:
                    continue  # page and verse numbers
                if psalm is None or any("Uncial" in c["fontname"] for c in chars):
                    continue
                if stripped.startswith("Glory be to the Father"):
                    in_gloria = True
                    continue
                # Verse numbers are set small; leave them (and footnote marks) out.
                body = [c for c in chars if not (c["size"] < 8 and c["text"].isdigit())]
                if any(c["size"] < 8 and c["text"].isdigit() for c in chars):
                    in_gloria = False
                if in_gloria or all(c["size"] < 11 for c in body if c["text"].strip()):
                    continue
                letters = [c for c in body if c["text"].strip()]
                if len(stripped.split()) > 3 and all(_style(c["fontname"]) == ITALIC for c in letters):
                    continue  # a note on how to sing the psalm
                words = psalms[psalm]
                # A character may hold a ligature ("fi"), so expand it.
                text = "".join(c["text"] for c in body)
                styles = [_style(c["fontname"]) for c in body for _ in c["text"]]
                for match in re.finditer(r"\S+", text):
                    token = match.group(0)
                    if token == "*":
                        if words:
                            words[-1].half_break = True
                        continue
                    if token.endswith("*"):
                        token = token[:-1]
                    letter_styles = [
                        styles[i]
                        for i in range(match.start(), match.start() + len(token))
                        if re.match(r"[^\W\d_]", text[i]) and text[i] not in "’'"
                    ]
                    if drop_cap:
                        token = drop_cap + "\u0000" + token  # resolved against the app's text
                        letter_styles = [REGULAR] + letter_styles
                        drop_cap = ""
                    if not letter_styles:
                        continue
                    words.append(
                        BookWord(token, letter_styles, tone, page_number, office, match.group(0).endswith("*"))
                    )
    return dict(psalms)


# --- Marks onto the app's text --------------------------------------------------

_WORD = re.compile(r"[A-Za-zÀ-ɏᴀ-ᴢɢɪɴʀʏʜʟꜰꜱ'’]+")


def _key(word):
    return re.sub(r"[^a-z]", "", dictionary.plain_letters(word))


def _book_words(chars):
    """[(key, [style of each letter])] for a half-verse of the book."""
    words = []
    for match in re.finditer(r"\S+", "".join(c for c, _ in chars)):
        letters = [
            (chars[i][0], chars[i][1])
            for i in range(match.start(), match.end())
            if re.match(r"[^\W\d_]", chars[i][0]) and chars[i][0] not in "’'"
        ]
        if letters:
            words.append((_key(match.group(0)), [style for _, style in letters]))
    return words


def _mark_word(token, styles):
    """Notate one whitespace-separated token of the app's text.

    ``styles`` (or None) gives the book's style for each letter. Syllable
    divisions fall wherever the style changes, and elsewhere by the
    dictionary; each syllable carries the mark of its first letter.
    """
    out = []
    position = 0
    letter_index = 0
    for match in _WORD.finditer(token):
        separator = token[position : match.start()]
        out.append(separator + "/" if position else separator)
        word = match.group(0)
        letter_positions = [i for i, c in enumerate(word) if c not in "’'"]
        word_styles = None
        if styles is not None:
            word_styles = styles[letter_index : letter_index + len(letter_positions)]
            if len(word_styles) != len(letter_positions):
                word_styles = None
        letter_index += len(letter_positions)
        out.append(_mark_syllables(word, letter_positions, word_styles))
        position = match.end()
    out.append(token[position:])
    return "".join(out)


def _mark_syllables(word, letter_positions, styles):
    """Divide ``word`` into syllables and mark each with the book's style.

    The book's typeface changes inside a word ("right|eous", "eve|ry") show
    where it divides; the dictionary's nearest division moves there, so the
    word keeps the dictionary's count of syllables unless the book plainly
    divides it further.
    """
    pieces = dictionary.syllabify(word)
    cuts = []
    at = 0
    for piece in pieces[:-1]:
        at += len(piece)
        cuts.append(at)
    if styles:
        forced = [
            letter_positions[i]
            for i in range(1, len(styles))
            if styles[i] != styles[i - 1] and (styles[i] != REGULAR or styles[i - 1] != REGULAR)
        ]
        for cut in forced:
            if cut in cuts:
                continue
            free = [c for c in cuts if c not in forced]
            nearest = min(free, key=lambda c: abs(c - cut), default=None)
            if nearest is not None and abs(nearest - cut) <= 2:
                cuts[cuts.index(nearest)] = cut
            else:
                cuts.append(cut)
        cuts = sorted(set(cuts))
        # No syllable without a vowel ("neighbo|r").
        changed = True
        while changed:
            changed = False
            bounds = [0] + cuts + [len(word)]
            for k in range(len(bounds) - 1):
                if not dictionary._has_vowel(word[bounds[k] : bounds[k + 1]]):
                    cuts.remove(bounds[k + 1] if k + 1 < len(bounds) - 1 else bounds[k])
                    changed = True
                    break
    bounds = [0] + sorted(cuts) + [len(word)]
    syllables = []
    for start, stop in zip(bounds, bounds[1:]):
        piece = word[start:stop]
        mark = ""
        if styles:
            first_letter = next((i for i, p in enumerate(letter_positions) if p >= start), None)
            if first_letter is not None and letter_positions[first_letter] < stop:
                mark = MARK_FOR_STYLE.get(styles[first_letter], "")
        syllables.append(mark + piece)
    return "/".join(syllables)


@dataclass
class VerseImport:
    verse: object  # PsalmVerse
    first_half: str
    second_half: str
    tone: str
    page: int = 0
    office: str = ""
    issues: list = field(default_factory=list)


def _resolve_drop_caps(words, known_keys):
    """Join a drop capital to its word ("T" + "each") or keep it apart ("I" "call")."""
    resolved = []
    for word in words:
        if "\u0000" not in word.text:
            resolved.append(word)
            continue
        cap, rest = word.text.split("\u0000", 1)
        joined = cap + rest
        if _key(joined) in known_keys or not _key(rest):
            # The capital is the first letter of the syllable after it.
            styles = word.styles[1:2] + word.styles[1:] if len(word.styles) > 1 else word.styles
            resolved.append(BookWord(joined, styles, word.tone, word.page, word.office, word.half_break))
        else:
            resolved.append(BookWord(cap, word.styles[:1], word.tone, word.page, word.office))
            resolved.append(BookWord(rest, word.styles[1:], word.tone, word.page, word.office, word.half_break))
    return resolved


def match_psalm(verses, words):
    """Copy the book's marks onto the app's verses of one psalm.

    ``verses`` are PsalmVerse objects in order; ``words`` the book's words for
    the psalm (``read_book``). Returns a VerseImport for each verse with text.
    """
    from psalter.chant.notation import normalize_text

    tokens = []  # (verse index, half, text)
    for index, verse in enumerate(verses):
        for half, text in enumerate((verse.first_half, verse.second_half)):
            for token in normalize_text(text).split(" ") if text else []:
                tokens.append((index, half, token))
    keys = [_key(t[2]) for t in tokens]
    words = _resolve_drop_caps(words, set(keys))
    book_keys = [_key(w.text) for w in words]

    styles_for = [None] * len(tokens)
    book_for = [None] * len(tokens)
    issues = defaultdict(list)
    matcher = SequenceMatcher(a=keys, b=book_keys, autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == "equal" or (tag == "replace" and a2 - a1 == b2 - b1):
            for offset in range(a2 - a1):
                word = words[b1 + offset]
                book_for[a1 + offset] = word
                if len(_key(tokens[a1 + offset][2])) == len(word.styles):
                    styles_for[a1 + offset] = word.styles
            if tag == "equal":
                continue
        if a1 == a2 and b2 - b1 > 6 and all(s == REGULAR for w in words[b1:b2] for s in w.styles):
            continue  # a note printed with the psalm ("best sung antiphonally")
        where = tokens[a1][0] if a1 < len(tokens) else tokens[-1][0]
        ours = " ".join(t[2] for t in tokens[a1:a2]) or "nothing"
        theirs = " ".join(w.text for w in words[b1:b2]) or "nothing"
        issues[where].append(f"The book has \u201c{theirs}\u201d where the text has \u201c{ours}\u201d.")
        if tag != "replace" and any(s != REGULAR for w in words[b1:b2] for s in w.styles):
            issues[where].append("A marked word of the book is not in the text.")

    results = []
    tone = words[0].tone if words else ""
    for index, verse in enumerate(verses):
        mine = [i for i, t in enumerate(tokens) if t[0] == index]
        if not mine:
            continue
        matched = [book_for[i] for i in mine if book_for[i] is not None]
        if matched:
            tones = [w.tone for w in matched]
            tone = max(set(tones), key=tones.count)
        halves = []
        for half in (0, 1):
            ids = [i for i in mine if tokens[i][1] == half]
            halves.append(" ".join(_mark_word(tokens[i][2], styles_for[i]) for i in ids))
            # The book's asterisk should follow the last word of the first half.
            if half == 0 and ids and book_for[ids[-1]] is not None and not book_for[ids[-1]].half_break:
                issues[index].append("The book divides this verse at another place.")
        notes = list(issues.get(index, []))
        if not matched:
            notes.append("Not found in the book.")
        results.append(
            VerseImport(
                verse=verse,
                first_half=halves[0],
                second_half=halves[1],
                tone=tone,
                page=matched[0].page if matched else 0,
                office=matched[0].office if matched else "",
                issues=notes,
            )
        )
    return results

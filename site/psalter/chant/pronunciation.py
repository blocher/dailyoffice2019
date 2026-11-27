"""How Cantai should sing words it would otherwise mispronounce.

Cantai sings a word as the first pronunciation its English dictionary (CMU)
gives, whatever the sense: "wind" as in winding a clock, "tears" as in
ripping, "live" as in a live wire. It also guesses at words it doesn't know
("hearken" came out "hear can") and stumbles on some silent letters across a
syllable break ("chas/ten"). The cure is to give it, for singing only, a
spelling it can't misread: one per syllable of the word as the pointing
splits it. The text people read is never changed.

``SPELLINGS`` holds words that are always sung one way in the psalter;
``SPELLINGS_AT`` the heteronyms whose sense depends on the verse ("bend the
bow" but "bow down"). Found by the pronunciation audit of the recordings
(Whisper transcripts lined up with the text, and the CMU dictionary's
heteronyms read in context).
"""

import re

SPELLINGS = {
    # Heteronyms where the psalter always means the second sense.
    "wind": ["winned"],
    "tears": ["tiers"],
    "live": ["liv"],
    "lead": ["leed"],
    "sow": ["so"],
    # Words Cantai doesn't know, or misreads at the syllable break.
    "chasten": ["chay", "sen"],
    "chastened": ["chay", "send"],
    "chastens": ["chay", "sens"],
    "hasten": ["hay", "sen"],
    "hastened": ["hay", "send"],
    "hearken": ["har", "ken"],
    "hearkened": ["har", "kend"],
    "hearkens": ["har", "kens"],
    "agéd": ["ay", "jed"],
    "zeëb": ["ze", "eb"],
    "covetous": ["cuv", "uh", "tus"],
    "zoan": ["zoh", "an"],
}

_WEAPON = ["beau"]
SPELLINGS_AT = {
    # The bow that shoots arrows, not bowing down (which Cantai gets right).
    **{
        (psalm, verse, "bow"): _WEAPON
        for psalm, verse in [
            (7, 13),
            (11, 2),
            (18, 35),
            (21, 12),
            (37, 14),
            (37, 15),
            (44, 7),
            (46, 9),
            (76, 3),
            (78, 58),
        ]
    },
    (78, 10, "bows"): ["beaus"],
    # "the lives of the poor", not "he lives".
    (72, 13, "lives"): ["lyves"],
    (74, 19, "lives"): ["lyves"],
    (68, 21, "wound"): ["woond"],
    (84, 6, "uses"): ["you", "zes"],
}

_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?")


def spelling(psalm_number, verse_number, word):
    """The sung syllables for ``word`` in that verse, or None to sing it as printed."""
    word = word.lower()
    return SPELLINGS_AT.get((psalm_number, verse_number, word)) or SPELLINGS.get(word)


def sung_syllables(psalm_number, notes):
    """Each note's lyric as Cantai should sing it (``SungNote.syllable`` unless
    the word is respelled), in the order of ``notes``."""
    sung = []
    respelled, index = None, 0
    for note in notes:
        if note.lyric not in ("+", "-"):
            respelled, index = spelling(psalm_number, note.verse, note.lyric), 0
        elif note.lyric == "+":
            index += 1
        text = note.syllable
        if respelled and text and index < len(respelled):
            text = respelled[index]
            if note.syllable[:1].isupper():
                text = text[:1].upper() + text[1:]
        sung.append(text)
    return sung


def respellings_in(psalm_number, verses):
    """The respellings that apply to these verses' words, for the recording key:
    changing one re-records only the psalms it touches."""
    from psalter.chant.service import verse_texts

    used = set()
    for verse in verses:
        if getattr(verse, "pointing", None) is None:
            continue
        for text in verse_texts(verse):
            for word in _WORD.findall(text or ""):
                respelled = spelling(psalm_number, verse.number, word)
                if respelled:
                    used.add((verse.number, word.lower(), "/".join(respelled)))
    return sorted(used)

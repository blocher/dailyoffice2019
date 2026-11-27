"""A dictionary baseline for syllables and stress.

Uses the CMU Pronouncing Dictionary (the ``cmudict`` package) for syllable
counts and lexical stress, a list of function words that are unstressed when
they stand alone, and a simple spelling rule to divide words into syllables.

It knows nothing of sense or sentence stress, so it is used two ways: to
cross-check the AI (where they disagree a person should look), and as the
whole answer when the AI is turned off.
"""

import re
from functools import lru_cache

# Monosyllables that normally go unstressed in reading. Pronouns are left out
# when they are often the point of a line (e.g. "you" in "it is you").
FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "nor",
    "of",
    "on",
    "or",
    "our",
    "shall",
    "she",
    "so",
    "than",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "those",
    "to",
    "us",
    "was",
    "we",
    "were",
    "who",
    "whom",
    "will",
    "with",
    "would",
    "you",
    "your",
}

_LETTERS = re.compile(r"[A-Za-zÀ-ɏᴀ-ᴢɢɪɴʀʏʜʟꜰꜱ'’]+")
_VOWELS = "aeiouy"
_DIGRAPHS = ("th", "sh", "ch", "ph", "wh", "gh", "ck", "ng", "qu")


@lru_cache(maxsize=1)
def _cmu():
    try:
        import cmudict
    except ImportError:  # pragma: no cover - the package is in requirements.txt
        return {}
    return cmudict.dict()


# House rules for words whose sung syllables a dictionary can't settle. The
# psalter is sung, so the shorter, flowing form is preferred ("ev-ery",
# "heav-en", "pow-er", one-syllable "fire"); proper names keep every syllable.
SYLLABLE_COUNTS = {
    "israel": 3,
    "israel's": 3,
    "every": 2,
    "everyone": 3,
    "everything": 3,
    "heaven": 2,
    "heavens": 2,
    "power": 2,
    "spirit": 2,
    "fire": 1,
    "hour": 1,
    "our": 1,
    "ours": 1,
    "desire": 2,
    "desires": 2,
    "desired": 2,
    "evil": 2,
    "jerusalem": 4,
}

_FLOWING_ENDINGS = ("ire", "ires", "ired", "our", "ours", "ower", "owers", "ery", "eries")

_SMALL_CAPS = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ", "abcdefghijklmnoprstuvwyz")


def plain_letters(word):
    """Lower case, small capitals and accents folded: "Lᴏʀᴅ's" -> "lord's"."""
    import unicodedata

    word = word.translate(_SMALL_CAPS).replace("’", "'")
    word = unicodedata.normalize("NFKD", word)
    return "".join(c for c in word if not unicodedata.combining(c)).lower()


def _pronunciations(word):
    entries = _cmu()
    word = plain_letters(word).strip("'")
    for candidate in (word, word.replace("'", ""), re.sub(r"'s$", "", word)):
        if candidate in entries:
            return entries[candidate]
    return []


def pronunciation(word):
    """CMU phones for a word, trying a few spellings; None if unknown."""
    found = _pronunciations(word)
    return found[0] if found else None


def lexical_stress(word):
    """(syllable count, primary stress index) from the dictionary, or None.

    The dictionary's first pronunciation is used, or its shortest for words
    like "fire" and "every", then the house rules in ``SYLLABLE_COUNTS``; a
    written "-èd" is always sounded ("bless-èd").
    """
    letters = plain_letters(word).strip("'")
    # Words whose "r" can be sung as one syllable or two ("fire", "power",
    # "every") take the shorter form; others the dictionary's first.
    shorter = letters.endswith(_FLOWING_ENDINGS)
    best = None
    for phones in _pronunciations(word):
        stresses = [p[-1] for p in phones if p[-1].isdigit()]
        if not stresses:
            continue
        primary = stresses.index("1") if "1" in stresses else 0
        if best is None or (shorter and len(stresses) < best[0]):
            best = (len(stresses), primary)
    if letters in SYLLABLE_COUNTS:
        count = SYLLABLE_COUNTS[letters]
        best = (count, min(best[1], count - 1) if best else 0)
    if word.lower().endswith("èd"):
        # "Blessèd", "belovèd": the stem's syllables and one more for "-èd".
        stem = plain_letters(word)[:-2]
        stem_found = lexical_stress(stem)
        stem_count = stem_found[0] if stem_found else max(1, len(_vowel_groups(stem)))
        best = (stem_count + 1, stem_found[1] if stem_found else (best[1] if best else 0))
    return best


def syllable_count(word):
    """How many syllables a word is sung in."""
    found = lexical_stress(word)
    if found:
        return found[0]
    return max(1, len(_vowel_groups(plain_letters(word))))


@lru_cache(maxsize=1)
def _hyphenator():
    try:
        import pyphen
    except ImportError:  # pragma: no cover - the package is in requirements.txt
        return None
    return pyphen.Pyphen(lang="en_US", left=1, right=1)


def _vowel_groups(word, final=True):
    """Spans of vowels; ``final`` says the piece ends the word (so a silent
    "-e" or "-ed" can be dropped)."""
    lower = plain_letters(word)
    final = final and not word.lower().endswith("èd")
    groups = []
    i = 0
    while i < len(lower):
        is_vowel = lower[i] in _VOWELS and not (lower[i] == "y" and i == 0)
        if is_vowel:
            start = i
            while i < len(lower) and lower[i] in _VOWELS:
                i += 1
            groups.append((start, i))
        else:
            i += 1
    # A silent final e ("shame", "made"), but not "-le" after a consonant.
    # A silent "-es" ("blasphemes", "times"), but not after a hissing sound ("faces").
    if (
        final
        and len(groups) > 1
        and lower.endswith("es")
        and groups[-1] == (len(lower) - 2, len(lower) - 1)
        and len(lower) > 3
        and lower[-3] not in "sxzcgi"
        and lower[-4] in _VOWELS
        and not lower.endswith(("ches", "shes"))
    ):
        groups.pop()
    # A silent "-e" ending a piece that has another vowel ("peace|able").
    if not final and len(groups) > 1 and lower.endswith("e") and groups[-1] == (len(lower) - 1, len(lower)):
        if lower[-2] not in _VOWELS and lower[-2] != "l":
            groups.pop()
    if final and len(groups) > 1 and lower.endswith("e") and groups[-1] == (len(lower) - 1, len(lower)):
        if not (lower.endswith("le") and len(lower) > 2 and lower[-3] not in _VOWELS):
            groups.pop()
    # A silent "-ed" ("praised"), except after t or d ("wanted", "blessed" is in the dictionary).
    if final and len(groups) > 1 and lower.endswith("ed") and groups[-1] == (len(lower) - 2, len(lower) - 1):
        if lower[-3:-2] not in ("t", "d"):
            groups.pop()
    return groups


def _has_vowel(piece):
    return any(c in _VOWELS for c in plain_letters(piece))


def syllabify(word, count=None):
    """Divide a word (letters only) into ``count`` syllables (default: as sung).

    Divisions come from the TeX hyphenation patterns (``pyphen``), which
    divide as an English printer would ("shep-herd", "there-fore",
    "right-eous-ness"); where they give too few or too many pieces for the
    sung syllables, pieces are split by their vowels or joined.
    """
    if count is None:
        count = syllable_count(word)
    hyphenator = _hyphenator()
    pieces = hyphenator.inserted(word, hyphen="\x00").split("\x00") if hyphenator else [word]
    # Pieces without a vowel ("b-lessed", "wa-ter-s") belong to a neighbour.
    merged = []
    for piece in pieces:
        if merged and (not _has_vowel(piece) or not _has_vowel(merged[-1])):
            merged[-1] += piece
        else:
            merged.append(piece)
    pieces = [p for p in merged if p] or [word]
    while len(pieces) > count > 0:
        # Join the shortest piece to the shorter of its neighbours.
        i = min(range(len(pieces)), key=lambda k: len(pieces[k]))
        j = i - 1 if i == len(pieces) - 1 or (i > 0 and len(pieces[i - 1]) <= len(pieces[i + 1])) else i + 1
        a, b = sorted((i, j))
        pieces[a : b + 1] = [pieces[a] + pieces[b]]
    while len(pieces) < count:
        # Split the piece with the most vowel groups ("evil" -> "e-vil").
        last = len(pieces) - 1
        i = max(range(len(pieces)), key=lambda k: (len(_vowel_groups(pieces[k], k == last)), len(pieces[k])))
        need = count - len(pieces) + 1
        split = _syllabify_by_vowels(pieces[i], need, final=i == last)
        if len(split) < 2 and i == last:
            # The dictionary sounds an "-e" or "-ed" the spelling rule drops ("wick-ed").
            split = _syllabify_by_vowels(pieces[i], need, final=False)
        if len(split) < 2:
            break
        pieces[i : i + 1] = split
    return pieces


def _syllabify_by_vowels(word, count=None, final=True):
    """Divide a word into syllables by its vowels, ``count`` of them if given."""
    groups = _vowel_groups(word, final)
    if not groups:
        return [word]
    while count and len(groups) > count:
        # Merge the closest pair of vowel groups.
        gaps = [groups[i + 1][0] - groups[i][1] for i in range(len(groups) - 1)]
        i = gaps.index(min(gaps))
        groups[i : i + 2] = [(groups[i][0], groups[i + 1][1])]
    while count and len(groups) < count:
        # Split a run of vowels that the dictionary hears as two ("Zi-on").
        longest = max(range(len(groups)), key=lambda i: groups[i][1] - groups[i][0])
        start, stop = groups[longest]
        if stop - start < 2:
            break
        groups[longest : longest + 1] = [(start, start + 1), (start + 1, stop)]
    cuts = []
    for (_, end), (next_start, _) in zip(groups, groups[1:]):
        cluster = word[end:next_start].lower()
        if cluster.startswith("gh"):
            # "right-eous", "might-y": gh belongs to the vowel before it.
            cuts.append(end + min(len(cluster), 3) if len(cluster) > 2 else end + 2)
        elif len(cluster) <= 1:
            cuts.append(end)
        elif cluster == "ck":
            # "wick-ed", "lock-et": ck closes the syllable before it.
            cuts.append(end + 2)
        elif cluster[0] == cluster[1]:
            # "val-ley", "fol-low".
            cuts.append(end + 1)
        elif len(cluster) >= 3 and cluster[-3:-1] in _DIGRAPHS and cluster[-1] in "lr":
            # "breth-ren".
            cuts.append(next_start - 3)
        elif len(cluster) == 2 and (cluster in _DIGRAPHS or cluster[1] in "lr"):
            # "fa-ther", "re-fresh", "ta-ble": keep the pair with the next vowel.
            cuts.append(end)
        elif len(cluster) >= 3 and cluster[-1] in "lr":
            # "hun-dred", "chil-dren": the last two begin the next syllable.
            cuts.append(next_start - 2)
        else:
            cuts.append(end + 1)
    pieces = []
    previous = 0
    for cut in cuts:
        pieces.append(word[previous:cut])
        previous = cut
    pieces.append(word[previous:])
    return [p for p in pieces if p] or [word]


def word_stress(word):
    """(syllables, accented indexes) for one word on its own."""
    found = lexical_stress(word)
    count, primary = found if found else (syllable_count(word), 0)
    pieces = syllabify(word, count)
    if len(pieces) == 1:
        accented = () if word.lower().strip("'") in FUNCTION_WORDS else (0,)
    else:
        accented = (min(primary, len(pieces) - 1),)
    return pieces, accented


def notate(text):
    """Mark a half-verse with ``/`` and ``+`` from the dictionary alone."""
    out = []
    for token in text.split():
        pieces = []
        position = 0
        for match in _LETTERS.finditer(token):
            separator = token[position : match.start()]
            # "well-being": the hyphen ends a syllable.
            pieces.append(separator + "/" if position else separator)
            syllables, accented = word_stress(match.group(0))
            marked = [("+" if i in accented else "") + s for i, s in enumerate(syllables)]
            pieces.append("/".join(marked))
            position = match.end()
        pieces.append(token[position:])
        out.append("".join(pieces))
    return " ".join(out)


def word_check(word):
    """(syllable count, primary stress index) for cross-checking, or None.

    Only polysyllables found in the dictionary are checked; monosyllables'
    stress depends on the sentence.
    """
    letters = re.sub(r"[^A-Za-zÀ-ɏᴀ-ᴢɢɪɴʀʏʜʟꜰꜱ'’]", "", word)
    found = lexical_stress(letters) if letters else None
    if not found or found[0] < 2:
        return None
    return found

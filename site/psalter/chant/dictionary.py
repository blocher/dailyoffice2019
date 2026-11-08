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

_LETTERS = re.compile(r"[A-Za-zÀ-ɏ']+")
_VOWELS = "aeiouy"
_DIGRAPHS = ("th", "sh", "ch", "ph", "wh", "gh", "ck", "ng", "qu")


@lru_cache(maxsize=1)
def _cmu():
    try:
        import cmudict
    except ImportError:  # pragma: no cover - the package is in requirements.txt
        return {}
    return cmudict.dict()


def pronunciation(word):
    """CMU phones for a word, trying a few spellings; None if unknown."""
    entries = _cmu()
    word = word.lower().strip("'")
    for candidate in (word, word.replace("'", ""), re.sub(r"'s$", "", word)):
        if candidate in entries:
            return entries[candidate][0]
    return None


def lexical_stress(word):
    """(syllable count, primary stress index) from the dictionary, or None."""
    phones = pronunciation(word)
    if not phones:
        return None
    stresses = [p[-1] for p in phones if p[-1].isdigit()]
    if not stresses:
        return None
    primary = stresses.index("1") if "1" in stresses else 0
    return len(stresses), primary


def _vowel_groups(word):
    lower = word.lower()
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
    if len(groups) > 1 and lower.endswith("e") and groups[-1] == (len(lower) - 1, len(lower)):
        if not (lower.endswith("le") and len(lower) > 2 and lower[-3] not in _VOWELS):
            groups.pop()
    # A silent "-ed" ("praised"), except after t or d ("wanted", "blessed" is in the dictionary).
    if len(groups) > 1 and lower.endswith("ed") and groups[-1] == (len(lower) - 2, len(lower) - 1):
        if lower[-3:-2] not in ("t", "d"):
            groups.pop()
    return groups


def syllabify(word, count=None):
    """Divide a word (letters only) into syllables, ``count`` of them if given."""
    groups = _vowel_groups(word)
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
    count, primary = found if found else (None, 0)
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
    letters = re.sub(r"[^A-Za-z']", "", word)
    found = lexical_stress(letters) if letters else None
    if not found or found[0] < 2:
        return None
    return found

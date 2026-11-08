"""Point psalms: combine AI stress marking with the dictionary and save it.

For each verse the AI is asked ``runs`` times. A verse is trusted when every
run marks the last six syllables of both halves the same way (that is the part
that decides where the tone's inflections fall) and the dictionary agrees with
the AI's syllable counts and stresses for the words in that stretch.
Otherwise it is flagged for review with a note saying why.
"""

from dataclasses import dataclass, field

from django.db import transaction

from psalter.chant import ai, dictionary
from psalter.chant.notation import is_valid, normalize_text, parse, tail_signature, word_patterns
from psalter.chant.pointing import point_verse, segments
from psalter.chant.tones import get_tone
from psalter.models import PsalmVerse, PsalmVersePointing

TAIL = 6


def verse_texts(verse):
    return normalize_text(verse.first_half), normalize_text(verse.second_half)


def _tail_words(notation, syllable_count=TAIL):
    """Word patterns for the words that touch the last few syllables."""
    syllables = parse(notation)
    if not syllables:
        return []
    first_word = syllables[max(0, len(syllables) - syllable_count)].word_index
    patterns = word_patterns(notation)
    words = sorted({s.word_index for s in syllables})
    keep = [i for i, w in enumerate(words) if w >= first_word]
    return [patterns[i] for i in keep]


def dictionary_disagreements(notation):
    """Words near the end where the dictionary counts or stresses differently."""
    problems = []
    for word, count, accented in _tail_words(notation):
        check = dictionary.word_check(word)
        if not check:
            continue
        dictionary_count, primary = check
        if dictionary_count != count:
            problems.append(f"'{word}': {count} syllables marked, the dictionary has {dictionary_count}")
        elif primary not in accented:
            problems.append(
                f"'{word}': stress marked on syllable {[a + 1 for a in accented] or 'none'}, the dictionary has {primary + 1}"
            )
    return problems


@dataclass
class VerseResult:
    verse: PsalmVerse
    first_half: str
    second_half: str
    status: str
    notes: list = field(default_factory=list)
    confidence: float = None
    runs: list = field(default_factory=list)
    dictionary_first: str = ""
    dictionary_second: str = ""


def assess(verse, runs):
    """Decide a verse's notation and status from the AI runs (may be empty)."""
    first_text, second_text = verse_texts(verse)
    dictionary_first = dictionary.notate(first_text)
    dictionary_second = dictionary.notate(second_text)
    notes = []

    valid = []
    for i, run in enumerate(runs, start=1):
        problems = []
        if not is_valid(run.get("first_half", ""), first_text):
            problems.append("first half")
        if not is_valid(run.get("second_half", ""), second_text):
            problems.append("second half")
        if problems:
            notes.append(f"AI answer {i} changed the text of the {' and '.join(problems)}; ignored.")
        else:
            valid.append(run)
        if run.get("note"):
            notes.append(f"AI answer {i}: {run['note']}")

    if not runs:
        return VerseResult(
            verse,
            dictionary_first,
            dictionary_second,
            PsalmVersePointing.DICTIONARY,
            notes=["Dictionary only; no AI."],
            dictionary_first=dictionary_first,
            dictionary_second=dictionary_second,
        )
    if not valid:
        notes.append("No usable AI answer; the dictionary's marking is shown.")
        return VerseResult(
            verse,
            dictionary_first,
            dictionary_second,
            PsalmVersePointing.NEEDS_REVIEW,
            notes=notes,
            runs=runs,
            dictionary_first=dictionary_first,
            dictionary_second=dictionary_second,
        )

    chosen = valid[0]
    status = PsalmVersePointing.AGREED
    signatures = {(tail_signature(r["first_half"], TAIL), tail_signature(r["second_half"], TAIL)) for r in valid}
    if len(valid) < len(runs) or len(signatures) > 1:
        status = PsalmVersePointing.NEEDS_REVIEW
        if len(signatures) > 1:
            notes.append(
                "The AI answers disagree near the end of a half-verse: " + " / ".join(sorted(map(str, signatures)))
            )

    for label, notation in (("first half", chosen["first_half"]), ("second half", chosen["second_half"])):
        problems = dictionary_disagreements(notation)
        if problems:
            notes.append(f"Dictionary differs in the {label}: " + "; ".join(problems))
            if status == PsalmVersePointing.AGREED:
                status = PsalmVersePointing.CHECK

    confidences = [r.get("confidence") for r in valid if isinstance(r.get("confidence"), (int, float))]
    confidence = min(confidences) if confidences else None
    if confidence is not None and confidence < 0.6 and status == PsalmVersePointing.AGREED:
        status = PsalmVersePointing.CHECK
        notes.append(f"The AI's confidence is low ({confidence:.2f}).")

    return VerseResult(
        verse,
        chosen["first_half"],
        chosen["second_half"],
        status,
        notes=notes,
        confidence=confidence,
        runs=runs,
        dictionary_first=dictionary_first,
        dictionary_second=dictionary_second,
    )


def collect_runs(psalm_number, verses, runs, *, client=None, model=None):
    """Ask the AI ``runs`` times; returns {verse number: [answer, ...]}."""
    payload = []
    for verse in verses:
        first_text, second_text = verse_texts(verse)
        payload.append({"number": verse.number, "first_half": first_text, "second_half": second_text})
    answers = {verse.number: [] for verse in verses}
    for _ in range(runs):
        result = ai.mark_psalm(psalm_number, payload, client=client, model=model)
        for number in answers:
            if number in result:
                answers[number].append(result[number])
            else:
                answers[number].append({"first_half": "", "second_half": "", "note": "Missing from the answer."})
    return answers


def point_psalm(psalm, *, runs=2, use_ai=True, force=False, verse_numbers=None, client=None, model=None, save=True):
    """Point one psalm's verses. Returns a list of VerseResult.

    Approved verses are left alone unless ``force`` is set.
    """
    verses = list(PsalmVerse.objects.filter(psalm=psalm).select_related("pointing").order_by("number"))
    if verse_numbers:
        verses = [v for v in verses if v.number in set(verse_numbers)]
    if not force:
        verses = [
            v for v in verses if not (hasattr(v, "pointing") and v.pointing.status == PsalmVersePointing.APPROVED)
        ]
    verses = [v for v in verses if v.first_half and v.second_half]
    if not verses:
        return []

    answers = {}
    if use_ai and runs > 0:
        answers = collect_runs(psalm.number, verses, runs, client=client, model=model)

    results = [assess(verse, answers.get(verse.number, [])) for verse in verses]
    if save:
        used_model = (model or ai.model_name()) if answers else ""
        with transaction.atomic():
            for result in results:
                PsalmVersePointing.objects.update_or_create(
                    verse=result.verse,
                    defaults={
                        "first_half_stress": result.first_half,
                        "second_half_stress": result.second_half,
                        "status": result.status,
                        "confidence": result.confidence,
                        "review_notes": "\n".join(result.notes),
                        "ai_model": used_model,
                        "ai_runs": result.runs,
                        "dictionary_first_half": result.dictionary_first,
                        "dictionary_second_half": result.dictionary_second,
                    },
                )
    return results


def chant_for_verse(verse, tone=None, first_verse=None):
    """Display data for one verse, or None if it has not been pointed.

    ``first_verse`` (default: verse 1) adds the tone's intonation. Uses
    ``verse.pointing`` and ``verse.psalm``; select_related both.
    """
    pointing = getattr(verse, "pointing", None)
    if pointing is None:
        return None
    first_text, second_text = verse_texts(verse)
    if not (is_valid(pointing.first_half_stress, first_text) and is_valid(pointing.second_half_stress, second_text)):
        # The verse text was edited after pointing; don't show stale marks.
        return None
    tone = tone or get_tone(verse.psalm.chant_tone)
    first, second = point_verse(
        pointing.first_half_stress,
        pointing.second_half_stress,
        tone,
        first_verse=verse.number == 1 if first_verse is None else first_verse,
    )
    return {
        "first_half": segments(first),
        "second_half": segments(second),
        "status": pointing.status,
        "tone": tone.code,
    }

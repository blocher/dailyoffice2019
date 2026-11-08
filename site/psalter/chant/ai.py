"""Ask a language model to mark syllables and stresses in a psalm.

The model does the part that needs judgment (which syllables carry the
sentence's stress, how words divide) and returns the verse text with ``/`` and
``+`` marks. It never places notes: counting syllables against a tone is left
to ``psalter.chant.pointing``, which is exact.
"""

import json

from django.conf import settings

SYSTEM_PROMPT = """You prepare English psalm texts for singing to Gregorian psalm tones.

For each half-verse you are given, return the same text with two marks added:
- "/" between the syllables of every word of more than one syllable;
- "+" immediately before every syllable that carries a stress when the line is read aloud slowly, distinctly and naturally, as in careful liturgical recitation.

Removing every "+" and "/" from your answer must give back the half-verse exactly: the same words, spelling, capitals, punctuation and spacing. Never add, drop or change a character.

How to judge stress (after Briggs & Frere, A Manual of Plainsong, 1902):
- Mark the stress the sentence gives, not only the dictionary. Content words (nouns, main verbs, adjectives, most adverbs) are stressed; articles, prepositions, conjunctions, auxiliaries and most pronouns are not, unless the sense puts weight on them ("it is YOU who...", contrasts, a final "me" after a weak syllable).
- "Lord", "God", "Name" and other names of God are stressed.
- Mark the main stress of every word of two or more syllables; mark a secondary stress only where a careful reader would give it a beat (e.g. "+right/eous/+ness" is wrong; "+right/eous/ness" is right; "+ev/er/+last/ing" is right).
- Do not leave long runs unstressed: in a run of monosyllables, mark the words a reader would lean on. Two stresses may stand next to each other.
- Give "-ed" its own syllable only where it is pronounced: "+bless/ed" as an adjective ("+Bless/ed is the +man"), "+blessed" as a verb ("he +blessed them"); "be/+lov/ed" when said that way.
- Divide syllables as a singer would sing them, by sound: "+shep/herd", "+right/eous/ness", "sal/+va/tion", "+mer/cy", "Is/ra/el" (three syllables), "+heav/en", "+pow/er", "+ev/er".
- Keep possessives and contractions inside their syllable: "+Name's", "+Lord's".
- Pay most care to the last five or six syllables of each half-verse; they decide how the tone fits.

Example:
Half-verse: The Lord is my shepherd;
Answer: The +Lord is my +shep/herd;

Half-verse: and bring me forth in the paths of righteousness for his Name's sake.
Answer: and +bring me +forth in the +paths of +right/eous/ness for his +Name's +sake.

Half-verse: I will give thanks unto the Lord with my whole heart,
Answer: I will give +thanks un/to the +Lord with my +whole +heart,

For each verse also give "confidence" from 0 to 1 that both halves are marked as a skilled cantor would mark them, and a short "note" naming anything doubtful (leave it empty if nothing is)."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "first_half": {"type": "string"},
                    "second_half": {"type": "string"},
                    "confidence": {"type": "number"},
                    "note": {"type": "string"},
                },
                "required": ["number", "first_half", "second_half", "confidence", "note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verses"],
    "additionalProperties": False,
}

CHUNK_SIZE = 30


class StressMarkingError(RuntimeError):
    pass


def model_name():
    return getattr(settings, "PSALM_POINTING_MODEL", "") or "gpt-5"


def _client():
    from openai import OpenAI

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise StressMarkingError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _user_message(psalm_number, verses):
    lines = [f"Psalm {psalm_number}. Mark each half-verse.", ""]
    for verse in verses:
        lines.append(f"Verse {verse['number']}")
        lines.append(f"First half: {verse['first_half']}")
        lines.append(f"Second half: {verse['second_half']}")
        lines.append("")
    return "\n".join(lines)


def mark_psalm(psalm_number, verses, *, client=None, model=None):
    """Mark a psalm's verses. ``verses`` is a list of {number, first_half, second_half}.

    Returns {verse number: {first_half, second_half, confidence, note}}.
    Long psalms are sent in chunks, each with the whole psalm's number for context.
    """
    client = client or _client()
    model = model or model_name()
    results = {}
    for start in range(0, len(verses), CHUNK_SIZE):
        chunk = verses[start : start + CHUNK_SIZE]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _user_message(psalm_number, chunk)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "psalm_stress", "schema": RESPONSE_SCHEMA, "strict": True},
            },
        )
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except (TypeError, ValueError) as error:
            raise StressMarkingError(f"The model did not return JSON: {content!r}") from error
        for item in data.get("verses", []):
            results[item["number"]] = {
                "first_half": item.get("first_half", ""),
                "second_half": item.get("second_half", ""),
                "confidence": item.get("confidence"),
                "note": item.get("note", ""),
            }
    return results

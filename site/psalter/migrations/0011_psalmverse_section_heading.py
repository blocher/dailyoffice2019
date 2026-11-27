import re

from django.db import migrations, models

# Kept here rather than imported, so the migration never changes with the app.
LETTERS = (
    "Aleph Beth Gimel Daleth He Waw Zayin Heth Teth Yodh Kaph Lamedh Mem Nun Samekh Ayin Pe Sadhe Qoph Resh Shin Taw"
).split()
TEXT_FIELDS = ("second_half", "second_half_tle")
NOTE = "The book has “nothing” where the text has “{}”."


def _letter(verse_number):
    index = verse_number // 8
    return LETTERS[index] if verse_number % 8 == 1 and index < len(LETTERS) else None


def _without_letter(notation, letter):
    """Drop the notated letter name ("Gi/mel") from the end of a half-verse."""
    head, _, last = notation.rstrip().rpartition(" ")
    if head and re.sub(r"[^A-Za-z]", "", last) == letter:
        return head
    return notation


def move_letters_to_headings(apps, schema_editor):
    """Psalm 119's section letters were stored at the end of the verse before
    each section ("... utterly. Beth"); move each into the heading of the
    verse that opens its section, and drop it from that verse's pointing."""
    PsalmVerse = apps.get_model("psalter", "PsalmVerse")
    Pointing = apps.get_model("psalter", "PsalmVersePointing")
    verses = {verse.number: verse for verse in PsalmVerse.objects.filter(psalm__number=119)}
    for number, verse in sorted(verses.items()):
        letter = _letter(number)
        if letter and verse.section_heading != letter:
            verse.section_heading = letter
            verse.save(update_fields=["section_heading"])
        following = _letter(number + 1)
        if not following:
            continue
        changed = []
        for field in TEXT_FIELDS:
            text = getattr(verse, field) or ""
            suffix = f" {following}"
            if text.rstrip().endswith(suffix):
                setattr(verse, field, text.rstrip()[: -len(suffix)])
                changed.append(field)
        if changed:
            verse.save(update_fields=changed)
        pointing = Pointing.objects.filter(verse=verse).first()
        if pointing is None:
            continue
        stress = _without_letter(pointing.second_half_stress, following)
        dictionary = _without_letter(pointing.dictionary_second_half, following)
        if stress == pointing.second_half_stress and dictionary == pointing.dictionary_second_half:
            continue
        pointing.second_half_stress = stress
        pointing.dictionary_second_half = dictionary
        if pointing.review_notes.strip() == NOTE.format(following):
            # The letter was the only difference from the book.
            pointing.review_notes = ""
            if pointing.source == "book" and pointing.status == "check":
                pointing.status = "book"
        pointing.save()


def move_headings_to_letters(apps, schema_editor):
    PsalmVerse = apps.get_model("psalter", "PsalmVerse")
    verses = {verse.number: verse for verse in PsalmVerse.objects.filter(psalm__number=119)}
    for number, verse in sorted(verses.items()):
        previous = verses.get(number - 1)
        if verse.section_heading and previous:
            for field in TEXT_FIELDS:
                text = getattr(previous, field)
                if text and not text.rstrip().endswith(f" {verse.section_heading}"):
                    setattr(previous, field, f"{text.rstrip()} {verse.section_heading}")
            previous.save(update_fields=list(TEXT_FIELDS))
            # The pointing no longer matches the text and stays hidden until
            # the psalm is imported again.


class Migration(migrations.Migration):
    dependencies = [
        ("psalter", "0010_chant_book_pointing"),
    ]

    operations = [
        migrations.AddField(
            model_name="psalmverse",
            name="section_heading",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.RunPython(move_letters_to_headings, move_headings_to_letters),
    ]

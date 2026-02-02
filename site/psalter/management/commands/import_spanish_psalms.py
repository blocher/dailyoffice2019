import re
from operator import itemgetter

import pdfplumber
from django.core.management import BaseCommand
from pdfplumber.utils import cluster_objects

from office.utils import title_case
from psalter.models import PsalmVerse, Psalm
from website import settings


def collate_line(line_chars, tolerance=3):
    coll = []
    last_x1 = None
    for char in sorted(line_chars, key=itemgetter("x0")):
        if (last_x1 is not None) and (char["x0"] > (last_x1 + tolerance)):
            coll += " "
        last_x1 = char["x1"]
        coll.append(char)
    return coll


def remove_smart_quotes(text):
    return text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


# covert to title case
def clean(input):
    input = title_case(input)
    input = remove_smart_quotes(input)
    input = input.replace("\n", " ").replace("\r", "")
    input = re.sub(r" +", " ", input)
    input = input.strip()
    return input


def clean_collect(input):
    input = remove_smart_quotes(input)
    input = input.replace("<strong>Amen.", "").replace("<strong> Amen.", "")
    input = input.replace("Amen.", "").replace("Amen", "")
    input = re.sub(r" +", " ", input)
    input = input.strip()
    input = f"<p>{input} <strong>Amen.</strong></p>"

    return input


def number(input):
    input = re.sub(r"[^0-9]", "", input)
    if input == "2323":
        input = "23"
    input = int(input)
    return input


def remove_number(input):
    input = re.sub(r"^[0-9]+\.", "", input)
    input = input.replace("Benedict of Nursia", "")
    input = input.strip()
    input = input.split("  ")
    input = input[0]

    input = clean(input)
    return input


def line_to_text(line):
    text = [obj["text"] for obj in line if type(obj) != str and type(obj) != list and obj["object_type"] == "char"]
    text = "".join(text)
    return text.strip()


def line_should_be_included(line):
    # if line[0]["fontname"] == "LPJIDQ+ACaslonPro-Italic-SC700":
    #     return False
    text = line_to_text(line).lower()
    skip_list = [
        "morning prayer",
        "evening prayer",
        "the psalter",
        "oración matutina",
        "oración vespertina",
        "el salterio",
    ]
    for skip in skip_list:
        if skip in text:
            return False
    return True


def import_spanish_psalter(verbose=False):
    files = ["spanish_psalms.pdf"]
    return import_psalter(files, verbose=verbose)


def import_psalter(files, verbose=False):
    lines = []
    for file in files:
        with pdfplumber.open(f"{settings.BASE_DIR}/psalter/management/commands/{file}") as pdf:
            for i, pdf_page in enumerate(pdf.pages):
                doctop_clusters = cluster_objects(pdf_page.chars, itemgetter("doctop"), 3)
                temp_lines = [collate_line(line_chars, 3) for line_chars in doctop_clusters]
                lines = lines + temp_lines
    lines = [line for line in lines if line_should_be_included(line)]

    psalm_number = 0
    latin = ""
    first_half = ""
    second_half = ""
    verse_number = 0
    first_half_complete = False
    had_asterisk = False
    fonts = []
    saved_count = 0
    skipped_count = 0

    for i, line_chars in enumerate(lines):
        if not line_chars:
            continue
        for obj in line_chars:
            try:
                fonts.append(obj["fontname"])
            except TypeError:
                pass

        try:
            if "Italic" in line_chars[0].get("fontname", ""):
                continue
        except (IndexError, TypeError, AttributeError):
            pass

        line_text = line_to_text(line_chars)

        # Check for page numbers (numeric and at top or bottom)
        if line_text.strip().isnumeric():
            try:
                # Calculate average 'top' position
                # Filter chars that have 'top' (sometimes spaces don't)
                chars_with_top = [c for c in line_chars if "top" in c]
                if chars_with_top:
                    avg_top = sum(c["top"] for c in chars_with_top) / len(chars_with_top)
                    # Assuming standard page height, headers < 60, footers > 700
                    # This range is a heuristic but should catch standard page numbers
                    if avg_top < 60 or avg_top > 700:
                        if verbose:
                            print(f"Skipping likely page number: '{line_text}' at top={avg_top:.2f}")
                        continue
            except (ZeroDivisionError, KeyError, TypeError):
                pass

        temp_line = line_text
        replace_lord = False
        if "Lord" in temp_line:
            for i, letter in enumerate(line_chars):
                try:
                    o_in_lord = "NO"
                    try:
                        if letter["text"] == "o":
                            if (
                                line_chars[i + 1]["text"] == "r"
                                and line_chars[i + 2]["text"] == "d"
                                and line_chars[i - 1]["text"] == "L"
                            ):
                                o_in_lord = "YES"
                    except IndexError:
                        pass
                    if letter["text"] == "o" and o_in_lord == "YES" and letter["width"] > 6:
                        replace_lord = True
                except TypeError:
                    pass

        line = line_text
        if replace_lord:
            line = line.replace("Lord", "Lᴏʀᴅ")

        # Check for verse number: starts with number followed by space
        verse_match = re.match(r"^([0-9]+)\s+(.*)", line)

        # Trigger save if we encounter a new verse number, a psalm number, or end of file
        if verse_match or line.isnumeric() or i >= len(lines) - 2:
            if verse_number != 0 and psalm_number != 0:
                psalm = Psalm.objects.get_or_create(number=psalm_number)[0]
                verse = PsalmVerse.objects.get_or_create(psalm=psalm, number=verse_number)
                verse = verse[0]
                if first_half.strip():
                    verse.first_half_spanish = first_half.strip()
                    verse.second_half_spanish = second_half.strip()
                    verse.save()
                    saved_count += 1
                    if verbose:
                        print(f"Saved Psalm {psalm_number}:{verse_number}")
                else:
                    skipped_count += 1
                    if verbose:
                        print(
                            f"Skipped Psalm {psalm_number}:{verse_number} - no first_half content (line: {line[:50]})"
                        )
                first_half = ""
                second_half = ""
                first_half_complete = False
                had_asterisk = False

        if verse_match:
            verse_num_str = verse_match.group(1)
            line = verse_match.group(2).strip()
            verse_number = number(verse_num_str)

        if line.isnumeric():
            psalm_number = number(line)
            if verbose:
                print(f"Detected Psalm {psalm_number}")

        if "*" in line:
            line = line.replace("*", "").strip()
            had_asterisk = True

        if not first_half_complete and not line.isnumeric():
            first_half = first_half + " " + line
        elif not line.isnumeric():
            second_half = second_half + " " + line

        if had_asterisk:
            first_half_complete = True
            had_asterisk = False

    # Save the last verse if we have one
    if verse_number != 0 and psalm_number != 0 and first_half.strip():
        psalm = Psalm.objects.get_or_create(number=psalm_number)[0]
        verse = PsalmVerse.objects.get_or_create(psalm=psalm, number=verse_number)
        verse = verse[0]
        verse.first_half_spanish = first_half.strip()
        verse.second_half_spanish = second_half.strip()
        verse.save()
        saved_count += 1

    fonts = set(fonts)
    print(f"Saved {saved_count} verses, skipped {skipped_count} verses with no content")


class Command(BaseCommand):
    help = "Import Spanish psalms from spanish_psalms.pdf"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output for debugging",
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)
        self.stdout.write("Starting Spanish psalm import...")
        import_spanish_psalter(verbose=verbose)
        self.stdout.write(self.style.SUCCESS("Spanish psalm import completed"))

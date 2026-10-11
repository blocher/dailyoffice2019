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
    ]
    for skip in skip_list:
        if skip in text:
            return False
    return True


def import_tle_psalter():
    files = ["tle328psalms1-50.pdf", "tle328psalms51-100.pdf", "tle328psalms101-150.pdf"]
    return import_psalter(files, trad=True)


def import_cont_psalter():
    files = ["BCP2019.pdf"]
    return import_psalter(files, trad=False)


def import_psalter(files, trad=False):
    lines = []
    for file in files:
        with pdfplumber.open(f"{settings.BASE_DIR}/psalter/management/commands/{file}") as pdf:
            for i, pdf_page in enumerate(pdf.pages):
                if not trad and (i < 277 or i > 475):
                    continue
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
    for i, line in enumerate(lines):
        for obj in line:
            try:
                fonts.append(obj["fontname"])
            except TypeError:
                pass

        if "Italic" in line[0]["fontname"]:
            continue
        temp_line = line_to_text(line)
        replace_lord = False
        if "Lord" in temp_line:
            for i, letter in enumerate(line):
                try:
                    o_in_lord = "NO"
                    try:
                        if letter["text"] == "o":
                            if (
                                line[i + 1]["text"] == "r"
                                and line[i + 2]["text"] == "d"
                                and line[i - 1]["text"] == "L"
                            ):
                                o_in_lord = "YES"
                    except IndexError:
                        pass
                    if letter["text"] == "o" and o_in_lord == "YES" and letter["width"] > 6:
                        replace_lord = True
                    # if letter['text'] in ["L", "o", "r", "d"]:
                    #     print(letter['text'], psalm_number, verse_number, letter['width'], o_in_lord)
                except TypeError:
                    pass
        line = line_to_text(line)
        if replace_lord:
            line = line.replace("Lord", "Lᴏʀᴅ")
        if re.match("[0-9]+\s", line) or line.isnumeric() or i >= len(lines) - 2:
            if verse_number != 0 and psalm_number != 0 and first_half:
                # print(psalm_number, verse_number, first_half, i, len(lines))
                psalm = Psalm.objects.get_or_create(number=psalm_number)[0]
                verse = PsalmVerse.objects.get_or_create(psalm=psalm, number=verse_number)
                verse = verse[0]
                if trad:
                    verse.first_half_tle = first_half
                    verse.second_half_tle = second_half
                else:
                    verse.first_half = first_half
                    verse.second_half = second_half
                verse.save()
                first_half = ""
                second_half = ""
                first_half_complete = False
                had_asterisk = False
        if re.match("[0-9]+\s", line):
            verse_number = re.search("[0-9]+\s", line).group()
            line = line.replace(verse_number, "").strip()
            verse_number = number(verse_number)
        if line.isnumeric():
            psalm_number = number(line)
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
    fonts = set(fonts)


class Command(BaseCommand):
    help = "Import all the collects"

    def handle(self, *args, **options):
        import_tle_psalter()
        import_cont_psalter()

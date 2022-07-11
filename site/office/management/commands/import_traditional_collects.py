import re

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from churchcal.management.commands.import_base import Command as ImportCommemorationsBaseCommand
from churchcal.models import Commemoration, Proper, Common
from office.models import Collect, CollectCategory
from office.utils import title_case


def remove_smart_quotes(text):
    return text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


# covert to title case
def clean(input):
    input = title_case(input)
    input = remove_smart_quotes(input)
    input = input.replace("\n", " ").replace("\r", "")
    input = re.sub(" +", " ", input)
    input = input.strip()
    return input


def clean_collect(input):
    input = remove_smart_quotes(input)
    input = input.replace("Amen.", "").replace("Amen", "")
    input = re.sub(" +", " ", input)
    input = input.strip()
    return input


def number(input):
    input = re.sub("[^0-9]", "", input)
    input = int(input)
    return input


def remove_number(input):
    input = re.sub("^[0-9]+\.", "", input)
    input = input.replace("Benedict of Nursia", "")
    input = input.strip()
    input = input.split("  ")
    input = input[0]

    input = clean(input)
    return input


def name_without_saint(input):
    if input == "Saint John the Evangelist":
        return "John, Apostle and Evangelist"
    if input == "Saint Mary the Virgin":
        return "The Virgin Mary, Mother of our Lord Jesus Christ"
    if input == "Memorial Day & Remembrance Day":
        return "Memorial Day"
    if input == "Christmas Eve":
        return "The Nativity of our Lord Jesus Christ: Christmas Day"
    if input == "Easter Eve":
        return "Easter Day"
    if input == "Saint James":
        return "James the Elder, Apostle"

    input = input.replace("Saint", "")
    input = input.replace("(I)", "")
    input = input.replace("(II)", "")
    input = re.sub(" +", " ", input)
    input = input.strip()
    return input


def proper_number(proper):
    proper = proper.lower()
    if "proper" not in proper:
        return None
    proper = re.sub("[^0-9]", "", proper)
    proper = int(proper)
    return proper


def get_contemporary_collect(name, commemoration, proper, common):
    if commemoration:
        if "(II)" in name and commemoration.alternate_collect:
            return commemoration.alternate_collect
        if "Eve" in name and commemoration.eve_collect:
            return commemoration.eve_collect
        return commemoration.collect
    if proper:
        return proper.collect
    if common:
        return common.collect
    return "???"


class Command(ImportCommemorationsBaseCommand):
    help = "Import the Traditional Language Collects"

    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "TradCollects!A1:F131"

    def handle(self, *args, **options):
        import pdfplumber

        all_text = ""
        print(f"{settings.BASE_DIR}/office/management/commands/tradocas.pdf")
        with pdfplumber.open(f"{settings.BASE_DIR}/office/management/commands/tradocas.pdf") as pdf:
            for pdf_page in pdf.pages:
                single_page_text = pdf_page.extract_text()
                # separate each page's text with newline
                all_text = all_text + "\n" + single_page_text

        # all text to list of lines
        all_text = all_text.split("\n")
        content = ""
        name = ""
        for line in all_text:
            if "occasional prayers" in line.lower() or "see also" in line.lower():
                continue
            if re.match("^[0-9]+\.", line):
                if name and content:
                    collect = Collect.objects.filter(collect_type="occasional", order=number(name)).first()
                    if not collect:
                        print("MISSING", name)
                    else:
                        collect.traditional_text = content
                        collect.save()
                name = line
                content = ""
            else:
                content = content + line + " "

        return

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=self.SHEET_ID, range=self.RANGE_NAME).execute()
        except HttpError as e:
            print("Data not found for this denomination")
            return

        self.values = result.get("values", [])

        Collect.objects.filter(collect_type__in=["collect", "year"]).delete()
        category = CollectCategory.objects.get_or_create(name="Church Year")[0]
        if not category.order:
            CollectCategory.objects.order_by("-order").first()
            category.order = category.order + 1
            category.save()
        last_collect = Collect.objects.order_by("-order").first()
        collect_order = last_collect.order + 1
        for i, row in enumerate(self.values):
            season = clean(row[0])
            name = clean(row[1])
            text = clean_collect(row[2])
            preface = clean(row[3])
            date_substring = clean(row[4])

            proper = None
            common = None
            commemoration = (
                Commemoration.objects.filter(
                    calendar__abbreviation="ACNA_BCP2019",
                    name__icontains=name_without_saint(name),
                    collect__isnull=False,
                )
                .exclude(collect="")
                .first()
            )

            if name == "All Saints' Day":
                commemoration = Commemoration.objects.filter(
                    calendar__abbreviation="ACNA_BCP2019", collect__contains="Almighty God, you have knit together "
                ).first()
            number_of_proper = proper_number(name)
            if number_of_proper and not commemoration:
                proper = Proper.objects.filter(calendar__abbreviation="ACNA_BCP2019", number=number_of_proper).first()
            if not proper and not commemoration:
                common = Common.objects.filter(calendar__abbreviation="ACNA_BCP2019", name__icontains=name).first()

            if not proper and not commemoration and not common:
                print(name)

            collect = Collect()
            collect.order = collect_order
            collect.collect_type = "year"
            collect.title = name
            collect.text = get_contemporary_collect(name, commemoration, proper, common)
            number_of_proper = proper_number(name)
            collect.traditional_text = text
            collect.collect_category = category
            collect.save()
            collect_order = collect_order + 1

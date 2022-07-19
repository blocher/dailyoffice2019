import os.path
import re
from operator import itemgetter

import pdfplumber
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pdfplumber.utils import cluster_objects
from tqdm import tqdm

from churchcal.models import Commemoration, Proper, Common
from office.models import CollectType, CollectTagCategory, CollectTag, Collect
from office.utils import title_case
from website import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_google_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


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
    input = re.sub(" +", " ", input)
    input = input.strip()
    return input


def clean_collect(input, strip_tags=False, remove_line_breaks=False):
    if strip_tags:
        input = BeautifulSoup(input, "lxml").text
    input = remove_smart_quotes(input)
    if remove_line_breaks:
        input = input.replace("\n", " ").replace("\r", "")
    input = input.replace("<strong>Amen.", "").replace("<strong> Amen.", "")
    input = input.replace("Amen.", "").replace("Amen", "")
    input = re.sub(" +", " ", input)
    input = input.strip()
    if input:
        input = f"<p>{input} <strong>Amen.</strong></p>"

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


def clear():
    CollectType.objects.all().delete()
    CollectTagCategory.objects.all().delete()
    CollectTag.objects.all().delete()
    Collect.objects.all().delete()


def import_collect_types():
    CollectType.objects.all().delete()
    collect_types = {
        "year": "Collects of the Christian Year",
        "occasional": "Collects and Occasional Prayers",
        "liturgical": "Collects from Various Liturgies",
    }
    for i, (key, name) in enumerate(collect_types.items()):
        CollectType.objects.create(name=name, key=key, order=i)


def import_collect_tag_categories():
    CollectTagCategory.objects.all().delete()
    collect_tag_categories = {
        "source": "Source",
        "theme": "Theme",
        "commemoration_type": "Commemoration Type",
        "season": "Season",
        "liturgy": "Liturgy",
    }
    for i, (key, name) in enumerate(collect_tag_categories.items()):
        CollectTagCategory.objects.create(name=name, key=key, order=i)


def import_collect_tags_for_category(category, items):
    for i, (key, name) in enumerate(items):
        collect_tag_category = CollectTagCategory.objects.get(key=category)
        CollectTag.objects.create(collect_tag_category=collect_tag_category, key=key, name=name, order=i)


def import_collect_tags():
    CollectTag.objects.all().delete()
    tags = {
        "source": CollectType.objects.order_by("order").values_list("key", "name"),
        "theme": [
            ("church", "The Church"),
            ("creation", "Creation"),
            ("nation_generic", "The Nation"),
            ("nation_canada", "The Nation (Specific to Canada)"),
            ("nation_us", "The Nation (Specific to the United States or Mexico)"),
            ("social_order", "Social Order"),
            ("those_in_need", "Those in Need"),
            ("family", "Family and Personal Life"),
            ("family_all", "Family and Personal Life (All)"),
            ("family", "Family and Personal Life (Throughout the Day)"),
            ("personal_devotion", "Personal Devotion"),
            ("prayer_and_worship", "At Times of Prayer and Worship"),
            ("death", "Death, the Departed, and the Communion of Saints"),
            ("thanksgivings", "Thanksgivings"),
            ("mission", "Mission"),
            ("confession", "Confession of Sin"),
        ],
        "commemoration_type": [
            ("major_feast", "Major Feast"),
            ("sunday", "Sunday"),
            ("holy_day", "Holy Day"),
            ("common", "Common of Commemorations"),
            ("national", "National Day"),
            ("ember_or_rogation", "Ember Day or Rogation Day"),
        ],
        "season": [
            ("advent", "Advent"),
            ("christmas", "Christmas"),
            ("epiphany", "Epiphany"),
            ("lent", "Lent"),
            ("holy_week", "Holy Week"),
            ("easter", "Easter"),
            ("pentecost", "Season after Pentecost"),
        ],
        "liturgy": [
            ("morning_prayer", "Morning Prayer"),
            ("midday_prayer", "Midday Prayer"),
            ("evening_prayer", "Evening Prayer"),
            ("compline", "Compline"),
            ("family_prayer", "Family Prayer"),
            ("holy_eucharist", "Holy Eucharist"),
            ("holy_baptism", "Holy Baptism"),
            ("confirmation", "Confirmation, Reception, and Reaffirmation"),
            ("holy_matrimony", "Holy Matrimony"),
            ("birth", "Thanksgiving for the Birth or Adoption of a Child"),
            ("reconciliation", "Reconciliation of a Penitent"),
            ("sick", "Ministry to the Sick"),
            ("burial", "Burial of the Dead"),
            ("ordination", "Ordination"),
            ("institution", "Institution of a New Rector"),
            ("consecration", "Consecration of a Place of Worship"),
            ("ash_wednesday", "Ash Wednesday"),
            ("palm_sunday", "Palm Sunday"),
            ("maundy_thursday", "Maundy Thursday"),
            ("good_friday", "Good Friday"),
            ("holy_saturday", "Holy Saturday"),
            ("easter_vigil", "Great Vigil of Easter"),
        ],
    }
    for category, items in tags.items():
        import_collect_tags_for_category(category, items)


def import_occasional_collects():
    Collect.objects.filter(collect_type__isnull=True).delete()
    Collect.objects.filter(collect_type__key="occasional").delete()
    collect_type = CollectType.objects.get(key="occasional")
    main_tag = CollectTag.objects.get(key="occasional", collect_tag_category__key="source")
    for i in range(1, 126):
        url = "https://occasionalprayers.com/acna2019/{}.html".format(i)
        data = requests.get(url)
        data.encoding = data.apparent_encoding
        html = BeautifulSoup(data.text, "html.parser")
        headings = html.select("h2")
        heading = headings[0].text
        text = (
            html.select("main")[0]
            .decode_contents(indent_level=None, formatter="html")
            .strip()
            .replace(" Amen.", " <strong>Amen.</strong>")
        )
        tag_name = ""
        tags = html.select(".tags")[0].find_all("a")
        if tags:
            tag_name = tags[0].text
        try:
            attribution = html.select("small")[0].text
        except IndexError:
            attribution = ""

        collect = Collect()
        collect.title = heading
        collect.text = text
        collect.order = i
        collect.number = i
        collect.attribution = attribution
        collect.collect_type = collect_type
        collect.save()

        try:
            tag = CollectTag.objects.get(name=tag_name, collect_tag_category__key="theme")
            collect.tags.add(tag)
        except CollectTag.DoesNotExist:
            print(tag_name)

        collect.tags.add(main_tag)


def line_should_be_included(line):
    line = line.lower()
    skip_list = ["& 51", "occasional prayers", "see also", "on page", "in the tradition of"]
    for skip in skip_list:
        if skip in line.lower():
            return False
    return True


def import_traditional_language_occasional_collects():
    collect_type = CollectType.objects.get(key="occasional")
    lines = []
    with pdfplumber.open(f"{settings.BASE_DIR}/office/management/commands/tradocas.pdf") as pdf:
        for pdf_page in pdf.pages:
            doctop_clusters = cluster_objects(pdf_page.chars, itemgetter("doctop"), 3)
            lines = lines + [collate_line(line_chars, 3) for line_chars in doctop_clusters]

    all_text = ""
    current_font = "LPJIDQ+ACaslonPro-Regular"
    for line in lines:
        for obj in line:
            if type(obj) is dict and obj["object_type"] == "char":
                if obj["fontname"] == "LPJIDQ+ACaslonPro-Italic-SC700":
                    current_font = "LPJIDQ+ACaslonPro-Regular"
                if obj["fontname"] == "LPJIDQ+ACaslonPro-Semibold" and obj["fontname"] != current_font:
                    all_text = all_text + "<strong>"
                if obj["fontname"] == "LPJIDQ+ACaslonPro-Italic" and obj["fontname"] != current_font:
                    all_text = all_text + "<em>"
                if obj["fontname"] == "LPJIDQ+ACaslonPro-Regular" and current_font == "LPJIDQ+ACaslonPro-Semibold":
                    all_text = all_text + "</strong>"
                if obj["fontname"] == "LPJIDQ+ACaslonPro-Regular" and current_font == "LPJIDQ+ACaslonPro-Italic":
                    all_text = all_text + "</em>"
                current_font = obj["fontname"]
                all_text = all_text + obj["text"]

        all_text = all_text + "\n"
    all_text = all_text + "\n126. Dummy to make it loop once more\n"
    all_text = all_text.split("\n")

    content = ""
    name = ""
    all_text = filter(line_should_be_included, all_text)
    all_text = list(all_text)
    for line in all_text:
        if re.match("(</strong>)?(</em>)?[0-9]+\.", line):
            if name and content:
                collect = Collect.objects.filter(collect_type=collect_type, order=number(name)).first()
                if not collect:
                    print("MISSING", name)
                else:
                    # print(name)
                    collect.traditional_text = clean_collect(content)
                    collect.save()
            name = line
            content = ""
        else:
            if "We thank thee, Lord." in line:
                line = f"<br>{line}<br>"
            if "To him be praise and glory" in line:
                line = f"<br>{line}"
            content = content + line + " "

    return


def get_commemoration_type_tag(commemoration, proper, common):
    if common:
        return CollectTag.objects.get(key="common", collect_tag_category__key="commemoration_type")
    if proper:
        return CollectTag.objects.get(key="sunday", collect_tag_category__key="commemoration_type")
    rank = commemoration.rank.name
    if rank in ["PRINCIPAL_FEAST", "PRIVILEGED_OBSERVANCE"]:
        return CollectTag.objects.get(key="major_feast", collect_tag_category__key="commemoration_type")
    if rank in ["SUNDAY"]:
        return CollectTag.objects.get(key="sunday", collect_tag_category__key="commemoration_type")
    if rank in ["HOLY_DAY", "ALTERNATE_SUNDAY"]:
        return CollectTag.objects.get(key="holy_day", collect_tag_category__key="commemoration_type")
    if rank in ["EMBER_DAY", "ROGATION_DAY"]:
        return CollectTag.objects.get(key="ember_or_rogation", collect_tag_category__key="commemoration_type")
    if rank in ["NATIONAL_DAY_UNITED_STATES", "NATIONAL_DAY_CANADA"]:
        return CollectTag.objects.get(key="national", collect_tag_category__key="commemoration_type")
    print("Uhoh", commemoration)


def import_collects_of_the_christian_year():
    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "TradCollects!A1:F131"

    service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    except HttpError as e:
        print("Data not found for this denomination")
        return

    values = result.get("values", [])

    collect_type = CollectType.objects.get(key="year")
    Collect.objects.filter(collect_type=collect_type).delete()
    main_tag = CollectTag.objects.get(key="year", collect_tag_category__key="source")

    for i, row in enumerate(values):
        season = clean(row[0])
        name = clean(row[1])
        text = clean_collect(row[2])
        preface = clean(row[3])
        date_substring = clean(row[4])

        proper = None
        common = None
        commemoration = (
            Commemoration.objects.filter(
                calendar__abbreviation="ACNA_BCP2019", name__icontains=name_without_saint(name), collect__isnull=False
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

        season_tag = None
        try:
            if season:
                season_tag = CollectTag.objects.get(name=season, collect_tag_category__key="season")
        except CollectTag.DoesNotExist:
            print(season)

        collect = Collect()
        collect.order = i
        collect.collect_type = collect_type
        collect.title = name
        collect.text = clean_collect(get_contemporary_collect(name, commemoration, proper, common))
        number_of_proper = proper_number(name)
        collect.traditional_text = text
        collect.save()
        if season_tag:
            collect.tags.add(season_tag)
        commemoration_type_tag = get_commemoration_type_tag(commemoration, proper, common)
        collect.tags.add(commemoration_type_tag)
        collect.tags.add(main_tag)


def import_liturgical_collects():
    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "LiturgyCollects!A2:J195"

    service = build("sheets", "v4", credentials=get_google_credentials())

    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    except HttpError as e:
        print("Data not found for this denomination")
        return

    values = result.get("values", [])
    collect_type = CollectType.objects.get(key="liturgical")
    Collect.objects.filter(collect_type=collect_type).delete()
    primary_tag = CollectTag.objects.get(key="liturgical", collect_tag_category__key="source")

    for i, row in tqdm(enumerate(values)):
        title = row[0]
        text = row[1]
        traditional = row[2]
        tag_1 = row[3]
        tag_2 = row[4]
        tag_3 = row[5]
        tag_4 = row[6]
        tag_5 = row[7]
        tag_6 = row[8]

        collect = Collect()
        collect.title = title
        collect.text = text
        collect.traditional_text = traditional
        collect.collect_type = collect_type
        collect.order = i
        collect.save()
        collect.tags.add(primary_tag)
        if tag_1:
            print(tag_1)
            collect.tags.add(CollectTag.objects.filter(name=tag_1.strip()).first())
        if tag_2:
            print(tag_2)
            collect.tags.add(CollectTag.objects.filter(name=tag_2.strip()).first())
        if tag_3:
            collect.tags.add(CollectTag.objects.filter(name=tag_3.strip()).first())
        if tag_4:
            collect.tags.add(CollectTag.objects.filter(name=tag_4.strip()).first())
        if tag_5:
            collect.tags.add(CollectTag.objects.filter(name=tag_5.strip()).first())
        if tag_6:
            collect.tags.add(CollectTag.objects.filter(name=tag_6.strip()).first())


def clean_liturgical_collects():
    SHEET_ID = "1s7GqYoy3HC5JD64opdRldAAi3mwsSQxtC6ZzzF2yUAg"
    RANGE_NAME = "LiturgyCollects!A2:J195"

    service = build("sheets", "v4", credentials=get_google_credentials())

    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    except HttpError as e:
        print("Data not found for this denomination")
        return

    values = result.get("values", [])

    results = []

    for i, row in tqdm(enumerate(values)):
        title = clean(row[0])
        collect = clean_collect(row[1], strip_tags=True, remove_line_breaks=True)
        traditional = clean_collect(row[2], strip_tags=True, remove_line_breaks=True)
        tag_1 = clean(row[3])
        tag_2 = clean(row[4])
        tag_3 = clean(row[5])
        tag_4 = clean(row[6])
        tag_5 = clean(row[7])
        tag_6 = clean(row[8])
        final_marker = "X"
        row_result = [title, collect, traditional, tag_1, tag_2, tag_3, tag_4, tag_5, tag_6, final_marker]
        results.append(row_result)

    final_row = len(values) + 2
    range = f"LiturgyCollects!A2:J{final_row}"
    sheet.values().update(
        spreadsheetId=SHEET_ID, range=range, valueInputOption="USER_ENTERED", body={"values": results}
    ).execute()


class Command(BaseCommand):
    help = "Import all the collects"

    def handle(self, *args, **options):
        # clean_liturgical_collects()
        clear()
        import_collect_types()
        import_collect_tag_categories()
        import_collect_tags()
        import_occasional_collects()
        import_traditional_language_occasional_collects()
        import_collects_of_the_christian_year()
        import_liturgical_collects()

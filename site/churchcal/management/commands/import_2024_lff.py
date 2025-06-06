import datetime
import re

import requests
from bs4 import BeautifulSoup, Tag
from django.core.management.base import BaseCommand

from churchcal.models import SanctoraleCommemoration, CommemorationRank, Calendar


def parse_lff_calendar():
    url = "https://www.lectionarypage.net/CalndrsIndexes/TxtIndexLFF.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    text = response.content.decode("utf-8")
    # Remove HTML comments before parsing
    clean_html = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).replace("\n", " ")
    clean_html = clean_html.replace(
        "Katharina von Bora</a>, Church Reformer, 1552", "Katharina von Bora</a>, Church Reformer, 1552</li>"
    )
    clean_html = clean_html.replace("</a>,] Martyr", "</a>,] Martyr</li>")
    clean_html = clean_html.replace("</b>", " ").replace("<b>", " ")
    clean_html = clean_html.replace("1902 and 1890 <br>", "1902 and 1890 <br></li>")
    clean_html = clean_html.replace("1856, 1858, and 1862", "1856, 1858, and 1862</li>")
    clean_html = clean_html.replace("&nbsp;&nbsp;<i>or</i>", "</li><li>7")
    clean_html = clean_html.replace("<i>or</i>", "</li><li>29")
    soup = BeautifulSoup(clean_html, "html.parser")
    entries = []

    blockquotes = soup.find_all("blockquote")

    for blockquote in blockquotes:
        month = blockquote.get_text(strip=True)

        next_sibling = blockquote.find_next_sibling()
        while next_sibling and (not isinstance(next_sibling, Tag) or next_sibling.name != "ul"):
            next_sibling = next_sibling.find_next_sibling()

        if not next_sibling:
            continue

        while True:
            nested_ul = next_sibling.find("ul")
            if nested_ul:
                next_sibling = nested_ul
            else:
                break

        for li in next_sibling.find_all("li", recursive=False):
            day_match = re.match(r"^\s*(\d+)", li.get_text(strip=True))
            if not day_match:
                continue
            day = int(day_match.group(1))

            a_tag = li.find("a")
            if not a_tag:
                continue
            name = a_tag.get_text(strip=True)

            title = ""
            for sib in a_tag.next_siblings:
                if isinstance(sib, str):
                    title += sib.strip()
                elif isinstance(sib, Tag):
                    title += sib.get_text(strip=True)

            name = f"{name}{title}".strip()
            rank = "LESSER_FEAST"

            if "[" in name or "]" in name:
                name = name.replace("[", "").replace("]", "")
                rank = "LESSER_FEAST_TRIAL_USE"

            name = name.replace("Georgeof", "George of")
            name = re.sub(r"\s+", " ", name)

            if "January|February|March|April|May|June||July|August|September|October|November|December" in month:
                continue

            print(f"{month} {day} : {name} ({rank})")

            matches = SanctoraleCommemoration.objects.filter(
                rank__name__in=["LESSER_FEAST", "LESSER_FEAST_TRIAL_USE"],
                month=datetime.datetime.strptime(month, "%B").month,
                day=day,
            ).all()

            for match in matches:
                if match.name != name:
                    print(f"{month} {day} : {name} ({rank})")
                    print(f"{match.month} {match.day} {match.name} {match.rank}")

            print("")

            entries.append(
                {
                    "Month": month,
                    "Day": day,
                    "Name": name,
                    "Rank": rank,
                }
            )

    return entries


class Command(BaseCommand):
    help = "Imports LFF 2024"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        SanctoraleCommemoration.objects.filter(
            rank__name__in=["LESSER_FEAST_TRIAL_USE", "LESSER_FEAST"]
        ).all().delete()

        calendar = Calendar.objects.get(abbreviation="TEC_BCP1979_LFF2024")
        for entry in parse_lff_calendar():
            month = datetime.datetime.strptime(entry["Month"], "%B").month
            day = entry["Day"]
            name = entry["Name"]
            rank = entry["Rank"]

            SanctoraleCommemoration.objects.create(
                month=month,
                day=day,
                name=name,
                rank=CommemorationRank.objects.get(name=rank),
                calendar=calendar,
            )
        # pprint(parse_lff_calendar())

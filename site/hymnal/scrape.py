import base64
import os
import subprocess
from os.path import isfile, join
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import SimpleCookie

from hymnal.models import Hymn

cookies = "_gid=GA1.2.676933162.1680473360; __RequestVerificationToken=qUtBVhXZ7msTGjljgTnm2FIB0RMYmS0DzZFxM0c_A9nGZvuda_x0Ap04Qf7hfWPAOvH-LxJT0ib46MAz-xXDwfup7ySSYWEcHzbOUFpUwT41; ASP.NET_SessionId=rmskwjobj2cmokl3exlg3sch; .ASPXAUTH=61208C9A319A50CE27DD8E334BD84E8F04ED53457EB3F4060D620C738359B67F4C7A1F59B2519BD701C6E1B434EE6708CBB433A9099E8593671ABE82DFA475BA909D920901DAC0C41530A9AB2A9F6076F2CC804721A4B014F917BF97E729E19B2EED70DA617B133D99CE55D4E8BFA336; _gat_UA-129462230-1=1; _ga_HPNFM6SKKL=GS1.1.1680630052.8.1.1680630054.0.0.0; _ga=GA1.1.1909329660.1680473360"


def cookies_string_to_dict(rawdata):
    cookie = SimpleCookie()
    cookie.load(rawdata)

    # Even though SimpleCookie is dictionary-like, it internally uses a Morsel object
    # which is incompatible with requests. Manually construct a dictionary instead.
    cookies = {k: v.value for k, v in cookie.items()}
    return cookies


def scrape_details(id):
    url = "https://members.riteplanning.com/Music/_Details"
    form_data = {
        "atomId": id,
    }
    result = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    soup = BeautifulSoup(result.content, "html.parser")
    return soup


def scrape_mp3(id):
    url = "https://members.riteplanning.com/Music/MediaPreview"
    form_data = {
        "atomId": id,
    }

    folder_to_store = settings.STATIC_ROOT + "/hymnal/mp3"
    isExist = os.path.exists(folder_to_store)
    if not isExist:
        os.makedirs(folder_to_store)
    full_filename = os.path.join(folder_to_store, str(id) + ".mp3")
    # print(full_filename)
    # if (os.path.isfile(full_filename)):
    #     return

    response = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    # with open(full_filename, "wb") as f:
    #     f.write(base64.b64decode(response.content))
    return str(id) + ".mp3", ContentFile(base64.b64decode(response.content))


def scrape_docs(id, number):
    url = "https://members.riteplanning.com/File/Download"
    form_data = {
        "atomId": id,
        "useType": "Testing / Community Group Worship",
        "useDate": "12/12/2022",
        "numCopies": 1,
    }

    folder_to_store = settings.STATIC_ROOT + "/hymnal/zip"
    isExist = os.path.exists(folder_to_store)
    if not isExist:
        os.makedirs(folder_to_store)
    number = number.replace(" ", "")
    full_filename = os.path.join(folder_to_store, f"{number}.zip")
    contents_dir = os.path.join(folder_to_store, f"{number}")
    # if (os.path.isfile(full_filename)):
    #     return

    response = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    print(full_filename)
    with open(full_filename, "wb") as f:
        f.write(response.content)
    with ZipFile(full_filename, "r") as zObject:
        zObject.extractall(path=contents_dir)
    music = [f for f in os.listdir(contents_dir) if isfile(join(contents_dir, f)) and "(Music)" in f]
    lyrics = [f for f in os.listdir(contents_dir) if isfile(join(contents_dir, f)) and "(Words)" in f and ".rtf" in f]
    for lyric in lyrics:
        full_path = os.path.join(contents_dir, lyric)
        os.rename(full_path, os.path.join(contents_dir, f"{number}.rtf"))
        rtf = os.path.join(contents_dir, f"{number}.rtf")
        html = os.path.join(contents_dir, f"{number}.html")
        cmd_str = f"cd {contents_dir} && /Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to html {rtf}"
        output = subprocess.run(cmd_str, shell=True, capture_output=True)
        print(output)
        with open(html) as f:
            content = f.read()
            soup = BeautifulSoup(content, "html.parser")
            lines = soup.find_all("p", {"class": "western"})
            verses = []
            verse = []
            attribution = []
            for line in lines:
                bs = line.find_all("b")
                small_font = line.find_all("font", {"size": "2"})
                if len(bs):
                    continue
                if small_font:
                    attribution.append(line.text.replace("\n", " ").strip())
                    continue
                if line.text.strip() == "":
                    verses.append(verse)
                    verse = []
                else:
                    verse.append(line.text.replace("\n", " ").strip())
            verses = [verse for verse in verses if len(verse)]
            for i, verse in enumerate(verses):
                print(f"***Verse {i + 1}:")
                print("\n".join(verse))
            print("***Attribution")
            print("\n".join(attribution))

            #
            # output = pypandoc.convert_file(os.path.join(contents_dir, lyric), 'docx',
            #                                outputfile=os.path.join(contents_dir, lyric).replace('.rtf', '.docx'))

    print(music, lyrics)

    return str(id) + ".pdf", ContentFile(response.content)

    result = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    print(result.headers)
    # print(result.content)


def construct_hymn(row):
    children = row.findChildren("td", recursive=False)
    id = row.attrs["id"].replace("result-", "")
    title = children[2].attrs["data-title"]
    title_parts = title.split("(")
    title = title_parts[0].strip()
    tune = title_parts[1].replace(")", "").strip() if len(title_parts) > 1 else ""
    details = scrape_details(id)
    copyright = details.findAll("div", {"id": "dialog-copyrights"})[0].text
    return {
        "id": id,
        "hymnal": "The Hymnal 1982",
        "number": children[1].text.strip(),
        "title": title,
        "tune": tune,
        "rite_planning_id": id,
        "copyright": copyright,
        "fair_use": "©" not in copyright,
    }


def get_hymn_list():
    url = "https://members.riteplanning.com/Music/Search"
    form_data = {
        "collection": "H",
        "page": 12,
        "sortColumn": "HymnNumberSort",
        "sortDirection": "asc",
    }
    result = requests.post(url, cookies=cookies_string_to_dict(cookies), data=form_data)
    soup = BeautifulSoup(result.content, "html.parser")
    last_page = soup.find_all("li", {"class": "PagedList-skipToLast"})[0].find("a").attrs["href"]
    pages = range(1, int(last_page) + 1)
    for i in pages:
        form_data["page"] = i
        result = requests.post(url, cookies=cookies_string_to_dict(cookies), data=form_data)
        soup = BeautifulSoup(result.content, "html.parser")
        rows = soup.find_all("tr", id=lambda value: value and value.startswith("result-"))
        for row in rows:
            hymn_data = construct_hymn(row)
            hymn = Hymn.objects.get_or_create(hymnal=hymn_data["hymnal"], number=hymn_data["number"])[0]
            hymn.title = hymn_data["title"]
            hymn.tune_name = hymn_data["tune"]
            hymn.rite_planning_id = hymn_data["id"]
            hymn.copyright = hymn_data["copyright"]
            hymn.fair_use = hymn_data["fair_use"]
            hymn.save()
            hymn.mp3.save(*scrape_mp3(hymn_data["id"]))
            hymn.pdf.save(*scrape_docs(hymn_data["id"], hymn_data["number"])),
            print(hymn)
            return


def scrape():
    get_hymn_list()

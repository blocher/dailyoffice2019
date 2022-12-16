import base64

import requests
from bs4 import BeautifulSoup
from django.http import SimpleCookie

cookies = ""


def cookies_string_to_dict(rawdata):
    cookie = SimpleCookie()
    cookie.load(rawdata)

    # Even though SimpleCookie is dictionary-like, it internally uses a Morsel object
    # which is incompatible with requests. Manually construct a dictionary instead.
    cookies = {k: v.value for k, v in cookie.items()}
    return cookies


def scrape_mp3(id):
    url = "https://members.riteplanning.com/Music/MediaPreview"
    form_data = {
        "atomId": id,
    }
    result = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    with open("test.mp3", "wb") as f:
        f.write(base64.b64decode(result.content))
    print("done")


def scrape_docs(id):
    url = "https://members.riteplanning.com/File/Download"
    form_data = {
        "atomId": id,
        "useType": "Testing / Community Group Worship",
        "useDate": "12/12/2022",
        "numCopies": 1,
    }
    result = requests.post(url, data=form_data, cookies=cookies_string_to_dict(cookies))
    print(result.headers)
    # print(result.content)
    file_name = result.headers["Content-Disposition"].split("filename=")[1].replace('"', "")
    print(file_name)
    with open(file_name, "wb") as f:
        f.write(result.content)
    print("done")


def construct_hymn(row):
    children = row.findChildren("td", recursive=False)
    title = children[2].attrs["data-title"]
    title_parts = title.split("(")
    title = title_parts[0].strip()
    tune = title_parts[1].replace(")", "").strip() if len(title_parts) > 1 else ""
    return {
        "number": children[1].text.strip(),
        "title": title,
        "tune": tune,
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
    last_page = soup.find("li", {"class": "PagedList-skipToLast"}).find("a").attrs["href"]
    pages = range(1, int(last_page) + 1)
    for i in pages:
        form_data["page"] = i
        result = requests.post(url, cookies=cookies_string_to_dict(cookies), data=form_data)
        soup = BeautifulSoup(result.content, "html.parser")
        rows = soup.find_all("tr", id=lambda value: value and value.startswith("result-"))
        for row in rows:
            hymn = construct_hymn(row)
            print(hymn)


def scrape():
    id = 602050
    get_hymn_list()

#!/usr/bin/env python

import sys
import requests


# API_KEY = "0ef851dd8743c8230145ee91f6dc30f210dee235"
# API_URL = "https://api.esv.org/v3/passage/text/"
#
#
# def get_esv_text(passage):
#     params = {
#         "q": passage,
#         "include-headings": True,
#         "include-footnotes": False,
#         "include-verse-numbers": False,
#         "include-short-copyright": False,
#         "include-passage-references": True,
#     }
#
#     headers = {"Authorization": "Token %s" % API_KEY}
#
#     response = requests.get(API_URL, params=params, headers=headers)
#
#     print(response.json())
#
#     passages = response.json()["passages"]
#
#     return passages[0].strip() if passages else "Error: Passage not found"
#
#
# if __name__ == "__main__":
#     passage = " ".join(sys.argv[1:])
#
#     if passage:
#         print(get_esv_text(passage))


API_KEY = "575ee0f3ddd09aef1529fb5847fb4370"
API_URL = "https://api.scripture.api.bible/v1/bibles"


def get_other_text(passage):

    headers = {"api-key": API_KEY}

    response = requests.get(API_URL, headers=headers)

    bibles = response.json()["data"]
    for bible in bibles:
        if bible["language"]["id"] == "eng":
            print(bible["abbreviation"], bible["name"])

    # passages = response.json()["passages"]
    #
    # return passages[0].strip() if passages else "Error: Passage not found"


if __name__ == "__main__":
    passage = " ".join(sys.argv[1:])

    if passage:
        print(get_other_text(passage))

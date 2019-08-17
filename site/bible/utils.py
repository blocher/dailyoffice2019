import requests


def get_passage(url, passage):
    r = requests.get(url, auth=("user", "pass"))

    r.headers["content-type"]
    r.encoding

    r.text
    r.json()

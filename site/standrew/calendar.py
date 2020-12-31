import datetime

import requests
from django.template.loader import render_to_string

from standrew.utils import send_mail


def get_week():
    base = datetime.datetime.today()
    dates = [base + datetime.timedelta(days=x) for x in range(8)]
    weekdays = []
    major_feast_names = []
    for date in dates:
        result = requests.get(
            "http://api.dailyoffice2019.com/api/v1/calendar/{}-{}-{}".format(date.year, date.month, date.day)
        )
        if result.status_code != 200:
            print("ERROR")
            continue
        content = result.json()
        content["filtered_feasts"] = [
            feast for feast in content["commemorations"] if "FERIA" not in feast["rank"]["name"]
        ]
        major_feast_names = major_feast_names + [
            feast["name"] for feast in content["commemorations"] if int(feast["rank"]["precedence"]) <= 4
        ]
        weekdays.append(content)
    print(weekdays)
    html = render_to_string("emails/weekly_email.html", {"weekdays": weekdays})

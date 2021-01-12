import calendar
from datetime import datetime, timedelta
from math import ceil

import requests
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from website.settings import GOOGLE_API_KEY, ZOOM_LINK


class SundayEmailModule(object):
    @cached_property
    def date_range(self):
        return [self.full_date_range[0], self.full_date_range[-1]]

    @cached_property
    def full_date_range(self):
        now = timezone.localtime(timezone.now())
        now = datetime.strptime("{} {} {}".format(5, 13, 2021), "%m %d %Y")
        return [(now + timedelta(days=x)).date() for x in range(9)]

    def get_data(self):
        raise NotImplementedError

    def render(self):
        pass


class LiturgicalCalendarSundayEmailModule(SundayEmailModule):
    def get_data(self):
        dates = self.full_date_range
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
        return weekdays

    def render(self):
        return render_to_string('emails/weekly_email/liturgical_celebrations.html', {"days": self.get_data()})


class BirthdaysSundayEmailModule(SundayEmailModule):
    @staticmethod
    def has_birthday_completed(birthday):
        try:
            month = birthday[2]
            date = birthday[3]
        except IndexError:
            return False
        if birthday[2] and birthday[3]:
            return True
        return False

    def birthday_to_date(self, birthday):

        now = self.date_range[0]
        year = now.year
        if now.month == 12 and birthday[2] == 1:
            year = year + 1
        return datetime.strptime("{} {} {}".format(birthday[2], birthday[3], year), "%m %d %Y").date()


    def birthday_to_born_date(self, birthday):
        try:
            year = birthday[4]
        except IndexError:
            return False
        if not birthday[4]:
            return False
        return datetime.strptime("{} {} {}".format(birthday[2], birthday[3], birthday[4]), "%m %d %Y").date()

    def birthday_in_range(self, birthday):

        if not self.has_birthday_completed(birthday):
            return False

        birthday = self.birthday_to_date(birthday)
        return self.date_range[0] <= birthday <= self.date_range[1]

    def calculate_age(self, birthday):
        born = self.birthday_to_born_date(birthday)
        if not born:
            return False
        birthday = self.birthday_to_date(birthday)

        return birthday.year - born.year - ((birthday.month, birthday.day) < (born.month, born.day))

    def decorate_birthday(self, birthday):
        birthday += [""] * (9 - len(birthday))
        birthday[7] = self.birthday_to_date(birthday)
        birthday[8] = self.calculate_age(birthday)
        return birthday

    def get_data(self):

        SPREADSHEET_ID = "1BpaVvpi66UKojz9SnO41iLKfVTggWq2jI_ReniyCeH4"
        RANGE_NAME = "A2:G35"
        service = build("sheets", "v4", developerKey=GOOGLE_API_KEY)

        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            return

        birthdays = [
            self.decorate_birthday(birthday) for birthday in result["values"] if self.birthday_in_range(birthday)
        ]
        birthdays = sorted(birthdays, key=lambda birthday: (birthday[2], birthday[3]))
        return birthdays

    def render(self):
        return render_to_string('emails/weekly_email/birthdays.html', {"birthdays": self.get_data()})




class StAndrewScheduleSundayEmailModule(SundayEmailModule):
    def get_tuesday(self):
        return [d for d in self.full_date_range if d.weekday() == 1][0]

    def get_friday(self):
        return [d for d in self.full_date_range if d.weekday() == 4][0]

    def get_tuesday_number(self):
        return ceil(self.get_tuesday().day / 7)

    def get_friday_type(self):
        first_friday = datetime.strptime('Jan 15 2021  12:00AM', '%b %d %Y %I:%M%p').date()
        current_friday = self.get_friday()
        difference = (current_friday - first_friday).days / 7
        if difference % 4 == 0:
            return "game"
        if difference % 2 == 0:
            return "movie"
        return "none"


    def get_optional(self):

        if self.get_friday_type() == "game":
            return [
                {
                    "title": "Game night",
                    "date": self.get_friday(),
                    "time": "8:45 p.m. to ?",
                    "zoom_link": ZOOM_LINK,
                    "slack_link": "slack://channel?team=T010PPE1R2Q&id=C010PU011HB",
                    "optional": True,
                },
            ]
        if self.get_friday_type() == "movie":
            return [
                {
                    "title": "Movie night",
                    "date": self.get_friday(),
                    "time": "8:45 p.m. to ?",
                    "zoom_link": ZOOM_LINK,
                    "slack_link": "slack://channel?team=T010PPE1R2Q&id=C010VJ4HX9T",
                    "optional": True,
                },
            ]
        return []

    def get_required(self):
        tuesday_number = self.get_tuesday_number()
        if tuesday_number in (1, 3):
            return [
                {
                    "title": "Morningside Cell Meeting",
                    "date": self.get_tuesday(),
                    "time": "6 to 8 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                },
                {
                    "title": "O'Hara Cell Meeting",
                    "date": self.get_tuesday(),
                    "time": "8:30 to 10:30 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                },
            ]
        if tuesday_number == 2:
            return [
                {
                    "title": "Women's Discipleship Group",
                    "date": self.get_tuesday(),
                    "time": "7 to 9 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                },
            ]
        if tuesday_number == 4:
            return [
                {
                    "title": "Men's Discipleship Group",
                    "date": self.get_tuesday(),
                    "time": "7 to 9 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                },
            ]
        if tuesday_number == 5 and timezone.now().year == "2021":
            return [
                {
                    "title": "The Color of Compromise Discussion (Both cells)",
                    "date": self.get_tuesday(),
                    "time": "6 to 8 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                },
            ]

        return []

    def get_data(self):
        return self.get_required() + self.get_optional()


    def render(self):
        return render_to_string('emails/weekly_email/schedule.html', {"schedule": self.get_data()})


def weekly_email():
    return [StAndrewScheduleSundayEmailModule(), BirthdaysSundayEmailModule(), LiturgicalCalendarSundayEmailModule() ]

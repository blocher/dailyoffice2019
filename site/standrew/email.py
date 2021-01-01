import calendar
from datetime import datetime, timedelta
from math import ceil

import requests
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from website.settings import GOOGLE_API_KEY


class SundayEmailModule(object):
    @cached_property
    def date_range(self):
        return [self.full_date_range[0], self.full_date_range[-1]]

    @cached_property
    def full_date_range(self):
        now = timezone.localtime(timezone.now())
        # now = datetime.strptime("{} {} {}".format(12, 26, 2020), "%m %d %Y")
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
        return weekdays


class BirthdaysSundayEmailModule(SundayEmailModule):
    @staticmethod
    def has_birthday_completed(birthday):
        try:
            month = birthday[2]
            date = birthday[3]
        except IndexError:
            return False
        return True

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
        return self.date_range[0] < birthday <= self.date_range[1]

    def calculate_age(self, birthday):
        born = self.birthday_to_born_date(birthday)
        birthday = self.birthday_to_date(birthday)
        if not born:
            return False
        return birthday.year - born.year - ((birthday.month, birthday.day) < (born.month, born.day))

    def decorate_birthday(self, birthday):
        birthday += [""] * (7 - len(birthday))
        birthday[5] = self.birthday_to_date(birthday)
        birthday[6] = self.calculate_age(birthday)
        return birthday

    def get_data(self):

        SPREADSHEET_ID = "1BpaVvpi66UKojz9SnO41iLKfVTggWq2jI_ReniyCeH4"
        RANGE_NAME = "A2:E35"
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

        return birthdays

    def render(self):
        html = render_to_string("emails/weekly_email.html", {"birthdays": self.get_data()})


class StAndrewScheduleSundayEmailModule(SundayEmailModule):
    def get_tuesday(self):
        return [d for d in self.full_date_range if d.weekday() == 1][0]

    def get_tuesday_number(self):
        return ceil(self.get_tuesday().day / 7)

    def get_data(self):
        tuesday_number = self.get_tuesday_number()
        if tuesday_number in (1, 3):
            return ["morningside_cell", "ohara_cell"]
        if tuesday_number == 2:
            return ["women"]
        if tuesday_number == 4:
            return ["men"]
        if tuesday_number == 5 and timezone.now().year == "2021":
            return ["both_cells"]
        if tuesday_number == 5:
            return ["none"]

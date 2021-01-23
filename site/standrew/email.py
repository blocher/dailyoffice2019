from datetime import datetime, timedelta

from math import ceil

import requests
from churchcal.api.serializer import DaySerializer
from churchcal.calculations import get_calendar_date
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from website.settings import GOOGLE_API_KEY, ZOOM_LINK


class SundayEmailModule(object):
    def __init__(self, *args, **kwargs):
        self.subjects = None

    @cached_property
    def date_range(self):
        return [self.full_date_range[0], self.full_date_range[-1]]

    @cached_property
    def full_date_range(self):
        now = timezone.localtime(timezone.now())
        # now = datetime.strptime("{} {} {}".format(1, 28, 2021), "%m %d %Y")
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
        subjects = []
        for date in dates:
            # result = requests.get(
            #     "http://api.dailyoffice2019.com/api/v1/calendar/{}-{}-{}".format(date.year, date.month, date.day)
            # )
            # if result.status_code != 200:
            #     print("ERROR")
            #     continue
            # content = result.json()

            date = timezone.now().replace(year=date.year, month=date.month, day=date.day)
            calendar_date = get_calendar_date(date)
            serializer = DaySerializer(calendar_date)
            content = serializer.data

            content["filtered_feasts"] = [
                feast for feast in content["commemorations"] if "FERIA" not in feast["rank"]["name"]
            ]
            major_feast_names = major_feast_names + [
                feast["name"] for feast in content["commemorations"] if int(feast["rank"]["precedence"]) <= 4
            ]
            subjects = subjects + [
                feast["name"]
                for feast in content["commemorations"]
                if int(feast["rank"]["precedence"]) <= 4 and "SUNDAY" not in feast["rank"]["name"]
            ]
            weekdays.append(content)
        self.subjects = subjects
        return weekdays

    def render(self):
        return render_to_string("emails/weekly_email/liturgical_celebrations.html", {"days": self.get_data()})


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
        self.subjects = ["{} 🎂 ({})".format(birthday[1], birthday[7].strftime("%a %-d")) for birthday in birthdays]
        return birthdays

    def render(self):
        return render_to_string("emails/weekly_email/birthdays.html", {"birthdays": self.get_data()})


class StAndrewScheduleSundayEmailModule(SundayEmailModule):
    def get_tuesday(self):
        return [d for d in self.full_date_range if d.weekday() == 1][0]

    def get_friday(self):
        return [d for d in self.full_date_range if d.weekday() == 4][0]

    def get_tuesday_number(self):
        return ceil(self.get_tuesday().day / 7)

    def get_friday_type(self):
        first_friday = datetime.strptime("Jan 15 2021  12:00AM", "%b %d %Y %I:%M%p").date()
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
                    "to_addresses": [
                        "community-of-st-andrew-all@googlegroups.com",
                        "community-of-st-andrew-alumni@googlegroups.com",
                    ],
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
                    "to_addresses": [
                        "community-of-st-andrew-all@googlegroups.com",
                        "community-of-st-andrew-alumni@googlegroups.com",
                    ],
                },
            ]
        return []

    def get_notes(self):

        SPREADSHEET_ID = "1lRsThD20a2thgtJk97J_bqEBxJBCqXPIg_UkFAqzMq8"
        RANGE_NAME = "MeetingNotes!A2:F1000"
        service = build("sheets", "v4", developerKey=GOOGLE_API_KEY)
        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            return

        tuesday = self.get_tuesday()
        for day in result["values"]:
            date = datetime.strptime(day[0], "%A, %B %d, %Y").date()
            if tuesday == date:
                return {
                    "notes": day[1],
                    "chapter": day[2],
                    "book": day[3],
                    "book_link": day[4],
                    "author": day[5],
                }

    def get_leader(self, cell):
        SPREADSHEET_ID = "1lRsThD20a2thgtJk97J_bqEBxJBCqXPIg_UkFAqzMq8"
        RANGE_NAME = "A2:C50"
        service = build("sheets", "v4", developerKey=GOOGLE_API_KEY)
        sheet = service.spreadsheets()

        try:
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        except HttpError as e:
            print(e)
            return

        tuesday = self.get_tuesday()
        for day in result["values"]:
            date = datetime.strptime(day[0], "%A, %B %d, %Y").date()
            if tuesday == date:
                if cell == "morningside":
                    return day[1]
                if cell == "ohara":
                    return day[2]

        return "?"

    def tuesday_subjects(self):
        tuesday_number = self.get_tuesday_number()
        if tuesday_number in (1, 3):
            return ["Cell meetings (Tue)"]
        if tuesday_number == 2:
            return ["Women's group (Tue)"]
        if tuesday_number == 4:
            return ["Men's group (Tue)"]
        if tuesday_number == 5 and timezone.now().year == "2021":
            return ["Discussion's group (Tue)"]

        return ["No Tuesday meeting this week"]

    def friday_subjects(self):
        if self.get_friday_type() == "game":
            return ["Game night (Fri)"]
        if self.get_friday_type() == "movie":
            return ["Movie night (Fri)"]
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
                    "leader": self.get_leader("morningside"),
                    "notes": self.get_notes(),
                    "meeting": "morningside",
                    "to_addresses": ["community-of-st-andrew-cell-morningside@googlegroups.com"],
                },
                {
                    "title": "O'Hara Cell Meeting",
                    "date": self.get_tuesday(),
                    "time": "8:30 to 10:30 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                    "leader": self.get_leader("ohara"),
                    "notes": self.get_notes(),
                    "meeting": "ohara",
                    "to_addresses": ["community-of-st-andrew-cell-morningside@googlegroups.com"],
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
                    "notes": self.get_notes(),
                    "to_addresses": ["community-of-st-andrew-cell-ohara@googlegroups.com"],
                    "meeting": "women",
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
                    "notes": self.get_notes(),
                    "to_addresses": ["community-of-st-andrew-men@googlegroups.com"],
                    "meeting": "men",
                },
            ]
        if tuesday_number == 5 and timezone.now().year == 2021:
            return [
                {
                    "title": "The Color of Compromise Discussion (Both cells)",
                    "date": self.get_tuesday(),
                    "time": "6 to 8 pm",
                    "zoom_link": ZOOM_LINK,
                    "optional": False,
                    "notes": self.get_notes(),
                    "to_addresses": ["community-of-st-andrew-women@googlegroups.com"],
                    "meeting": "both_cells",
                },
            ]

        return []

    def get_data(self):
        self.subjects = self.tuesday_subjects() + self.friday_subjects()
        return self.get_required() + self.get_optional()

    def render(self):
        return render_to_string("emails/weekly_email/schedule.html", {"schedule": self.get_data()})


class CommemorationDailyEmailModule(object):
    @cached_property
    def subject(self):
        if not self.data["feasts"]:
            return None
        feasts = [feast["name"] for feast in self.data["feasts"]]
        feasts = "; ".join(feasts)
        return "Happy Feast Day: {}".format(feasts)

    @cached_property
    def should_send(self):
        return True if self.data["feasts"] else False

    @cached_property
    def data(self):

        date = timezone.now()
        # date = datetime.strptime("{} {} {}".format(1, 25, 2021), "%m %d %Y")
        result = requests.get(
            "http://api.dailyoffice2019.com/api/v1/calendar/{}-{}-{}".format(date.year, date.month, date.day)
        )
        if result.status_code != 200:
            print("ERROR")
            return
        content = result.json()
        major_feasts = [
            feast
            for feast in content["commemorations"]
            if int(feast["rank"]["precedence"]) <= 4 and feast["rank"]["name"] != "SUNDAY"
        ]
        return {
            "day": content,
            "feasts": major_feasts,
            "today": timezone.now(),
        }

    def render(self):
        if self.should_send:
            return render_to_string("emails/weekly_email/major_feast.html", self.data)
        else:
            return "There are no feasts today."


class WeeklyMeetingEmailModule(StAndrewScheduleSundayEmailModule):
    def __init__(self):
        self.today = timezone.now().date()
        # self.today = datetime.strptime("{} {} {}".format(1, 29, 2021), "%m %d %Y").date()

    @cached_property
    def subject(self):
        if not self.get_data():
            return None
        return "TONIGHT: {} ({})".format(self.get_data()[0]["title"], self.get_data()[0]["time"])

    @cached_property
    def should_send(self):
        return len(self.get_data()) > 0

    def render(self):
        if self.should_send:
            return [
                render_to_string("emails/weekly_email/weekly_meeting.html", {"meeting": meeting})
                for meeting in self.get_data()
            ]
        else:
            return []

    def get_data(self):
        data = super().get_data()
        return [meeting for meeting in data if meeting["date"] == self.today]


def weekly_email():
    return [StAndrewScheduleSundayEmailModule(), BirthdaysSundayEmailModule(), LiturgicalCalendarSundayEmailModule()]

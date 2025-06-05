import datetime
from datetime import date
from io import BytesIO

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from icalendar import Calendar, Event

from churchcal.calculations import ChurchYear
from office.offices import Office
from website import settings


class Command(BaseCommand):
    help = "My shiny new management command."

    def build_calendar(self, year, major=False):
        cal = Calendar()
        cal.add("prodid", "-//Daily Office//mxm.dk//")
        cal.add("version", "2.0")
        year = ChurchYear(year)
        for datestring, calendardate in year.dates.items():
            office = Office(datestring)
            event = Event()
            event.add("SUMMARY", calendardate.primary.name)
            event.add("DTSTART", date(calendardate.date.year, calendardate.date.month, calendardate.date.day))
            event.add(
                "URL",
                "https://www.dailyoffice2019.com/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                ),
            )
            event.add(
                "LOCATION",
                "https://www.dailyoffice2019.com/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                ),
            )
            fast_day = calendardate.fast_day != calendardate.FAST_NONE

            feast_day = calendardate.primary.rank.precedence_rank <= 4
            if major and not feast_day:
                continue

            description_lines = []
            for feast in calendardate.all:
                description_lines.append(feast.name)

            if fast_day:
                description_lines.append("")
                description_lines.append("FAST DAY")

            if feast_day:
                description_lines.append("")
                description_lines.append("SUNDAY OR MAJOR HOLY DAY")

            description_lines.append("")
            description_lines.append("MORNING PRAYER (or year 1)")
            description_lines.append("Psalms {} (30 day cycle)".format(office.thirty_day_psalter_day.mp_psalms))
            description_lines.append("Psalms {} (60 day cycle)".format(office.office_readings.mp_psalms))
            description_lines.append(office.office_readings.mp_reading_1)
            description_lines.append(office.office_readings.mp_reading_2)
            description_lines.append("")
            description_lines.append("EVENING PRAYER (or year 2)")
            description_lines.append("Psalms {} (30 day cycle)".format(office.thirty_day_psalter_day.ep_psalms))
            description_lines.append("Psalms {} (60 day cycle)".format(office.office_readings.ep_psalms))
            description_lines.append(office.office_readings.ep_reading_1)
            description_lines.append(office.office_readings.ep_reading_2)

            if calendardate.primary.rank.precedence_rank <= 4:
                description_lines.append("")
                description_lines.append("EUCHARIST")
                for reading in calendardate.mass_readings:
                    description_lines.append(reading.long_citation)
            description_lines.append("")
            description_lines.append(
                "Morning Prayer: https://www.dailyoffice2019.com/morning_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Midday Prayer: https://www.dailyoffice2019.com/midday_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Evening Prayer: https://www.dailyoffice2019.com/evening_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Compline: https://www.dailyoffice2019.com/compline/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )

            description_lines.append(
                "Family Prayer in the Morning: https://www.dailyoffice2019.com/family/morning_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer at Midday: https://www.dailyoffice2019.com/family/midday_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer in the Early Evening: https://www.dailyoffice2019.com/family/early_evening_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer at the Close of Day: https://www.dailyoffice2019.com/family/close_of_day_prayer/{}/{}/{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )

            event.add("DESCRIPTION", "\n".join(description_lines))

            cal.add_component(event)

        return cal.to_ical()

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        current_year = now.year
        start = current_year - 3
        end = current_year + 10
        for year in range(start, end):
            print("Generating {}".format(year))
            
            # Generate regular calendar
            calendar_data = self.build_calendar(year)
            filename = f"churchcal/ics/acna_church_calendar_{year}-{year + 1}.ics"
            calendar_file = BytesIO(calendar_data)
            default_storage.save(filename, calendar_file)

            print("Generating Major Only{}".format(year))
            
            # Generate major days only calendar
            major_calendar_data = self.build_calendar(year, major=True)
            major_filename = f"churchcal/ics/acna_church_calendar_major_days_only_{year}-{year + 1}.ics"
            major_calendar_file = BytesIO(major_calendar_data)
            default_storage.save(major_filename, major_calendar_file)

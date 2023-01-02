from datetime import datetime

from churchcal.management.commands.import_base import Command as ImportCommemorationsBaseCommand
from churchcal.models import Proper


class Command(ImportCommemorationsBaseCommand):
    help = "Imports Propers"

    RANGE_NAME = "Propers!A2:H700"

    def import_dates(self):
        Proper.objects.filter(calendar=self.calendar).delete()
        for row in self.values:
            if row[0]:
                start_date = datetime.strptime("2019-{}-{}".format(row[3], row[4]), "%Y-%m-%d").date()
                end_date = datetime.strptime("2019-{}-{}".format(row[5], row[6]), "%Y-%m-%d").date()
                proper = Proper.objects.create(
                    number=row[0], start_date=start_date, end_date=end_date, calendar=self.calendar
                )

                try:
                    proper.collect = row[7]
                    proper.save()
                except IndexError:
                    proper.collect = None

                print(row[0])

    def import_not_after(self):
        return

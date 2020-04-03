from churchcal.management.commands.import_base import ImportCommemorationsBaseCommand
from churchcal.models import MassReading, Common


class Command(ImportCommemorationsBaseCommand):
    help = "Imports Commons of the Saints, plus Ember and Rogation Days"

    RANGE_NAME = "Commons!A1:E14"

    def import_dates(self):

        Common.objects.filter(calendar=self.calendar).delete()
        self.values.pop(0)
        for i, row in enumerate(self.values):
            common = Common()
            common.abbreviation = row[0]
            common.name = row[1]
            common.collect = row[2]
            common.alternate_collect = row[3]
            common.calendar = self.calendar
            common.save()

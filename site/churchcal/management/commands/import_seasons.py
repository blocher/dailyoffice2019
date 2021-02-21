from churchcal.management.commands.import_base import Command as ImportCommemorationsBaseCommand
from churchcal.models import Season, Commemoration, CommemorationRank


class Command(ImportCommemorationsBaseCommand):

    help = "Imports Seasons"

    RANGE_NAME = "Seasons!A2:I700"

    def import_dates(self):

        Season.objects.filter(calendar=self.calendar).delete()
        for i, row in enumerate(self.values):
            if row[0]:
                Season.objects.create(
                    order=i,
                    name=row[1],
                    start_commemoration=Commemoration.objects.get(name=row[0]),
                    color=row[2],
                    alternate_color=row[3],
                    rank=CommemorationRank.objects.filter(calendar=self.calendar).get(name=row[4]),
                    calendar=self.calendar,
                )

                print(row[1])

    def import_not_after(self):

        return

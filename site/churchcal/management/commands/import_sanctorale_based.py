from churchcal.management.commands.import_base import ImportCommemorationsBaseCommand
from churchcal.models import CommemorationRank, SanctoraleBasedCommemoration, Commemoration


class Command(ImportCommemorationsBaseCommand):

    help = "Imports Episcopal sanctorale"

    RANGE_NAME = "SanctoraleBased!A2:N700"

    def import_dates(self):
        for row in self.values:
            if row[0]:
                rank = CommemorationRank.objects.filter(name=row[1]).first()
                commemoration = SanctoraleBasedCommemoration.objects.create(
                    name=row[0],
                    weekday=row[2],
                    number_after=row[3],
                    month_after=row[4],
                    day_after=row[5],
                    rank=rank,
                    calendar=self.calendar,
                )
                try:
                    commemoration.color = row[6]
                except IndexError:
                    commemoration.color = None
                try:
                    commemoration.additional_color = row[9]
                except IndexError:
                    commemoration.additional_color = None
                try:
                    commemoration.alternate_color = row[7]
                except IndexError:
                    commemoration.alternate_color = None
                try:
                    commemoration.alternate_color_2 = row[8]
                except IndexError:
                    commemoration.alternate_color_2 = None
                try:
                    commemoration.color_notes = row[10]
                except IndexError:
                    commemoration.color_notes = None
                try:
                    commemoration.collect = row[12]
                except IndexError:
                    commemoration.collect = None
                try:
                    commemoration.alternate_collect = row[13]
                except IndexError:
                    commemoration.alternate_collect = None
                commemoration.save()
                print(row)
                print(row[0])

    def import_not_after(self):

        for row in self.values:
            if len(row) > 11 and row[11]:
                commemoration = SanctoraleBasedCommemoration.objects.filter(calendar=self.calendar).get(name=row[0])
                commemoration.cannot_occur_after = Commemoration.objects.filter(calendar=self.calendar).get(
                    name=row[11]
                )
                print("{} cannot occur after {}".format(commemoration.name, commemoration.cannot_occur_after.name))
                commemoration.save()

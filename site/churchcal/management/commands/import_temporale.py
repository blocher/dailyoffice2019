from churchcal.management.commands.import_base import ImportCommemorationsBaseCommand
from churchcal.models import CommemorationRank, TemporaleCommemoration, Commemoration


class Command(ImportCommemorationsBaseCommand):

    help = "Imports Episcopal temporale"

    RANGE_NAME = "Temporale!A2:L700"

    def import_dates(self):

        for row in self.values:
            if row[0]:
                rank = CommemorationRank.objects.filter(name=row[1]).first()
                commemoration = TemporaleCommemoration.objects.create(
                    name=row[0], days_after_easter=row[2], rank=rank, calendar=self.calendar
                )

                try:
                    commemoration.color = row[4]
                except IndexError:
                    commemoration.color = None
                try:
                    commemoration.additional_color = row[7]
                except IndexError:
                    commemoration.additional_color = None
                try:
                    commemoration.alternate_color = row[5]
                except IndexError:
                    commemoration.alternate_color = None
                try:
                    commemoration.alternate_color_2 = row[6]
                except IndexError:
                    commemoration.alternate_color_2 = None
                try:
                    commemoration.color_notes = row[8]
                except IndexError:
                    commemoration.color_notes = None
                commemoration.save()
                try:
                    commemoration.collect = row[9]
                except IndexError:
                    commemoration.collect = None
                commemoration.save()
                try:
                    commemoration.alternate_collect = row[10]
                except IndexError:
                    commemoration.alternate_collect = None
                commemoration.save()
                try:
                    commemoration.eve_collect = row[11]
                except IndexError:
                    commemoration.eve_collect = None
                commemoration.save()
                print(row[0])

    def import_not_after(self):

        for row in self.values:
            if len(row) > 3 and row[3]:
                commemoration = TemporaleCommemoration.objects.filter(calendar=self.calendar).get(name=row[0])
                commemoration.cannot_occur_after = Commemoration.objects.filter(calendar=self.calendar).get(
                    name=row[3]
                )
                print("{} cannot occur after {}".format(commemoration.name, commemoration.cannot_occur_after.name))
                commemoration.save()

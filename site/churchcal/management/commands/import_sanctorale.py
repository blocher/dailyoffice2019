from churchcal.management.commands.import_base import ImportCommemorationsBaseCommand
from churchcal.models import CommemorationRank, SanctoraleCommemoration, Commemoration


class Command(ImportCommemorationsBaseCommand):

    help = "Imports Episcopal sanctorale"

    RANGE_NAME = "Sanctorale!A2:R700"

    def import_dates(self):

        for row in self.values:
            if row[0]:
                rank = CommemorationRank.objects.filter(name=row[1]).first()
                commemoration = SanctoraleCommemoration.objects.create(
                    name=row[0], month=row[2], day=row[3], rank=rank, calendar=self.calendar
                )
                try:
                    commemoration.color = row[5]
                except IndexError:
                    commemoration.color = None
                try:
                    commemoration.additional_color = row[8]
                except IndexError:
                    commemoration.additional_color = None
                try:
                    commemoration.alternate_color = row[6]
                except IndexError:
                    commemoration.alternate_color = None
                try:
                    commemoration.alternate_color_2 = row[7]
                except IndexError:
                    commemoration.alternate_color_2 = None
                try:
                    commemoration.color_notes = row[9]
                except IndexError:
                    commemoration.color_notes = None
                try:
                    commemoration.collect = row[10]
                except IndexError:
                    commemoration.collect = None
                try:
                    commemoration.eve_collect = row[11]
                except IndexError:
                    commemoration.eve_collect = None

                try:
                    commemoration.saint_name = row[12]
                except IndexError:
                    commemoration.saint_name = None

                try:
                    commemoration.saint_type = row[13]
                except IndexError:
                    commemoration.saint_type = None

                try:
                    commemoration.saint_gender = row[14]
                except IndexError:
                    commemoration.saint_gender = None

                try:
                    commemoration.saint_fill_in_the_blank = row[15]
                except IndexError:
                    commemoration.saint_fill_in_the_blank = None

                try:
                    commemoration.link_1 = row[16]
                except IndexError:
                    commemoration.link_1 = None

                try:
                    commemoration.link_2 = row[17]
                except IndexError:
                    commemoration.link_2 = None

                try:
                    commemoration.link_3 = row[18]
                except IndexError:
                    commemoration.link_3 = None

                commemoration.save()

    def import_not_after(self):

        for row in self.values:
            if len(row) > 4 and row[4]:
                commemoration = SanctoraleCommemoration.objects.filter(calendar=self.calendar).get(name=row[0])
                commemoration.cannot_occur_after = Commemoration.objects.filter(calendar=self.calendar).get(
                    name=row[4]
                )
                print("{} cannot occur after {}".format(commemoration.name, commemoration.cannot_occur_after.name))
                commemoration.save()

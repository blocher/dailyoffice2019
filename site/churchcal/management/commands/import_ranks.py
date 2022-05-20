from django.conf import settings
from django.core.management.base import BaseCommand
from googleapiclient.discovery import build

from churchcal.models import CommemorationRank, Calendar

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"

SPREADSHEET_ID = "1tx3LIrKAzMBO2LH7vA1943OQl8jY5lmSd5RtMEaXoPM"
RANGE_NAME = "Ranks!A2:D100"


class Command(BaseCommand):
    help = "Imports ranks for commemorations"

    def add_arguments(self, parser):
        parser.add_argument("--calendar", dest="calendar", help="Import not after import_dates")

    def handle(self, *args, **options):

        if not options["calendar"]:
            raise Exception("You must supply a calendar id for which to import ranks.")

        try:
            calendar = Calendar.objects.get(pk=options["calendar"])
        except Calendar.DoesNotExist:
            raise Exception("You must supply a valid calendar id for which to import ranks.")

        service = build("sheets", "v4", developerKey=settings.GOOGLE_API_KEY)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=calendar.google_sheet_id, range=RANGE_NAME).execute()
        values = result.get("values", [])
        if not values:
            print("No data found.")
        else:
            CommemorationRank.objects.filter(calendar=calendar).delete()
            for row in values:
                if row[0]:
                    CommemorationRank.objects.create(
                        calendar=calendar,
                        name=row[0],
                        formatted_name=row[1],
                        precedence_rank=row[2],
                        required=True if row[3].upper() == "TRUE" else False,
                    )
                    print(row[0])

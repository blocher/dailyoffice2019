from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup

from psalter.models import Psalm, PsalmVerse
from website.settings import BASE_DIR


class Command(BaseCommand):
    help = "Import the psalms"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        soup = BeautifulSoup(open("{}/psalter/psalms.html".format(BASE_DIR)), "html5lib")
        for br in soup.find_all("br", class_="footnote"):
            br.decompose()
        psalm_number = 0
        psalm = None
        psalm_verse = None
        latin_title = ""
        first_half_next = False
        second_half_next = False
        latin_next = False
        for line in soup.find_all("p"):
            line = line.text.strip()
            if line[:3] == "DAY":
                pass
            elif line.isnumeric():
                first_half_next = False
                psalm_number = line
                latin_next = True
            elif latin_next:
                latin_title = line
                psalm = Psalm.objects.get_or_create(number=psalm_number)[0]
                print(psalm_number)
                psalm.latin_title = latin_title
                psalm.save()
                latin_next = False
                first_half_next = True
            elif first_half_next:
                words = line.split(" ")
                verse = words.pop(0)
                if not verse.isnumeric():
                    continue
                line = " ".join(words)
                line = line.replace(" * ", "")
                line = line.replace(" *", "")
                line = line.replace("*", "")
                try:
                    psalm_verse = PsalmVerse.objects.get_or_create(psalm=psalm, number=verse)[0]
                except Exception as e:
                    print(line)
                    continue
                line = line.replace("<br/>", " ").replace("<br />", " ").replace("<br>", " ")
                line = line.replace("\n", " ").replace("\r", "").replace("\t", "")
                line = line.replace("  ", " ")
                psalm_verse.first_half = line
                first_half_next = False
                second_half_next = True
            elif second_half_next:
                line = line.replace("<br/>", " ").replace("<br />", " ").replace("<br>", " ")
                line = line.replace("\n", " ").replace("\r", "")
                line = line.replace("  ", " ")
                psalm_verse.second_half = line
                psalm_verse.save()
                first_half_next = True
                second_half_next = False

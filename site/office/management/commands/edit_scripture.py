from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from office.models import Scripture

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"


class Command(BaseCommand):
    def handle(self, *args, **options):
        passages = Scripture.objects.all()
        for passage in passages:
            nasb = BeautifulSoup(passage.nasb, "html5lib")
            for match in nasb.find_all("i"):
                match.replaceWithChildren()
            passage.nasb = str(nasb)
            nabre = BeautifulSoup(passage.nabre, "html5lib")
            for match in nabre.find_all("b", class_="inline-h3"):
                match.name = "h3"
            for match in nabre.find_all("h2", class_="outline"):
                match.name = "h3"
                match["class"] = "bible-outline"
            for match in nabre.find_all("h3", class_="outline"):
                match["class"] = "bible-outline"
            for match in nabre.find_all("h3", class_="chapter"):
                match.name = "span"
                match["class"] = "chapternum"
                match.string = match.text.replace("Chapter ", "")
            for match in nabre.find_all("span", class_="chapternum"):
                match.string = match.text.replace("Chapter ", "")
            passage.nabre = str(nabre)
            passage.save()

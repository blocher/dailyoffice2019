import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from office.models import CollectCategory, Collect


def remove_smart_quotes(text):
    return text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


class Command(BaseCommand):
    help = "Import the Occasional Collects"

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        CollectCategory.objects.all().delete()
        Collect.objects.all().delete()
        category_order = 0
        collect_order = 0
        for i in range(1, 126):
            url = "https://occasionalprayers.com/acna2019/{}.html".format(i)
            data = requests.get(url)
            data.encoding = data.apparent_encoding
            html = BeautifulSoup(data.text, "html.parser")
            headings = html.select("h2")
            heading = headings[0].text
            text = (
                html.select("main")[0]
                .decode_contents(indent_level=None, formatter="html")
                .strip()
                .replace(" Amen.", " <strong>Amen.</strong>")
            )
            tag = ""
            tags = html.select(".tags")[0].find_all("a")
            if tags:
                tag = tags[0].text
            try:
                attribution = html.select("small")[0].text
            except IndexError:
                attribution = ""
            print(tag)

            category = CollectCategory.objects.get_or_create(name=tag)
            if category[1]:
                category_order += 1
            category = category[0]
            category.order = category_order
            category.save()

            collect_order = collect_order + 1
            collect = Collect()
            collect.collect_category = category
            collect.title = heading
            collect.text = text
            collect.order = collect_order
            collect.attribution = attribution
            collect.collect_type = "occasional"
            collect.save()

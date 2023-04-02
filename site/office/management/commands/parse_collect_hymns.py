import os
import re
import shutil

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from office.models import MetricalCollect, Collect

mappings = {
    ("c8842381-8278-41ce-a4a8-1ed94dc5593a", 1),
    ("4f129ae5-20e8-4a4c-bd5b-7a1809319971", 2),
    ("8d72a23c-8747-4ce3-b8ea-18c98b739f55", 3),
    ("e5d8f45c-ead8-4d86-99ca-36816bc9a0b7", 4),
    ("16ac733e-c7a0-49fd-8cea-bcb76353e214", 5),
    ("81f758ff-3ffa-4b47-91ae-cf2784059390", 6),
    ("3f6b6df9-f4cf-4740-82c6-70e1025c7bda", 7),
    ("9253c541-3187-48f6-9c91-af67f10fe03e", 8),
    ("84ef48f3-43e7-4ab7-9316-d6fa37210947", 9),
    ("dd652309-3985-48a0-a4f7-8eb4cece9342", 10),
    ("20298bb1-c152-4b67-8a9f-918bd4b6f8eb", 11),
    ("cb25b742-30f3-4f3f-b1f9-28e47785f8e8", 12),
    ("84ef48f3-43e7-4ab7-9316-d6fa37210947", 13),
    ("c1c149f9-f6e4-4bc1-bbeb-8fd7a1507717", 14),
    ("544ce0f7-8eb1-426c-98d8-eec8f8245175", 15),
    ("e91552b4-42f7-405f-8ada-e68e8b75573f", 17),
    ("8dbbe1c4-4171-443f-84ed-599c6282a262", 19),
    ("cbcb913e-16bf-4e3d-abb5-d19d223c73af", 20),
    ("61dad133-8c15-4004-ab64-14fbbce0d373", 21),
    ("1f3a37c0-f9e8-465c-bb97-ba9fc877dd6f", 24),
    ("b470f46f-5b1f-481e-87f0-848d76409007", 25),
    ("7c0f4d61-6db9-4244-b26e-2181ca0ec7e2", 26),
    ("9d2e8368-ce5b-40b3-b65c-b0c2572f9f7a", 30),
    ("d347755e-8b62-4db7-be91-6e72bfbf2613", 31),
    ("e99c6c73-7830-41f6-9936-045513061888", 32),
    ("b3ebf9bc-90fe-4328-95d4-115d993035ee", 33),
    ("e4e7ce67-8deb-46c0-8f88-505ee1635a02", 35),
    ("1894b27b-7fd0-4b04-90d2-8f75a1c28805", 36),
    ("1894b27b-7fd0-4b04-90d2-8f75a1c28805", 37),
    ("1894b27b-7fd0-4b04-90d2-8f75a1c28805", 38),
    ("1597d568-a525-445f-bf09-aaeb80db29c3", 39),
    ("a4acd76f-fa69-4925-b1b1-9bd17ce3a5b9", 40),
    ("7d02b01e-4f27-4ee6-898e-9de6086fefe5", 41),
    ("f323eb27-c9e7-4e96-acb6-570561fe47d2", 42),
    ("c83ba715-c236-4b7d-b92f-aea51d0cf180", 43),
    ("97863055-e958-4e0e-9297-9bed419a0803", 44),
    ("cde826a3-c6b4-46a7-8ddd-db49750fd53f", 45),
    ("18277cfe-afb3-4c4e-9908-96a460829ba1", 46),
    ("18277cfe-afb3-4c4e-9908-96a460829ba1", 47),
    ("18277cfe-afb3-4c4e-9908-96a460829ba1", 48),
    ("b69cc66f-1e4a-48fb-8dba-640a5904d0e4", 49),
    ("759c57fc-692f-4795-b829-1d6a49d127c0", 50),
    ("ff717bfd-1f60-4172-baf4-f2430fb7f2cb", 51),
    ("4641c12c-36f8-4354-aa10-52cea0862591", 52),
    ("05e734e4-a846-42a9-822b-563926ed93a2", 53),
    ("f313651d-4ac2-4e35-a55b-2c3d54ae5ff2", 54),
    ("f1c10165-ba1b-4dbb-b403-62104be45ca6", 55),
    ("4de46487-559d-4220-ad74-39e2ae909642", 56),
    ("87e94ae3-7b19-45b1-b0a4-3ef275a3b8b3", 57),
    ("d2230acb-cd34-4fd2-b948-c525dd916923", 58),
    ("d2230acb-cd34-4fd2-b948-c525dd916923", 59),
    ("1cb48374-059f-4247-b135-9d5259728361", 60),
    ("dd381d76-1e82-41f1-9794-1985ef18583a", 61),
    ("00fb98c5-a922-407d-941d-792f293da599", 62),
    ("5df95372-e33b-4c1b-9d9f-91ec7f4ba201", 63),
    ("cdc4672f-cd2e-46a4-8bd0-315e55b6986c", 64),
    ("bc4e2c5c-18c3-4a4a-910b-c0b07a9387ad", 65),
    ("8c66ec37-709d-45de-b9c0-dba2b771af65", 66),
    ("cca33ed2-47ac-4117-af52-bb68fbecaf3a", 67),
    ("8442ba0d-9e30-4084-b144-a8334a3e8d97", 68),
    ("98d09d73-8b4f-4ec3-a43b-9325d47315e0", 69),
    ("aa1b7d1f-cb77-4f49-89fa-86631165737b", 70),
    ("75d04387-beb3-46b5-ab08-0efa269570e3", 71),
    ("ebfd63ea-8d0e-4662-81de-843f36562e7a", 72),
    ("1ffd46ae-7a4e-44b9-8dcf-7cb460b1e5b0", 73),
    ("e8fd6c71-b69d-4f34-a626-8506380f84ef", 75),
    ("7c9f404a-be74-425e-838f-71de4a899a1c", 76),
    ("9fb4b2af-0416-4395-8b33-163f3319b65b", 77),
    ("b113e9ae-e5db-4be4-8253-0015dce2adc1", 78),
    ("972c787e-357c-4af2-8b7d-3ff2f403a401", 79),
    ("27375465-f2a6-45f9-8a96-b8b8d2c451d6", 80),
    ("36f96ab3-67e6-4815-b85e-8196bf2d6de5", 81),
    ("8ede2619-fd58-432e-bb24-cc4da38d1ec4", 82),
    ("bf1c2b45-573b-4c36-a023-8dba488a45fd", 83),
    ("cd44f2f2-bfef-43c4-b35a-3715778879ea", 84),
    ("a4115de7-05d7-472f-8144-b65b6b2da719", 85),
    ("22ebcee6-56fd-42a2-b264-ebfb1c3fb673", 86),
    ("ece0a141-92f5-4867-af7d-9bd7a50bfe90", 87),
    ("205190a8-6887-4dc8-9caa-e4cdec57d0ae", 88),
    ("b1ca6d86-bcca-45ba-b87f-6db34dc1ec07", 89),
    ("af7927f2-db8c-4360-9ea0-5129a7269baa", 90),
    ("eedd7150-84af-4d1c-9066-ab9a904147ba", 91),
    ("8d8c36ab-b61f-4990-8e70-aba5cfbba4bb", 92),
    ("a38a1202-38f4-4bad-8127-caa88862e722", 93),
    ("63d4d279-f5c1-4e41-8b9e-483a64a84e08", 94),
    ("52d5fa34-95dc-477c-a10d-2491931dafa1", 95),
    ("ae39267c-4a8a-445e-847e-2d87c4573423", 96),
    ("7b81a6ad-d203-4584-b309-9966fd516dd4", 97),
    ("99521e70-8594-40a6-81b0-ec64b4a661a1", 100),
    ("2440611f-dd7d-42b8-ba35-54aca255d984", 102),
    ("Venite", 103),
    ("Jubilate", 104),
    ("Pascha Nostrum", 105),
    ("Phos Hilaron", 106),
    ("S5", 107),
    ("S8", 108),
    ("S4", 109),
    ("S2", 110),
    ("S10", 111),
    ("MP2", 112),
    ("S3", 113),
    ("EP1", 114),
    ("MP3", 115),
    ("EP2", 116),
    ("S6", 117),
    ("S1", 118),
    ("O1", 119),
    ("MP1", 120),
    ("Alma Redemptoris Mater", 121),
    ("Ave Regina Caelorum ", 122),
    ("Regina Caeli", 123),
    ("Salve Regina", 124),
}


def normalize_collect_text(text):
    text = BeautifulSoup(text, "html5lib").text
    text = text.replace("Amen.", "")
    regex = re.compile("[^a-zA-Z ]")
    text = regex.sub(" ", text)
    text = text.strip().lower()
    text = re.sub("\s\s+", " ", text)
    return text


def normalize_collect(collect):
    collect.normalized_text = normalize_collect_text(collect.text)
    collect.normalized_traditional_text = normalize_collect_text(collect.traditional_text)
    collect.save()


def normalize_collects():
    for collect in Collect.objects.all():
        normalize_collect(collect)


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        normalize_collects()
        link = "https://metricalcollects.com/index/first_line/"
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html5lib")
        rows = soup.findAll("tr")
        for row in rows:
            columns = row.findAll("td")
            if columns:
                site_link = columns[3].find("a").get("href")
                site_link = site_link.replace("../..", "https://metricalcollects.com")
                first_line = columns[0].text
                tune_name = columns[1].text
                collect_number = int(columns[3].text)

                metrical_collect = MetricalCollect.objects.get_or_create(collect_number=collect_number)[0]
                metrical_collect.first_line = first_line
                metrical_collect.tune_name = tune_name
                metrical_collect.site_link = site_link

                r = requests.get(site_link)
                soup = BeautifulSoup(r.text, "html5lib")
                blocks = soup.findAll("div", class_="tabbed-block")
                name = blocks[-1].find("center")
                if name:
                    name = name.text
                    metrical_collect.name = name
                else:
                    metrical_collect.name = name = ""
                collect_texts = blocks[-1].findAll("p")
                if collect_texts:
                    collect = ""
                    for text in collect_texts:
                        i = text.find("i")
                        if not i:
                            if text.text.strip():
                                collect = collect + text.text.strip()
                    metrical_collect.original_collect = collect
                else:
                    metrical_collect.original_collect = ""

                pdf_link = soup.findAll("a", class_="md-button")[0].get("href")
                pdf_link = "https://metricalcollects.com" + pdf_link
                metrical_collect.pdf_link = pdf_link
                metrical_collect.normalized_original_collect = normalize_collect_text(
                    metrical_collect.original_collect
                )

                metrical_collect.lyrics = ""
                lyrics = blocks[1].findAll("tr")
                for lyric in lyrics:
                    columns = lyric.findAll("td")
                    if columns:
                        line = columns[1].decode_contents()
                        metrical_collect.lyrics += "<p>" + line + "</p>\n\r"
                metrical_collect.lyrics = metrical_collect.lyrics.strip()

                metrical_collect.midi_link = "https://metricalcollects.com" + soup.findAll("midi-player")[0].get("src")

                info = blocks[2].findAll("tr")
                metrical_collect.text_source = info[1].findAll("td")[1].decode_contents()
                metrical_collect.tune_source = info[2].findAll("td")[1].decode_contents()

                print(collect_number, name, first_line, tune_name, site_link)
                metrical_collect.save()
                related_collects = Collect.objects.filter(
                    Q(normalized_traditional_text=metrical_collect.normalized_original_collect)
                    | Q(normalized_text=metrical_collect.normalized_original_collect)
                ).all()
                if related_collects:
                    for collect in related_collects:
                        collect.metrical_collect = metrical_collect
                        collect.save()
                        print("****", collect.pk)

                folder_to_store = settings.STATIC_ROOT + "/metrical_collects/pdf"
                isExist = os.path.exists(folder_to_store)
                if not isExist:
                    os.makedirs(folder_to_store)
                full_filename = os.path.join(folder_to_store, str(collect_number) + ".pdf")
                response = requests.get(metrical_collect.pdf_link, stream=True)
                with open(full_filename, "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)

                folder_to_store = settings.STATIC_ROOT + "/metrical_collects/midi"
                isExist = os.path.exists(folder_to_store)
                if not isExist:
                    os.makedirs(folder_to_store)
                full_filename = os.path.join(folder_to_store, str(collect_number) + ".midi")
                response = requests.get(metrical_collect.midi_link, stream=True)
                with open(full_filename, "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)

        Collect.objects.update(metrical_collect=None, metrical_collect_2=None, metrical_collect_3=None)

        for id, number in mappings:
            try:
                collect = Collect.objects.get(pk=id)
            except:
                continue
            metrical_collect = MetricalCollect.objects.get(collect_number=number)
            if not collect.metrical_collect:
                collect.metrical_collect = metrical_collect
                collect.save()
                continue
            if not collect.metrical_collect_2:
                collect.metrical_collect_2 = metrical_collect
                collect.save()
                continue
            if not collect.metrical_collect_3:
                collect.metrical_collect_3 = metrical_collect
                collect.save()
                continue

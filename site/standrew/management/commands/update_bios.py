from django.core.management.base import BaseCommand

from churchcal.models import Commemoration
from standrew.bios import google_image_search, clean_string, perplexity


class Command(BaseCommand):
    help = "Send weekly St. Andrew email"

    def handle(self, *args, **options):
        feasts = Commemoration.objects.filter(ai_one_sentence__isnull=False).all()
        for feast in feasts:
            print(feast.name, feast.uuid)
            feast.ai_one_sentence = clean_string(feast.ai_one_sentence)
            feast.ai_quote = clean_string(feast.ai_quote)
            feast.ai_quote_by = clean_string(feast.ai_quote_by)
            feast.ai_verse = clean_string(feast.ai_verse)
            feast.ai_verse_citation = clean_string(feast.ai_verse_citation)
            feast.ai_hagiography = clean_string(feast.ai_hagiography)
            feast.ai_legend = clean_string(feast.ai_legend)
            feast.ai_legend_title = clean_string(feast.ai_legend_title)
            feast.ai_bullet_points = clean_string(feast.ai_bullet_points)
            feast.ai_traditions = clean_string(feast.ai_traditions)
            feast.ai_foods = clean_string(feast.ai_foods)
            feast.ai_lesser_feasts_and_fasts = clean_string(feast.ai_lesser_feasts_and_fasts)
            feast.ai_martyrology = clean_string(feast.ai_martyrology)
            feast.ai_butler = clean_string(feast.ai_butler)
            if not feast.ai_legend_title:
                message = f"Extract the title from the first line of the following text and return just the text without an intro or conclusion: {feast.ai_legend}"
                result = perplexity(message)[0]
                feast.ai_legend_title = result
                print(feast.ai_legend_title)
            feast.ai_legend_title = clean_string(feast.ai_legend_title)

            if not feast.ai_image_1 or not feast.ai_image_2:
                results = google_image_search(feast.name)
                filenames = []
                good_ones = []
                for result in results:
                    filename = result.split("/")[-1]
                    filename = filename.split("?")[0]
                    print(filename)
                    if filename not in filenames:
                        filenames.append(filename)
                        good_ones.append(result)
                if good_ones:
                    feast.ai_image_1 = good_ones[0]
                    if len(good_ones) > 1:
                        feast.ai_image_2 = good_ones[1]
            feast.save()

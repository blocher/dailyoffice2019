import json
import os
from typing import List

import requests
from django.core.files.temp import NamedTemporaryFile
from django.utils import timezone
from openai import OpenAI
from pydantic import BaseModel

from bible.passage import Passage
from standrew.models import BibleStudyPassage, BibleStudyDay
from website import settings


def prepare_bible_study_passage(citation):
    bible_study_passage = BibleStudyPassage.objects.get_or_create(passage=citation)[0]

    scripture = Passage(citation, source="esv")

    bible_study_passage.html = scripture.html
    bible_study_passage.text = scripture.text

    client = OpenAI(api_key=settings.PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

    class PrimarySource(BaseModel):
        author_name: str
        author_denomination: str | None
        author_birth_year_if_known: int | None
        author_death_year_if_known: int | None
        source_title: str
        source_description: str
        source_url: str | None
        source_date_year_if_known: int | None

    class PrimarySourceCategories(BaseModel):
        patristic: List[PrimarySource]
        doctor: List[PrimarySource]
        reformation: List[PrimarySource]
        modern: List[PrimarySource]

    class FourSenses(BaseModel):
        literal: str
        allegorical: str
        moral_or_tropological: str
        anagogical: str

    class Questions(BaseModel):
        questions: List[str]

    class Headings(BaseModel):
        headings: List[str]

    questions = [
        f"For the rest of this conversation, I am working with the passage {citation}. The full text of the passage is: {scripture.text}.",
        f"Extract headings from the passage {scripture.html}. Make them text only (remove any html).",
        f"What is the main theme of this passage: {citation}?",
        f"Throughout time how has the church interpreted {citation} according to each of the four senses of scripture: literal, allegorical, moral or tropological, and anagogical? Be fairly detailed and cite sources.",
        f"Provide any background needed to understand {citation} in terms of authorship, date, historical context, literary context, references to other scripture passages, and what happened before and after these passages in the Bible. Be detailed.",
        f"List three or more primary sources that interpret {citation} in each of these categories: patristic (written between year 0 and year 700), doctors (only from doctors of the church, east or west), reformation and later (from 1500 to 1950) and modern from (1950 to {timezone.now().year}). For modern sources, please include only Roman Catholic, Eastern Orthodox, Anglican, Episcopal, and Lutheran sources. For each one, include 1-2 sentences summarizing the source, the authors name and (if available) birth and death dates, a URL to read the full source, and the author's Christian denomination). Make sure the URL is a valid, current URL still accessible on the Internet. NEVER make up a URL.",
        f"What are some unique, interesting, or far-out points that can be said about {citation}? Don't just give the same comon, boring stuff.",
        f"Study questions: Prepare six or more questions for a bible study on {citation} that include a range of themes and will provoke interesting, challenging conversation. You might want to include questions about the historical, cultural, and literary context, the theological meaning, different interpretations, and how it all applies to our lives today as lay Christians and in family life. Any questions that provoke hearty conversations are great.",
        f"Practical questions: Prepare three or more questions for a bible study on Hebrews 1 that about how it can be applied to our common life today as lay Christians living in the world. These questions should be far ranging and spark great conversations!",
        f"Prepare a lengthy lecture or reflection based on {citation} that is suitable for a bible study. It should be about 300-500 words. It should cite multiple sources from different eras. It should be compelling, convicting, and motivational.",
        f"What are the title or subject headings you might commonly find printed for this passage: {citation} in the RSV?",
    ]

    messages = [
        {
            "role": "system",
            "content": "You are a Roman Catholic priest who always answers pastorally better never contradicts the magisterium of the Roman Catholic church. You should answer just the question without adding conversation.",
        },
    ]

    for i, question in enumerate(questions):
        messages.append({"role": "user", "content": question})
        params = {
            "model": "gpt-4o",
            "messages": messages,
        }
        client = OpenAI()
        if "primary sources" in question:
            params["response_format"] = PrimarySourceCategories
            # params["model"] = "sonar"
            # client = OpenAI(api_key=settings.PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
            # params["response_format"] = {"type": "json_schema",
            #                              "json_schema": {"schema": PrimarySourceCategories.model_json_schema()}}
        if "four senses" in question:
            params["response_format"] = FourSenses
        if "questions" in question:
            params["response_format"] = Questions
        if "headings" in question:
            params["response_format"] = Headings

        if params["model"] == "gpt-4o":

            completion = client.beta.chat.completions.parse(**params)
        else:
            print("BOOM")
            completion = client.chat.completions.create(**params)
        print()
        print()
        print()
        print()
        print(f"==={question}===")
        print()
        print(completion.choices[0].message.content)
        if i == 1:
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.extracted_headings = content["headings"]
        if i == 2:
            bible_study_passage.theme = completion.choices[0].message.content
        if i == 3:
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.four_senses = content
        if i == 4:
            bible_study_passage.background = completion.choices[0].message.content
        if i == 5:
            print(completion.choices[0].message.content)
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.primary_sources = content
        if i == 6:
            bible_study_passage.interesting_points = completion.choices[0].message.content
        if i == 7:
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.study_questions = content["questions"]
        if i == 8:
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.practical_questions = content["questions"]
        if i == 9:
            bible_study_passage.reflection = completion.choices[0].message.content
        if i == 10:
            content = json.loads(completion.choices[0].message.content)
            bible_study_passage.headings = content["headings"]

        messages.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

    bible_study_passage.save()


def prepare_bible_study(study_day):
    from openai import OpenAI

    client = OpenAI()

    class Questions(BaseModel):
        questions: List[str]

    passages = [x.bible_study_passage.passage for x in study_day.biblestudydaypassage_set.all()]
    citation = ", ".join(passages)
    text = " == ".join([x.bible_study_passage.text for x in study_day.biblestudydaypassage_set.all()])

    questions = [
        f"For the rest of this conversation, I am working with the passage(s) {citation}. The full text of the passage is: {text}.",
        f"Summarize the chapter for the Jesus Storybook Bible by Sally Lloyd-Jones that is titled {study_day.jesus_story_book_title}.",
        f"Explain to me the intersection between the passages in {citation}.",
        f"Study questions: Prepare six or more questions for a bible study on {citation} that include a range of themes and will provoke interesting, challenging conversation. You might want to include questions about the historical, cultural, and literary context, the theological meaning, different interpretations, and how it all applies to our lives today as lay Christians and in family life. Any questions that provoke hearty conversations are great.",
        f"Practical questions: Prepare three or more questions for a bible study on Hebrews 1 that about how it can be applied to our common life today as lay Christians living in the world. These questions should be far ranging and spark great conversations!",
        f"Prepare a lengthy lecture or reflection based on {citation} that is suitable for a bible study. It should be about 300-500 words. It should cite multiple sources from different eras. It should be compelling, convicting, and motivational. It should include thoughts on every passage in the list if there is more than one.",
    ]

    messages = [
        {
            "role": "system",
            "content": "You are a Roman Catholic priest who always answers pastorally better never contradicts the magisterium of the Roman Catholic church. You should answer just the question without adding conversation.",
        },
    ]

    for i, question in enumerate(questions):
        if len(passages) == 1 and i > 1:
            break
        messages.append({"role": "user", "content": question})
        params = {
            "model": "gpt-4o",
            "messages": messages,
        }
        if "questions" in question:
            params["response_format"] = Questions
        completion = client.beta.chat.completions.parse(**params)
        print()
        print()
        print()
        print()
        print(f"==={question}===")
        print()
        print(completion.choices[0].message.content)

        if i == 1:
            print("HERE!!")
            study_day.jesus_story_book_summary = completion.choices[0].message.content
        if i == 2:
            study_day.intersection = completion.choices[0].message.content
        if i == 3:
            content = json.loads(completion.choices[0].message.content)
            study_day.study_questions = content["questions"]
        if i == 4:
            print("*****")
            print(completion, completion.choices[0].message.content, question)
            print("^^^^^")
            content = json.loads(completion.choices[0].message.content)
            study_day.practical_questions = content["questions"]
        if i == 5:
            study_day.reflection = completion.choices[0].message.content

        messages.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

    if len(passages) == 1:
        study_day.intersection = ""
        study_day.study_questions = study_day.biblestudydaypassage_set.all()[0].bible_study_passage.study_questions
        study_day.practical_questions = study_day.biblestudydaypassage_set.all()[
            0
        ].bible_study_passage.practical_questions
        study_day.reflection = study_day.biblestudydaypassage_set.all()[0].bible_study_passage.reflection

    study_day.save()


def create_image(study_day):
    passages = [x.bible_study_passage.passage for x in study_day.biblestudydaypassage_set.all()]

    client = OpenAI()
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"Make a beautiful, artistic, meditative image based on either or any of the passages of the Bible: {passages}.",
        size="1792x1024",
        quality="standard",
        n=1,
    )

    url = response.data[0].url

    response = requests.get(url)
    if response.status_code == 200:
        with NamedTemporaryFile(delete=True) as img_temp:
            img_temp.write(response.content)
            img_temp.flush()
            img_temp.seek(0)

            # Define the path where the image will be saved
            img_name = f"{study_day.pk}.png"
            img_path = os.path.join(settings.MEDIA_ROOT, img_name)

            with open(img_path, "wb") as f:
                f.write(img_temp.read())

        # Return the public URL
        return os.path.join(settings.MEDIA_URL, img_name)
    else:
        return None


def import_jesus_storybook_bible():
    jesus_storybook_bible = [
        (1, "The Story and the Song", "God’s Story and Glory", [("Psalm 19"), ("Hebrews 1")]),
        (2, "The Beginning: A Perfect Home", "Creation", [("Genesis 1-2")]),
        (3, "The Terrible Lie", "The Fall", [("Genesis 3")]),
        (4, "A New Beginning", "Noah’s Ark", [("Genesis 6-9")]),
        (5, "A Giant Staircase to Heaven", "The Tower of Babel", [("Genesis 11")]),
        (6, "Son of Laughter", "God’s Promise to Abraham", [("Genesis 12-21")]),
        (7, "The Present", "Abraham and Isaac", [("Genesis 22")]),
        (8, "The Girl No One Wanted", "Jacob, Leah, and Rachel", [("Genesis 29-30")]),
        (9, "The Forgiving Prince", "Joseph", [("Genesis 37-50")]),
        (10, "God to the Rescue!", "Moses and the Exodus", [("Exodus 3-13")]),
        (11, "God Makes a Way", "The Red Sea", [("Exodus 14-15")]),
        (12, "Ten Ways to Be Perfect", "The Ten Commandments", [("Exodus 16-17"), ("Exodus 19-40")]),
        (13, "The Warrior Leader", "Joshua and Jericho", [("Joshua 3, 6")]),
        (14, "The Teeny, Weenie... True King", "David Chosen as King", [("1 Samuel 16")]),
        (15, "The Young Hero and the Horrible Giant", "David and Goliath", [("1 Samuel 17")]),
        (16, "The Good Shepherd", "David’s Psalms", [("Psalm 23")]),
        (17, "A Little Servant Girl and the Proud General", "Naaman", [("2 Kings 5")]),
        (18, "Operation 'No More Tears'", "Isaiah's Prophecy", [("Isaiah 9, 11, 40, 50, 53, 55, 60")]),
        (19, "Daniel and the Scary Sleepover", "Daniel in the Lion’s Den", [("Daniel 6")]),
        (20, "God’s Messenger", "Jonah", [("Jonah 1-4")]),
        (21, "Get Ready!", "Nehemiah and Malachi", [("Nehemiah 8-10"), ("Malachi 1, 3, 4")]),
        (22, "He’s Here!", "Jesus’ Birth", [("Luke 1-2")]),
        (23, "The Light of the Whole World", "Shepherds and Angels", [("Luke 2")]),
        (24, "The King of All Kings", "The Wise Men", [("Matthew 2")]),
        (
            25,
            "Heaven Breaks Through",
            "John the Baptist and Jesus’ Baptism",
            [("Matthew 3"), ("Luke 1, 3"), ("John 1")],
        ),
        (26, "Let’s Go!", "Jesus Calls His Disciples", [("Mark 1")]),
        (27, "A Little Girl and a Poor Frail Lady", "Jesus’ Miracles", [("Mark 5")]),
        (28, "How to Pray", "The Lord’s Prayer", [("Matthew 6")]),
        (29, "The Singer", "Jesus’ Teaching on Trust", [("Matthew 6, 9"), ("Luke 12")]),
        (30, "The Captain of the Storm", "Jesus Calms the Storm", [("Mark 4"), ("Matthew 8")]),
        (31, "Filled Full!", "Feeding the 5,000", [("Matthew 14"), ("Mark 6"), ("Luke 9")]),
        (32, "Treasure Hunt!", "Parables of the Kingdom", [("Matthew 13")]),
        (
            33,
            "The Friend of Little Children",
            "Jesus Welcomes Children",
            [("Matthew 18-19"), ("Mark 10"), ("Luke 18")],
        ),
        (34, "The Man Who Didn’t Have Any Friends (None)", "Zacchaeus", [("Luke 19")]),
        (35, "Running Away", "The Prodigal Son", [("Luke 15")]),
        (36, "Washed with Tears", "Jesus Anointed", [("Mark 14"), ("Luke 7"), ("John 12")]),
        (37, "The Servant King", "The Last Supper", [("Mark 14"), ("John 13-14")]),
        (38, "A Dark Night in the Garden", "Gethsemane", [("Luke 22"), ("Mark 14"), ("John 18")]),
        (39, "The Sun Stops Shining", "The Crucifixion", [("Matthew 27"), ("Mark 15"), ("Luke 23"), ("John 19")]),
        (40, "God’s Wonderful Surprise", "The Resurrection", [("Matthew 28"), ("Mark 16"), ("Luke 24"), ("John 20")]),
        (41, "Going Home", "The Ascension", [("Matthew 28"), ("Mark 16"), ("Luke 24"), ("John 14")]),
        (42, "God Sends Help", "Pentecost", [("Acts 1-5"), ("John 15")]),
        (
            43,
            "A New Way to See",
            "Paul’s Conversion",
            [("Acts 6-9, 12-28"), ("Colossians 2"), ("Romans 8"), ("Ephesians 2")],
        ),
        (44, "A Dream of Heaven", "Revelation", [("Revelation 1, 5, 21-22")]),
    ]
    from datetime import datetime, timedelta

    def generate_dates():
        start_date = datetime(2025, 2, 4)
        count = 44
        dates = []
        current_date = start_date
        while len(dates) < count:
            if current_date.weekday() == 1:  # Check if it's Tuesday
                # Check if it's the 1st or 3rd Tuesday of the month
                if 1 <= current_date.day <= 7 or 15 <= current_date.day <= 21:
                    dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

    dates = generate_dates()

    for i, chapter in enumerate(jesus_storybook_bible):
        study_day = BibleStudyDay.objects.get_or_create(jesus_story_book_number=chapter[0])[0]
        study_day.date = dates[i]
        study_day.jesus_story_book_number = chapter[0]
        study_day.jesus_story_book_title = chapter[1]
        study_day.passage_title = chapter[2]
        study_day.save()
        if not study_day.image_url:
            study_day.image_url = create_image(study_day)
            study_day.save()
        # for passage in chapter[3]:
        #     passage = BibleStudyPassage.objects.get_or_create(passage=passage)[0]
        #     study_day.biblestudydaypassage_set.get_or_create(
        #         bible_study_passage=passage
        #     )
        # if study_day.jesus_story_book_number < 2:
        #     for passage in study_day.biblestudydaypassage_set.all():
        #         prepare_bible_study_passage(passage.bible_study_passage.passage)
        #     prepare_bible_study(study_day)


def google_image_search():
    url = "https://www.googleapis.com/customsearch/v1"
    days = BibleStudyDay.objects.filter(image_url__isnull=True, jesus_story_book_number__lte=10).all()
    for day in days:
        params = {
            "q": f"{day.passage_title} Bible painting or art horizontal",  # Search query
            "cx": settings.GOOGLE_CUSTOM_SEARCH_ENGINE_KEY,  # Custom Search Engine ID
            "key": settings.GOOGLE_API_KEY,  # API Key
            "searchType": "image",  # Image search
            "num": 5,  # Number of results
            "rights": "cc_publicdomain,cc_attribute,cc_sharealike,cc_noncommercial",
            "imgSize": "large",  # Ensure images are at least 500px by 500px
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            results = response.json()
            images = [item["link"] for item in results.get("items", [])]
            print(images)
        else:
            print(f"Error: {response.status_code}, {response.text}")

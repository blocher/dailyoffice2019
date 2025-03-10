import json
import os
import re
from typing import List

import openai
import requests
from pydantic import BaseModel

from churchcal.models import Commemoration
from website import settings

# Replace with your actual API key
openai.api_key = settings.OPENAI_API_KEY


# Upload PDF files as knowledge sources
def upload_file(path):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}/data/{path}", "rb") as file:
        response = openai.files.create(file=file, purpose="assistants")
        print(response)
        return response.id


def create_vector_store():
    files = [
        ("BCP2019.pdf", "The Book of Common Prayer (2019)"),
        ("BCP2019Spanish.pdf", "The Book of Common Prayer (2019) (Spanish Language)"),
        ("BCP2019TLE.pdf", "The Book of Common Prayer (2019) (Traditional Language Edition)"),
        ("BookOfHomilies.pdf", "The Two Books of Homilies"),
        ("LesserFeastsAndFasts2018.pdf", "Lesser Feasts and Fasts (2018)"),
        ("LivesOfTheSaints.txt", "Alban Butler's Complete Lives of the Saints"),
        ("RomanMartyrology.pdf", "The Roman Martyrology"),
        ("ToBeAChristianACNACatehcism.pdf", "To Be a Christian: An Anglican Catechism (ACNA)"),
    ]
    vector_store = openai.beta.vector_stores.create(name="ACNA Documents")

    # Ready the files for upload to OpenAI
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_paths = [f"{dir_path}/data/{path}" for path, title in files]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = openai.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # You can print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)
    return vector_store, files


def create_custom_assistant():
    vector_store, files = create_vector_store()
    file_titles = ", ".join([f"{file[0]} ({file[1]})" for file in files])
    assistant = openai.beta.assistants.create(
        name="Anglican Assistant",
        instructions=f"You are a helpful Anglican theologian, historian, liturgist, and priest dedicated to answering theological questions and consulting authoritative documents from an orthodox Anglican perspective, particularly within the Anglican Church in North America (ACNA). You provide well-researched, clear, and thoughtful responses grounded in Scripture, the Book of Common Prayer (2019), and To Be a Christian: An Anglican Catechism. Consult each of these files {file_titles} in addition to web searches. Your tone is respectful, compassionate, and insightful, reflecting the Anglican tradition's emphasis on faith, reason, and tradition. You prioritizes doctrinal accuracy and integrity, ensuring that it represents Anglican beliefs fairly while acknowledging ecumenical contexts. Upon request, you can assist with writing, editing, and refining hagiographies, theological essays, sermons, and reflections with a scholarly yet pastoral style. You are a knowledgeable AI assistant with access to web search, code execution, DALL·E image generation, and data analysis. Use uploaded PDFs as reference materials when responding as well as web searches. Please both search upload files and use your general knowledge to make a comprehensive response.",
        model="gpt-4o",
        tools=[
            {"type": "code_interpreter"},
            {"type": "file_search"},
            # {"type": "dalle_image_generation"},
            # {"type": "web_browser"},
            # {"type": "canvas"}
        ],
    )
    print(assistant)
    assistant = openai.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    print(assistant)
    return assistant


class BibleVerse(BaseModel):
    citation: str
    text: str
    bible_version: str


class Food(BaseModel):
    food_name: str
    description: str
    country_of_origin: str


class Tradition(BaseModel):
    tradition: str
    country_of_origin: str


class Quote(BaseModel):
    quote: str
    person: str
    date: str | None


class Bio(BaseModel):
    one_sentence_description: str
    quote: Quote
    bible_verse: BibleVerse
    top_fact_bullet_points: List[str]
    hagiographical_biography: str
    butler_lives_of_the_saints_biography: str | None
    roman_martyrology_biography: str | None
    lesser_feasts_and_fasts_biography: str | None
    important_traditions: List[Tradition] | None
    import_food: List[Food] | None


# Example function to interact with the assistant
# def chat_with_assistant(user_input, assistant_id="asst_Cn21k5w6SVb7pBMLYXhtVxgL"):
def chat_with_assistant(user_input, assistant_id="asst_U7P5XMh4YbRRyEYz76fFbZ1M"):
    thread = openai.beta.threads.create()
    message = openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_input)
    run = openai.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
        response_format="auto",
    )
    if run.status == "completed":
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        assistant_response = next(msg.content for msg in messages if msg.role == "assistant")
        print(assistant_response[0].text.value)
        return assistant_response[0].text.value

    else:
        print(run.status)
        return ""


def perplexity(message):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": f"You are a helpful Anglican theologian, historian, liturgist, and priest dedicated to answering theological questions and consulting authoritative documents from an orthodox Anglican perspective, particularly within the Anglican Church in North America (ACNA). You provide well-researched, clear, and thoughtful responses grounded in Scripture, the Book of Common Prayer (2019), and To Be a Christian: An Anglican Catechism. You prioritizes doctrinal accuracy and integrity. Upon request, you can assist with writing, editing, and refining hagiographies, theological essays, sermons, and reflections with a scholarly yet pastoral style. You are a knowledgeable AI assistant with access to web search. Please ensure the accuracy of your responses.",
            },
            {"role": "user", "content": message},
        ],
        "search_domain_filter": None,
    }
    headers = {"Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}", "Content-Type": "application/json"}

    response = requests.request("POST", url, json=payload, headers=headers)
    result = json.loads(response.content)
    return (result["choices"][0]["message"]["content"], result["citations"])


def clean_string(s):
    if not s:
        return ""
    cleaned = s.replace(" ", " ")
    cleaned = re.sub(r"【.*?】", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    if cleaned == "N/A":
        return ""
    if cleaned == "null":
        return ""
    if cleaned == '""':
        return ""
    if not cleaned:
        return ""
    return cleaned


def extract_and_remove_parenthetical(s):
    # Regex to capture the last set of parentheses in the string
    match = re.search(r"\(([^)]*?)\)(?!.*\()", s)
    if match:
        extracted = match.group(1)  # Capture the content inside the last parentheses
        # Remove the last parenthetical (with optional preceding whitespace)
        s = re.sub(r"\s*\([^)]*?\)(?!.*\()", "", s)
    else:
        extracted = None
    return s.strip(), extracted


def go(commemoration, overwrite=False):
    person = commemoration.name
    name = commemoration.saint_name

    prompts = [
        (
            "ai_one_sentence",
            None,
            f"Who is {person} in exactly one sentence? Include what the person is known for and their role in the Christian life and church.",
        ),
        (
            "ai_quote",
            "ai_quote_citations",
            f"List one quote either by or about {person} that best represents them and their importance to Christianity? Only return the quote and author and citations -- no other text. The book author should be in a parenthetical at the end.",
        ),
        (
            "ai_verse",
            None,
            f"What is one bible verse in English Standard Version that best represents the life, work, and beliefs of {person} ? Include the quote with book chapter and verse but absolutely no other text. The book chapter and verse should be in a parenthetical at the end.",
        ),
        (
            "ai_hagiography",
            "ai_hagiography_citations",
            f"Write a hagiographical biography of {person} that is at least 6 paragraphs and 500 words and is rather detailed. Include just the biography -- no intro text or other text",
        ),
        (
            "ai_legend",
            "ai_legend_citations",
            f"Tell an story, anecdote, or pious legend from the life of {person} that is interesting and revealing of their character and faith. Begin with a Title on its own line. Include just the title and story -- no intro text or other text. Tell it as storyteller with a narrative, dramatic style.",
        ),
        (
            "ai_bullet_points",
            "ai_bullet_points_citations",
            f"Summarize {person}'s life and contributions to the Christian life in 4-6 short bullet points. Include just the bullet points -- no intro text or other text.",
        ),
        (
            "ai_traditions",
            "ai_traditions_citations",
            f"Include a bulleted list of interesting traditions for the feast day of {person} from around the world with which country they are from. If there is nothing notable, return just the letters 'N/A' and absolutely no other text. Do not use the first person ever. Include just the bullet points -- no intro text or other text.",
        ),
        (
            "ai_foods",
            "ai_foods_citations",
            f"Include a bulleted list of interesting foods or culinary habits for the feast day of {person} from around the world with which country they are from. If there is nothing notable, return just the letters 'N/A' and absolutely no other text. Do not use the first person ever. Include just the bullet points -- no intro text or other text.",
        ),
    ]
    for prompt in prompts:
        current_value = getattr(commemoration, prompt[0])
        if not current_value or overwrite:
            result, citations = perplexity(prompt[2])
            print("")
            print(f"===={prompt}====")
            print("")
            print(result)
            print(citations)
            print("")
            setattr(commemoration, prompt[0], clean_string(result))
            if prompt[1]:
                setattr(commemoration, prompt[1], citations)
            if prompt[0] == "ai_verse":
                verse, citation = extract_and_remove_parenthetical(result)
                setattr(commemoration, "ai_verse", verse)
                setattr(commemoration, "ai_verse_citation", citation)
            if prompt[0] == "ai_quote":
                quote, author = extract_and_remove_parenthetical(result)
                setattr(commemoration, "ai_quote", quote)
                setattr(commemoration, "ai_quote_by", author)
        commemoration.save()

    both_sources = " Use both the uploaded files and your broader knowledge to provide comprehensive answers. If information is unavailable in the provided files, use external knowledge to fill in the gaps."
    internal_sources = (
        " Use only the uploaded files. If information is unavailable in the provided files, return null."
    )
    external_sources = " Use your broader knowledge only. Do not reference the uploaded files."
    prompts = [
        (
            "ai_martyrology",
            f"Include exact full text of the biography of St. {name} from The Roman Martyrology, if it exists. Include just the biography -- Do not include any additional text, no title, no introduction, no outro, nothing. If it does not exist, return an empty string."
            + internal_sources,
        ),
        (
            "ai_lesser_feasts_and_fasts",
            f"Include exact full text of the biography of {person} from Lesser Feasts and Fasts (2018), if it exists.  DInclude just the biography -- Do not include any additional text, no title, no introduction, no outro, nothing. If it does not exist, return null"
            + internal_sources,
        ),
        (
            "ai_butler",
            f"Include exact full text of the biography of St. {name} from Alban Butler's Complete Life of the Saints, if it exists. Include just the biography -- Do not include any additional text, no title, no introduction, no outro, nothing. If it does not exist, return null"
            + internal_sources,
        ),
    ]
    for prompt in prompts:
        current_value = getattr(commemoration, prompt[0])
        if not current_value or overwrite:
            print(f"===={prompt}====")
            res = chat_with_assistant(prompt[1])
            setattr(commemoration, prompt[0], res)
            commemoration.save()


def run_all_bios(overwrite=False):
    commemorations = Commemoration.objects.filter(calendar__year=2019).all()
    for c in commemorations:
        if hasattr(c, "saint_name") and c.saint_name:
            print(c.name)
            print(c.saint_name)
            go(c, overwrite)


def get_duckduckgo_images(prompt, num_images=2):
    search_url = f"https://duckduckgo.com/i.js?q={prompt}"
    response = requests.get(search_url)
    response.raise_for_status()
    images = response.json()["results"]

    return [img["image"] for img in images[:num_images]]


def google_image_search(query):
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "q": query,
        "cx": settings.GOOGLE_CUSTOM_SEARCH_ENGINE_KEY,  # Custom Search Engine ID
        "key": settings.GOOGLE_API_KEY,  # API Key
        "searchType": "image",  # Image search
        "num": 5,  # Number of results
        "imgSize": "large",  # Ensure images are at least 500px by 500px
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        results = response.json()
        images = [item["link"] for item in results.get("items", [])]
        return images
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

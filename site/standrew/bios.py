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


KNOWLEDGE_FILES = [
    ("BCP2019.pdf", "The Book of Common Prayer (2019)"),
    ("BCP2019Spanish.pdf", "The Book of Common Prayer (2019) (Spanish Language)"),
    ("BCP2019TLE.pdf", "The Book of Common Prayer (2019) (Traditional Language Edition)"),
    ("BookOfHomilies.pdf", "The Two Books of Homilies"),
    ("LesserFeastsAndFasts2018.pdf", "Lesser Feasts and Fasts (2018)"),
    ("LivesOfTheSaints.txt", "Alban Butler's Complete Lives of the Saints"),
    ("RomanMartyrology.pdf", "The Roman Martyrology"),
    ("ToBeAChristianACNACatehcism.pdf", "To Be a Christian: An Anglican Catechism (ACNA)"),
]
VECTOR_STORE_NAME = "ACNA Documents"
ASSISTANT_MODEL = "gpt-4o"


def create_vector_store():
    files = KNOWLEDGE_FILES
    vector_store = openai.vector_stores.create(name=VECTOR_STORE_NAME)

    # Ready the files for upload to OpenAI
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_paths = [f"{dir_path}/data/{path}" for path, title in files]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = openai.vector_stores.file_batches.upload_and_poll(vector_store_id=vector_store.id, files=file_streams)

    # You can print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)
    return vector_store, files


def assistant_instructions(files=KNOWLEDGE_FILES):
    file_titles = ", ".join([f"{file[0]} ({file[1]})" for file in files])
    return f"You are a helpful Anglican theologian, historian, liturgist, and priest dedicated to answering theological questions and consulting authoritative documents from an orthodox Anglican perspective, particularly within the Anglican Church in North America (ACNA). You provide well-researched, clear, and thoughtful responses grounded in Scripture, the Book of Common Prayer (2019), and To Be a Christian: An Anglican Catechism. Consult each of these files {file_titles} in addition to web searches. Your tone is respectful, compassionate, and insightful, reflecting the Anglican tradition's emphasis on faith, reason, and tradition. You prioritizes doctrinal accuracy and integrity, ensuring that it represents Anglican beliefs fairly while acknowledging ecumenical contexts. Upon request, you can assist with writing, editing, and refining hagiographies, theological essays, sermons, and reflections with a scholarly yet pastoral style. You are a knowledgeable AI assistant with access to web search, code execution, DALL·E image generation, and data analysis. Use uploaded PDFs as reference materials when responding as well as web searches. Please both search upload files and use your general knowledge to make a comprehensive response."


def create_custom_assistant():
    # The Assistants API was shut down on 2026-08-26, so there is no assistant object to create.
    # This now only builds the knowledge base; chat_with_assistant() sends the model and instructions itself.
    vector_store, files = create_vector_store()
    print(vector_store)
    return vector_store


def find_vector_store_id(name=VECTOR_STORE_NAME):
    for vector_store in openai.vector_stores.list(limit=100):
        if vector_store.name == name:
            return vector_store.id
    raise RuntimeError(f"No vector store named {name!r}; run create_vector_store() first")


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
def chat_with_assistant(user_input, vector_store_id=None):
    response = openai.responses.create(
        model=ASSISTANT_MODEL,
        instructions=assistant_instructions(),
        input=user_input,
        tools=[
            {"type": "code_interpreter", "container": {"type": "auto"}},
            {"type": "file_search", "vector_store_ids": [vector_store_id or find_vector_store_id()]},
        ],
    )
    if response.status == "completed":
        print(response.output_text)
        return response.output_text

    else:
        print(response.status)
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


def _append_generation_instructions(prompt, instructions):
    if not instructions or not instructions.strip():
        return prompt
    return f"{prompt}\n\nImportant additional instructions (follow carefully): {instructions.strip()}"


def _extract_legend_title(legend_text):
    if not legend_text:
        return ""
    first_line = legend_text.strip().splitlines()[0].strip()
    return clean_string(first_line)


def go_perplexity(commemoration, overwrite=False):
    """Regenerate Perplexity-backed AI fields shown in the frontend."""
    person = commemoration.name
    instructions = getattr(commemoration, "ai_generation_instructions", None) or ""

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
            message = _append_generation_instructions(prompt[2], instructions)
            result, citations = perplexity(message)
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
                setattr(commemoration, "ai_verse", clean_string(verse))
                setattr(commemoration, "ai_verse_citation", clean_string(citation))
            if prompt[0] == "ai_quote":
                quote, author = extract_and_remove_parenthetical(result)
                setattr(commemoration, "ai_quote", clean_string(quote))
                setattr(commemoration, "ai_quote_by", clean_string(author))
            if prompt[0] == "ai_legend":
                setattr(commemoration, "ai_legend_title", _extract_legend_title(result))
        commemoration.save()


def go_openai_sources(commemoration, overwrite=False):
    """Regenerate OpenAI assistant source excerpts (not shown in frontend)."""
    person = commemoration.name
    name = getattr(commemoration, "saint_name", None) or person

    internal_sources = (
        " Use only the uploaded files. If information is unavailable in the provided files, return null."
    )
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


def go(commemoration, overwrite=False):
    go_perplexity(commemoration, overwrite=overwrite)
    go_openai_sources(commemoration, overwrite=overwrite)


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

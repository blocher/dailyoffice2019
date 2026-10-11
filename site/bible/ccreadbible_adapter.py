import re
import urllib.parse

import requests
import scriptures
from bs4 import BeautifulSoup
from html2text import html2text

from bible.sources import BibleSource, PassageNotFoundException

# Mapping from scriptures library book names to ccreadbible.org URL names
BOOK_URL_NAMES = {
    "Genesis": "Genesis",
    "Exodus": "Exodus",
    "Leviticus": "Leviticus",
    "Numbers": "Numbers",
    "Deuteronomy": "Deuteronomy",
    "Joshua": "Joshua",
    "Judges": "Judges",
    "Ruth": "Ruth",
    "I Samuel": "1_Samuel",
    "II Samuel": "2_Samuel",
    "I Kings": "1_Kings",
    "II Kings": "2_Kings",
    "I Chronicles": "1_Chronicles",
    "II Chronicles": "2_Chronicles",
    "Ezra": "Ezra",
    "Nehemiah": "Nehemiah",
    "Esther": "Esther",
    "Job": "Job",
    "Psalms": "Psalms",
    "Proverbs": "Proverbs",
    "Ecclesiastes": "Ecclesiastes",
    "Song of Songs": "Song_of_Songs",
    "Isaiah": "Isaiah",
    "Jeremiah": "Jeremiah",
    "Lamentations": "Lamentations",
    "Ezekiel": "Ezekiel",
    "Daniel": "Daniel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "Matthew": "Matthew",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Romans": "Romans",
    "I Corinthians": "1_Corinthians",
    "II Corinthians": "2_Corinthians",
    "Galatians": "Galatians",
    "Ephesians": "Ephesians",
    "Philippians": "Philippians",
    "Colossians": "Colossians",
    "I Thessalonians": "1_Thessalonians",
    "II Thessalonians": "2_Thessalonians",
    "I Timothy": "1_Timothy",
    "II Timothy": "2_Timothy",
    "Titus": "Titus",
    "Philemon": "Philemon",
    "Hebrews": "Hebrews",
    "James": "James",
    "I Peter": "1_Peter",
    "II Peter": "2_Peter",
    "I John": "1_John",
    "II John": "2_John",
    "III John": "3_John",
    "Jude": "Jude",
    "Revelation": "Revelation",
    # Deuterocanonical
    "Tobit": "Tobit",
    "Judith": "Judith",
    "Wisdom": "Wisdom",
    "Sirach": "Sirach",
    "Baruch": "Baruch",
    "I Maccabees": "1_Maccabees",
    "II Maccabees": "2_Maccabees",
}

BASE_URL = "https://www.ccreadbible.org/chinesebible"


class CCReadBible(BibleSource):
    """Adapter for fetching 思高本 (Studium Biblicum) from ccreadbible.org.

    Supports both traditional (sigao) and simplified (znsigao) Chinese.
    """

    def __init__(self, passage, version="sigao"):
        self.version = version  # "sigao" for traditional, "znsigao" for simplified
        self.passage = passage

        self.passage = self.passage.replace("III ", "3 ")
        self.passage = self.passage.replace("II ", "2 ")
        self.passage = self.passage.replace("I ", "1 ")

        self.references = scriptures.extract(passage)
        if self.references:
            self.reference = self.references[0]
        else:
            self.reference = None

        self.html = self._build_html()
        self.text = self._set_text()

    def get_text(self):
        return self.text

    def get_html(self):
        return self.html

    def get_headings(self):
        return []

    def _get_chapter_html(self, book_url_name, chapter):
        url = f"{BASE_URL}/{self.version}/{book_url_name}_bible_Ch_{chapter}_.html"
        print(url)
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        raise PassageNotFoundException(f"Could not fetch {url}")

    def _extract_verses(self, markup, start_verse, end_verse):
        soup = BeautifulSoup(markup, "html5lib")
        content_div = soup.find("div", id="parent-fieldname-text")
        if not content_div:
            raise PassageNotFoundException("Could not find content div")

        verses = []
        for td in content_div.find_all("td"):
            sup = td.find("sup")
            if not sup:
                continue
            try:
                verse_num = int(sup.get_text().strip())
            except (ValueError, AttributeError):
                continue
            if start_verse <= verse_num <= end_verse:
                verses.append(str(td))

        if not verses:
            raise PassageNotFoundException("No verses found")
        return "\n".join(verses)

    def _build_html(self):
        if not self.reference:
            raise PassageNotFoundException(f"Could not parse passage: {self.passage}")

        book, start_chapter, start_verse, end_chapter, end_verse, testament = self.reference
        book_url_name = BOOK_URL_NAMES.get(book)
        if not book_url_name:
            raise PassageNotFoundException(f"Unknown book: {book}")

        all_verses = []
        for chapter in range(start_chapter, end_chapter + 1):
            markup = self._get_chapter_html(book_url_name, chapter)
            ch_start = start_verse if chapter == start_chapter else 1
            ch_end = end_verse if chapter == end_chapter else 999
            verses_html = self._extract_verses(markup, ch_start, ch_end)
            all_verses.append(verses_html)

        result = "\n".join(all_verses)
        if not result:
            raise PassageNotFoundException
        return result

    def _set_text(self):
        try:
            text = html2text(self.html).replace("\n", " ").replace(r"/\s\s+/", " ").strip()
            text = re.sub(r" +", " ", text)
            return text
        except Exception as e:
            print(e)
            return None

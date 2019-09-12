from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
import scriptures
from html2text import html2text
import re


class BibleSource(ABC):
    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def get_html(self):
        pass

    @abstractmethod
    def get_headings(self):
        pass


class BibleGateway(BibleSource):
    def __init__(self, passage, version="nrsv"):

        self.version = version
        self.reference = scriptures.extract(passage)[0]
        self.passage = scriptures.reference_to_string(*self.reference)
        self.markup = self._get_markup()
        # print(self.markup)
        self.soup = BeautifulSoup(self.markup, "html5lib")
        self.html = self._set_html()
        self.text = self._set_text()
        self.headings = self._set_headings()

    def get_text(self):
        return self.text

    def get_html(self):
        return self.html

    def get_headings(self):
        return self.headings

    def _get_markup(self, passage=None):
        passage = passage if passage else self.passage
        r = requests.get("https://beta.biblegateway.com/passage/?search={}&version={}".format(passage, self.version))
        print("https://beta.biblegateway.com/passage/?search={}&version={}".format(passage, self.version))
        if r.status_code == 200:
            return r.text
        raise Exception("Error getting passage")

    def _set_text(self):
        try:
            str = html2text(self.html).replace("\n", " ").replace("/\s\s+/", " ").strip()
            str = re.sub(" +", " ", str)
            return str
        except Exception as e:
            print(e)
            return None

    def _set_html(self):
        try:
            for h3 in self.soup.find_all("h3"):
                h3.decompose()
            for span in self.soup.find_all("span", class_="chapternum"):
                span.decompose()
            for sup in self.soup.find_all("sup", class_="versenum"):
                sup.decompose()
            for sup in self.soup.find_all("sup", class_="crossreference"):
                sup.decompose()
            for sup in self.soup.find_all("sup", class_="footnote"):
                sup.decompose()
            return " ".join(
                [
                    str(tag)
                    for tag in self.soup.find_all("div", class_="result-text-style-normal")[0].find_all(
                        "span", class_="text"
                    )
                ]
            )
        except Exception as e:
            print(e)
            return None

    def _get_previous_heading(self):

        book, start_chapter, start_verse, end_chapter, end_verse = self.reference

        new_start_chapter = 1 if start_chapter == 1 else start_chapter - 1
        new_start_verse = 1
        new_end_chapter = start_chapter
        new_end_verse = start_verse

        passage = "{} {}:{} - {}:{}".format(book, new_start_chapter, new_start_verse, new_end_chapter, new_end_verse)
        markup = self._get_markup(passage)
        soup = BeautifulSoup(markup, "html5lib")
        headings = soup.find_all("div", class_="result-text-style-normal")[0].find_all("h3")
        if headings:
            return headings.pop()
        return None

    def _set_headings(self):

        try:
            headings = self.soup.find_all("div", class_="result-text-style-normal")[0].find_all("h3")

            first_element = self.soup.find_all("div", class_="result-text-style-normal")[0].find_all()[0]
            if first_element.name != "h3":
                new_heading = self._get_previous_heading()
                if new_heading:
                    headings = [new_heading] + headings

            formatted_headings = []
            for heading in headings:
                span = heading.find_next("span")
                classes = span.get_attribute_list("class")
                try:
                    classes.remove("text")
                except ValueError:
                    pass
                passage = classes[0].split("-")
                passage = "{} {}:{}".format(passage[0], passage[1], passage[2])
                passage = scriptures.extract(passage)[0]
                passage = scriptures.reference_to_string(*passage)
                formatted_headings.append((passage, heading.string))

            return formatted_headings
        except Exception as e:
            print(e)
            return None

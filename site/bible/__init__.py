from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
import scriptures


class PassageRetriever(object):

    pass


class BibleVersion(ABC):
    @abstractmethod
    def getPassageText(self):
        pass

    @abstractmethod
    def getPassageHTML(self):
        pass

    @abstractmethod
    def getPassageHeadings(self):
        pass


class NRSV(BibleVersion):
    def __init__(self, passage):
        self.passage_reference = scriptures.extract(passage)[0]
        self.passage = scriptures.reference_to_string(*self.passage_reference)
        self.markup = self.getPassage()
        self.soup = BeautifulSoup(self.markup, "html5lib")

    def getPassage(self, passage=None):
        passage = passage if passage else self.passage
        r = requests.get("https://beta.biblegateway.com/passage/?search={}&version=NRSV".format(passage))
        if r.status_code == 200:
            return r.text
        raise Exception("Error getting passage")

    def getPassageText(self):
        pass

    def getPassageHTML(self):
        main_sections = self.soup.find_all("div", class_="result-text-style-normal")
        for section in main_sections:
            print(section)

    def getPassageHeadings(self):

        headings = self.soup.find_all("div", class_="result-text-style-normal")[0].find_all("h3")
        headings = [heading.string for heading in headings]

        first_element = self.soup.find_all("div", class_="result-text-style-normal")[0].find_all()[0]
        if first_element.name != "h3":
            chapter = 1 if self.passage_reference[1] == 1 else self.passage_reference[1] - 1
            extended_passage = "{} {}:1 - {}:{}".format(
                self.passage_reference[0], chapter, self.passage_reference[3], self.passage_reference[4]
            )
            extended_markup = self.getPassage(extended_passage)
            extended_soup = BeautifulSoup(extended_markup, "html5lib")
            extended_headings = extended_soup.find_all("div", class_="result-text-style-normal")[0].find_all("h3")
            extended_headings = [heading.string for heading in extended_headings]
            original_headings = set(headings)
            new_headings = [item for item in extended_headings if item not in original_headings]
            headings = [new_headings.pop()] + headings

        return headings

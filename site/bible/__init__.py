from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests


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
        self.passage = passage
        self.markup = self.getPassage()
        self.soup = BeautifulSoup(self.markup, "html5lib")

    def getPassage(self):
        r = requests.get("https://beta.biblegateway.com/passage/?search={}&version=NRSV".format(self.passage))
        if r.status_code == 200:
            self.passage = r.text
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
        if first_element.name != 'h3':


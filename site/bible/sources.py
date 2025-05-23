import re
from abc import ABC, abstractmethod

import requests
import scriptures
from bs4 import BeautifulSoup
from html2text import html2text

from psalter.utils import get_psalms


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


class PassageNotFoundException(BaseException):
    pass


class BibleGateway(BibleSource):
    def __init__(self, passage, version="nrsv"):
        self.version = version
        if self.version == "kjv":
            self.version = "akjv"
        # try:
        self.reference = scriptures.extract(passage)[0]
        self.passage = scriptures.reference_to_string(*self.reference)
        self.passage = self.passage.replace("III ", "3 ")
        self.passage = self.passage.replace("II ", "2 ")
        self.passage = self.passage.replace("I ", "1 ")

        # except Exception as e:
        #     print(e)
        #     self.text = ""
        #     self.html = ""
        #     self.headings = []
        #     return
        self.markup = self._get_markup()

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
        r = requests.get("https://biblegateway.com/passage/?search={}&version={}".format(passage, self.version))
        print("https://biblegateway.com/passage/?search={}&version={}".format(passage, self.version))
        print(r)
        if r.status_code == 200:
            return r.text
        raise Exception("Error getting passage")

    def _set_text(self):
        try:
            str = html2text(self.html).replace("\n", " ").replace(r"/\s\s+/", " ").strip()
            str = re.sub(r" +", " ", str)
            return str
        except Exception as e:
            print(e)
            return None

    def _set_html(self):
        try:
            for sup in self.soup.find_all("sup", class_="crossreference"):
                sup.decompose()
            for sup in self.soup.find_all("sup", class_="footnote"):
                sup.decompose()
            for div in self.soup.find_all("div", class_="footnotes"):
                div.decompose()
            for div in self.soup.find_all("div", class_="crossrefs"):
                div.decompose()
            for div in self.soup.find_all("div", class_="publisher-info-bottom"):
                div.decompose()
            for a in self.soup.find_all("a", class_="full-chap-link"):
                a.decompose()
            for a in self.soup.find_all("div", class_="passage-other-trans"):
                a.decompose()

            result = " ".join([str(tag) for tag in self.soup.find_all("div", class_="passage-text")[0]])
            print(self.version)
            if self.version.lower() in ["kjv", "akjv"]:
                result = result.replace("<i>", "").replace("</i>", "")
            if self.version.lower() == "esv":
                result = result.replace("[The earliest manuscripts do not include 7:53–8:11.]", "")
                result = result.replace("[Some of the earliest manuscripts do not include 16:9–20.]", "")
                result = result.replace("[[", "").replace("]]", "")
            if not result:
                raise PassageNotFoundException
            return result
        except Exception as e:
            raise PassageNotFoundException

    def _get_previous_heading(self):
        book, start_chapter, start_verse, end_chapter, end_verse, testament = self.reference

        new_start_chapter = 1 if start_chapter == 1 else start_chapter - 1
        new_start_verse = 1
        new_end_chapter = start_chapter
        new_end_verse = start_verse

        passage = "{} {}:{}-{}:{}".format(book, new_start_chapter, new_start_verse, new_end_chapter, new_end_verse)
        markup = self._get_markup(passage)
        soup = BeautifulSoup(markup, "html5lib")
        headings = soup.find_all("div", class_="result-text-style-normal")[0].find_all("h3")
        if headings:
            return headings.pop()
        return None

    def _set_headings(self):
        # try:
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
        # except Exception as e:
        #     print(e)
        #     return None


class OremusBibleBrowser(BibleSource):
    def __init__(self, passage, version="av"):
        self.version = version

        self.reference = scriptures.extract(passage)[0]
        self.passage = scriptures.reference_to_string(*self.reference)
        self.passage = self.passage.replace("III ", "3 ")
        self.passage = self.passage.replace("II ", "2 ")
        self.passage = self.passage.replace("I ", "1 ")

        self.markup = self._get_markup()
        self.soup = BeautifulSoup(self.markup, "html5lib")
        self.html = self._set_html()
        self.text = self._set_text()
        self.headings = self._set_headings()

    def get_text(self):
        return self.text

    def get_html(self):
        return self.html

    def get_headings(self):
        return []
        return self.headings

    def _get_markup(self, passage=None):
        passage = passage if passage else self.passage
        url = f"http://bible.oremus.org/?version={self.version}&passage={passage}&vnum=YES&fnote=NO&show_ref=NO&headings=YES&omithidden=YES"
        print(url)
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        raise Exception("Error getting passage")

    def _set_text(self):
        try:
            str = html2text(self.html).replace("\n", " ").replace(r"/\s\s+/", " ").strip()
            str = re.sub(r" +", " ", str)
            return str
        except Exception as e:
            print(e)
            return None

    def _set_html(self):
        try:
            result = " ".join([str(tag) for tag in self.soup.find_all("div", class_="bibletext")[0]])
            result = result.replace("</sup>", "&nbsp;</sup>")
            result = result.replace("\n", "").replace("\r", "")
            result = result.replace('<br/><sup class="ww vnumVis">', " <sup>")
            if not result:
                raise PassageNotFoundException
            return result
        except Exception as e:
            raise PassageNotFoundException

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
        pass


class BCPPsalter(BibleSource):
    def __init__(self, passage, version="renewed_coveraale"):
        self.version = version

        # self.reference = scriptures.extract(passage)[0]
        # self.passage = scriptures.reference_to_string(*self.reference)
        self.passage = passage
        self.html = self.get_markup()
        self.text = self._set_text()
        print(self.html)

    def get_html(self):
        return self.html

    def get_text(self):
        return self.text

    def get_headings(self):
        return []

    def get_markup(self, passage=None):
        passage = passage if passage else self.passage
        if "Psalms" not in passage:
            return "-"
        passage = passage.replace("Psalms", "").strip()
        if self.version == "renewed_coverdale":
            return get_psalms(passage, simplified_citations=True, headings="none")
        elif self.version == "coverdale":
            return get_psalms(passage, language_style="traditional", simplified_citations=True, headings="none")
        return "-"

    def _set_text(self):
        try:
            str = html2text(self.html).replace("\n", " ").replace(r"/\s\s+/", " ").strip()
            str = re.sub(r" +", " ", str)
            return str
        except Exception as e:
            print(e)
            return None

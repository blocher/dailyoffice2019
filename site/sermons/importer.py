import mimetypes
import zipfile

import datefinder
import pke
import scriptures
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.utils import get_stop_words

from bible.passage import Passage
from sermons.models import SermonBiblePassage, SermonLocation, Sermon
from sermons.text_extractor import FileTypeNotSupportedException
from sermons.text_extractor import TextExtractorFactory


class SermonImporter(object):
    @staticmethod
    def import_zip_archive(file):
        archive = zipfile.ZipFile(file)
        for name in archive.namelist():
            print(name)
            try:
                file = archive.open(name)
                if not hasattr(file, "content_type"):
                    file.content_type = mimetypes.MimeTypes().guess_type(name)[0]
                SermonImporter.import_file(file)
            except FileTypeNotSupportedException:
                print("File type not supported")

    @staticmethod
    def import_file(file):
        if hasattr(file, "content_type") and file.content_type == "application/zip":
            return SermonImporter.import_zip_archive(file)
        text_extractor = TextExtractorFactory.get_extractor(file)
        sermon_extractor = SermonExtractor(text_extractor)
        sermon = Sermon()
        # sermon.file = file
        sermon.title = sermon_extractor.getTitle()
        sermon.content = sermon_extractor.getContent()
        sermon.text = sermon_extractor.getText(file)
        sermon.auto_summary = sermon_extractor.getSummary()
        sermon.location = sermon_extractor.getLocation()
        sermon.primary_date_and_time_given = sermon_extractor.getDate()
        sermon_extractor.getKeyWords()

        sermon.save()
        sermon_extractor.getBiblePassages(sermon)

        return sermon


class SermonExtractor(object):
    def __init__(self, extractor):
        self.extractor = extractor

    def getTitle(self):
        name = self.extractor.file_name()
        name = name.split(".")
        if len(name) > 1:
            name.pop()
        name = ".".join(name)
        name = name.replace("_", " ")
        name = name.split("-")
        if len(name) > 1:
            return name.pop().strip()
        return name[0].strip()

    def getContent(self):
        return self.extractor.html()

    def getText(self, file):
        return self.extractor.text()

    # TODO: Scripture paassages on same line
    def getBiblePassages(self, sermon):

        text = self.extractor.text()
        lines = text.splitlines()
        i = 0
        for line in lines:
            passages = scriptures.extract(line)

            if passages:
                if i < 4:
                    i = i + 1
                    book = passages[0][0]
                    segments = []
                    texts = []
                    for passage in passages:
                        texts.append(Passage(scriptures.reference_to_string(*passage)).text)
                        segments.append("{}:{}-{}:{}".format(passage[1], passage[2], passage[3], passage[4]))
                    texts = list(filter(lambda x: x is not None, texts))
                    text = " ".join(texts)
                    segments = " ".join(segments)
                    quote = "{} {}".format(book, segments)
                    book = book.lower()
                    if book in ["psalms"]:
                        book_type = SermonBiblePassage.PSALM
                    elif book in ["matthew", "mark", "luke", "john"]:
                        book_type = SermonBiblePassage.GOSPEL
                    elif book in [
                        "acts",
                        "romans",
                        "1 corinthians",
                        "2 corinthians",
                        "galatians",
                        "ephesians",
                        "philippians",
                        "colossians",
                        "1 thessalonians",
                        "2 thessalonians",
                        "1 timothy",
                        "2 timothy",
                        "titus",
                        "philemon",
                        "hebrews",
                        "james",
                        "1 peter",
                        "2 peter",
                        "1 john",
                        "2 john",
                        "3 john",
                        "jude",
                        "revelation",
                    ]:
                        book_type = SermonBiblePassage.EPISTLE
                    else:
                        book_type = SermonBiblePassage.PROPHECY
                    SermonBiblePassage.objects.create(
                        type=book_type, text=text, html=text, passage=quote, version="nrsv", sermon=sermon
                    )

    def getSummary(self):

        LANGUAGE = "english"
        SENTENCES_COUNT = 5

        parser = PlaintextParser.from_string(self.extractor.text(), Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)

        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summary = ""
        for sentence in summarizer(parser.document, SENTENCES_COUNT):
            summary = "{} {}".format(summary, sentence)
        return summary

    def getLocation(self):
        locations = SermonLocation.objects.all()
        search_strings = {}
        for location in locations:
            search_strings = {**search_strings, **location.search_strings}
        text = self.extractor.text().replace(",", "")
        for search_string, location in search_strings.items():
            if search_string in text:
                return location
        return None

    def getKeyWords(self):

        # initialize keyphrase extraction model, here TopicRank
        extractor = pke.unsupervised.KPMiner()

        # load the content of the document, here document is expected to be in raw
        # format (i.e. a simple text file) and preprocessing is carried out using spacy

        extractor.load_document(input=self.extractor, language="en")

        # keyphrase candidate selection, in the case of TopicRank: sequences of nouns
        # and adjectives (i.e. `(Noun|Adj)*`)
        extractor.candidate_selection()

        # candidate weighting, in the case of TopicRank: using a random walk algorithm
        extractor.candidate_weighting()

        # N-best selection, keyphrases contains the 10 highest scored candidates as
        # (keyphrase, score) tuples
        keyphrases = extractor.get_n_best(n=10)
        print(keyphrases)

    def getDate(self):

        matches = list(datefinder.find_dates(self.extractor.text()))
        if len(matches) > 0:
            if matches[0].hour == 0:
                matches[0] = matches[0].replace(hour=10, minute=0, second=0, microsecond=0)
            return matches[0]

        return None

        # sermon.save()
        #
        # if sermon.primary_date_and_time_given:
        #     SermonDateTime.objects.create(
        #         sermon_id=sermon.pk, date_and_time_given=sermon.primary_date_and_time_given, primary=True
        #     )

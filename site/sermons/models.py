from django.db import models
from website.models import UUIDModel
import mammoth
from rake_nltk import Rake

from taggit.managers import TaggableManager
import docx
import sumy
from djrichtextfield.models import RichTextField


class Sermon(UUIDModel):
    title = models.CharField(max_length=255, verbose_name="Sermon title", help_text="Sermon Title")
    location = models.CharField(max_length=255, verbose_name="Location", help_text="Location Sermon was delivered")
    file = models.FileField(
        verbose_name="File", help_text="The sermon in Microsoft Word or text format", blank=True, null=True
    )
    text = models.TextField(verbose_name="Text", help_text="The full content of the sermon", blank=True, null=True)
    content = RichTextField(
        verbose_name="Formatted Content", help_text="The formatted content of the sermon", blank=True, null=True
    )
    summary = models.TextField(verbose_name="Summary", help_text="A summary of the sermon", blank=True, null=True)
    auto_summary = models.TextField(
        verbose_name="Auto-summary", help_text="An auto-generated summary of the sermon", blank=True, null=True
    )
    notes = models.TextField(verbose_name="Notes", help_text="Publicly displayed Notes", blank=True, null=True)
    private_notes = models.TextField(
        verbose_name="Notes (private)", help_text="Notes (Internal only)", blank=True, null=True
    )
    primary_date_and_time_given = models.DateTimeField(
        verbose_name="Date and Time Given",
        help_text="The primary date given (used for sorting).  More than one date and time can be added on the date and time tab",
        null=True,
        blank=True,
    )

    # tags = TaggableManager()

    def getContent(self, file):
        result = mammoth.convert_to_html(file)
        html = result.value
        messages = result.messages
        print(messages)
        return html

    def getText(self, file):
        result = mammoth.extract_raw_text(file)
        html = result.value
        messages = result.messages
        print(messages)
        return html

    def getSummary(self):

        from sumy.parsers.html import HtmlParser
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer as Summarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words

        LANGUAGE = "english"
        SENTENCES_COUNT = 5

        url = "https://en.wikipedia.org/wiki/Automatic_summarization"
        parser = HtmlParser.from_url(url, Tokenizer(LANGUAGE))
        # or for plain text files
        parser = PlaintextParser.from_string(self.text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)

        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summary = ""
        for sentence in summarizer(parser.document, SENTENCES_COUNT):
            summary = "{} {}".format(summary, sentence)
        return summary

    def getKeyWords(self):
        import pke

        # initialize keyphrase extraction model, here TopicRank
        extractor = pke.unsupervised.TfIdf()

        # load the content of the document, here document is expected to be in raw
        # format (i.e. a simple text file) and preprocessing is carried out using spacy
        extractor.load_document(input=self.text, language="en")

        # keyphrase candidate selection, in the case of TopicRank: sequences of nouns
        # and adjectives (i.e. `(Noun|Adj)*`)
        extractor.candidate_selection()

        # candidate weighting, in the case of TopicRank: using a random walk algorithm
        extractor.candidate_weighting()

        # N-best selection, keyphrases contains the 10 highest scored candidates as
        # (keyphrase, score) tuples
        keyphrases = extractor.get_n_best(n=10)
        print(keyphrases)

    def save(self, *args, **kwargs):
        if self.file:
            self.content = self.getContent(self.file)
            self.text = self.getText(self.file)
        self.auto_summary = self.getSummary()
        self.getKeyWords()
        return super().save(*args, **kwargs)


class SermonDateTime(UUIDModel):

    date_and_time_given = models.DateTimeField(verbose_name="Date Given", help_text="Date and Time Given", null=False)
    sermon = models.ForeignKey("Sermon", verbose_name="Sermon", on_delete=models.CASCADE, null=False)
    primary = models.BooleanField(
        verbose_name="Primray Service",
        help_text="Should this date be the primary date used for sorting?",
        default=False,
    )

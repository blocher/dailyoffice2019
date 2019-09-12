import io
from abc import ABC, abstractmethod

import mammoth
from pdfminer3.converter import TextConverter, HTMLConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.pdfpage import PDFPage

import mimetypes


class FileTypeNotSupportedException(Exception):
    pass


class TextExtractorFactory(object):
    @staticmethod
    def get_extractor(file):

        if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return WordXExtractor(file)

        if file.content_type == "application/pdf":
            return PDFExtractor(file)

        if file.content_type == "x-pdf":
            return PDFExtractor(file)

        raise FileTypeNotSupportedException("This file type is not yet implemented.")


class TextExtractor(ABC):
    def __init__(self, file):
        self.file = file
        self.file_name_cache = ""
        self.text_cache = ""
        self.html_cache = ""

    def set_file_name(self):
        return self.file.name

    @abstractmethod
    def set_text(self):
        pass

    @abstractmethod
    def set_html(self):
        pass

    def file_name(self):
        if not self.file_name_cache:
            self.file_name_cache = self.set_file_name()
        return self.file_name_cache

    def text(self):
        if not self.text_cache:
            self.text_cache = self.set_text()
        return self.text_cache

    def html(self):
        if not self.html_cache:
            self.html_cache = self.set_html()
        return self.html_cache


class WordXExtractor(TextExtractor):
    def set_text(self):
        return mammoth.extract_raw_text(self.file).value

    def set_html(self):
        return mammoth.convert_to_html(self.file).value


class PDFExtractor(TextExtractor):
    def _extract(self, convertor_class=TextConverter):
        rsrcmgr = PDFResourceManager()
        retstr = io.BytesIO()
        codec = "utf-8"
        laparams = LAParams()
        if convertor_class == HTMLConverter:
            device = convertor_class(rsrcmgr, retstr, codec=codec, laparams=laparams, showpageno=False, pagemargin=0)
        if convertor_class == TextConverter:
            device = convertor_class(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(
            self.file, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True
        ):
            interpreter.process_page(page)

        text = retstr.getvalue()

        device.close()
        retstr.close()
        return text.decode()

    def set_text(self):
        return self._extract()

    def set_html(self):
        return self._extract(convertor_class=HTMLConverter)

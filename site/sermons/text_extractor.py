from abc import ABC, abstractmethod

import mammoth
import magic
import PyPDF2
import io

from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter, HTMLConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage


class TextExtractor(ABC):
    def __init__(self, file):
        self.file = file

    def file_name(self):
        return self.file.name

    @abstractmethod
    def text(self):
        pass

    @abstractmethod
    def html(self):
        pass

    @staticmethod
    def get_extractor(file):

        if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return WordXExtractor(file)

        if file.content_type == "application/pdf":
            return PDFExtractor(file)

        if file.content_type == "x-pdf":
            return PDFExtractor(file)

        raise Exception("This file type is not yet implemented.")


class WordXExtractor(TextExtractor):
    def text(self):
        return mammoth.extract_raw_text(self.file).value

    def html(self):
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

    def text(self):
        return self._extract()

    def html(self):
        return self._extract(convertor_class=HTMLConverter)

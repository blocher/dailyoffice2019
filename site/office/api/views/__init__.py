from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.api.line import Line, file_to_lines
from office.api.translations import translate as _translate_text, is_chinese
from office.utils import chinese_books, spanish_books
from office.utils import generate_uuid_from_string


class Module(object):
    def __init__(self, office=None):
        self.office = office

    @property
    def language(self):
        """Get the display language from office settings."""
        if self.office and hasattr(self.office, "settings"):
            return self.office.settings.get("display_language", "english")
        return "english"

    # Default Bible translations for each display language
    LANGUAGE_BIBLE_DEFAULTS = {
        "chinese-traditional": "cuv",
        "chinese-simplified": "cuvs",
        "spanish": "nvi",
    }

    @property
    def bible_translation(self):
        """Get the Bible translation, auto-selecting based on display language if appropriate."""
        if not self.office or not hasattr(self.office, "settings"):
            return "esv"
        configured = self.office.settings.get("bible_translation", "esv")
        lang = self.language
        # If display language is non-English and the bible_translation is still an English one,
        # auto-switch to the default for that language
        if lang in self.LANGUAGE_BIBLE_DEFAULTS:
            english_translations = {"esv", "kjv", "rsv", "nrsvce", "nabre", "niv", "nasb", "coverdale", "renewed_coverdale"}
            if configured in english_translations:
                return self.LANGUAGE_BIBLE_DEFAULTS[lang]
        return configured

    def t(self, text):
        """Translate a string based on the current display language."""
        return _translate_text(text, self.language)

    def load_lines(self, filename):
        """Load lines from a CSV file, using the appropriate language version."""
        return file_to_lines(filename, self.language)

    def _ftl(self, filename):
        """Shorthand for load_lines - loads CSV with language support."""
        return self.load_lines(filename)

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def get_safe_name(self):
        return "".join(filter(str.isalpha, self.get_name().replace(" ", "_").lower()))

    @staticmethod
    def _translate_citation(citation, lang):
        """Translate Bible book names in citations like 'DANIEL 9:9' or '2 CORINTHIANS 13:14'."""
        if lang in ("chinese-traditional", "chinese-simplified"):
            book_map = chinese_books
        elif lang == "spanish":
            book_map = spanish_books
        else:
            return citation
        # Normalize numeric prefixes: "1 " -> "I ", "2 " -> "II ", "3 " -> "III "
        normalized = citation
        for num, roman in [("3 ", "III "), ("2 ", "II "), ("1 ", "I ")]:
            if normalized.startswith(num):
                normalized = roman + normalized[len(num):]
                break
        # Try to match book name (handles "I SAMUEL", "SONG OF SOLOMON", etc.)
        for eng_name, translated in book_map.items():
            upper_name = eng_name.upper()
            if normalized.upper().startswith(upper_name):
                rest = normalized[len(eng_name):]
                return translated + rest
        return citation

    def strip_line(self, line):
        line["content"] = line["content"].strip()
        line["line_type"] = line["line_type"].strip()
        return line

    def translate_line(self, line):
        """Translate a line's content if the display language is non-English."""
        if not isinstance(line, dict):
            return line
        lang = self.language
        if lang == "english":
            return line
        line_type = line.get("line_type", "")
        content = line.get("content", "")
        # Translate headings, subheadings, rubrics, dialogues, and short responses
        if line_type in ("heading", "rubric", "leader_dialogue",
                         "congregation_dialogue") or content in ("Amen.", "Amen"):
            line["content"] = _translate_text(content, lang)
        elif line_type == "subheading":
            translated = _translate_text(content, lang)
            # If not in translation dict, try translating as a citation (book name)
            if translated == content:
                translated = self._translate_citation(content, lang)
            line["content"] = translated
        # Translate Bible citation references (e.g. "DANIEL 9:9" -> "但以理書 9:9")
        elif line_type == "citation" and content:
            line["content"] = self._translate_citation(content, lang)
        # Also translate other line types if a known translation exists
        elif line_type in ("reader", "congregation", "leader") and content:
            translated = _translate_text(content, lang)
            if translated != content:
                line["content"] = translated
        return line

    def get_formatted_lines(self):
        i = 0
        lines = self.get_lines()
        if not lines:
            return lines
        lines = [self.strip_line(line) for line in lines]
        lines = [
            line
            for line in lines
            if line and (line.get("content") or (line.get("line_type") and line["line_type"] == "spacer"))
        ]
        lines = [self.translate_line(line) for line in lines]
        lines = [self.mark_html_safe(line) for line in lines]
        for line in lines:
            line["audio_id"] = generate_uuid_from_string(line["content"])
            line["id"] = f"{self.get_safe_name()}_{i}_{line['audio_id']}"
            i = i + 1
        return lines

    def get_lines(self):
        raise NotImplementedError("You must implement this method.")

    @staticmethod
    def mark_html_safe(line):
        if not isinstance(line, dict):
            return line
        if line.get("line_type") == "html":
            line["content"] = mark_safe(line["content"])
        return line

    @cached_property
    def json(self):
        lines = self.get_formatted_lines()
        return {"name": self.get_name(), "lines": lines}

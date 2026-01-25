"""
ESV XML Adapter - Reads ESV scripture from XML files and converts to HTML

This module provides functionality to:
1. Parse ESV XML files to extract scripture passages
2. Convert XML elements to beautifully formatted HTML similar to esv.org
3. Handle all book types including Apocrypha
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

import scriptures

from bible.sources import BibleSource, PassageNotFoundException


class ESVXMLAdapter(BibleSource):
    """
    Adapter for reading ESV scripture passages from XML files.

    The XML files are structured with namespaces and use specific elements
    for verses, headings, paragraphs, poetry, quotations, and more.
    """

    # XML namespace used in ESV files
    NAMESPACE = {"cb": "http://www.crosswaybibles.org"}

    # Path to ESV XML files
    ESV_DIR = Path(__file__).parent / "esv"

    # Mapping of normalized book names to XML file names
    # This handles variations in book naming
    BOOK_NAME_MAP = {
        # Old Testament
        "Genesis": "Genesis.xml",
        "Exodus": "Exodus.xml",
        "Leviticus": "Leviticus.xml",
        "Numbers": "Numbers.xml",
        "Deuteronomy": "Deuteronomy.xml",
        "Joshua": "Joshua.xml",
        "Judges": "Judges.xml",
        "Ruth": "Ruth.xml",
        "1 Samuel": "1 Samuel.xml",
        "2 Samuel": "2 Samuel.xml",
        "1 Kings": "1 Kings.xml",
        "2 Kings": "2 Kings.xml",
        "1 Chronicles": "1 Chronicles.xml",
        "2 Chronicles": "2 Chronicles.xml",
        "Ezra": "Ezra.xml",
        "Nehemiah": "Nehemiah.xml",
        "Esther": "Esther.xml",
        "Job": "Job.xml",
        "Psalms": "Psalms.xml",
        "Psalm": "Psalms.xml",  # Singular form
        "Proverbs": "Proverbs.xml",
        "Ecclesiastes": "Ecclesiastes.xml",
        "Song of Solomon": "Song of Solomon.xml",
        "Song of Songs": "Song of Solomon.xml",  # Alternative name
        "Isaiah": "Isaiah.xml",
        "Jeremiah": "Jeremiah.xml",
        "Lamentations": "Lamentations.xml",
        "Ezekiel": "Ezekiel.xml",
        "Daniel": "Daniel.xml",
        "Hosea": "Hosea.xml",
        "Joel": "Joel.xml",
        "Amos": "Amos.xml",
        "Obadiah": "Obadiah.xml",
        "Jonah": "Jonah.xml",
        "Micah": "Micah.xml",
        "Nahum": "Nahum.xml",
        "Habakkuk": "Habakkuk.xml",
        "Zephaniah": "Zephaniah.xml",
        "Haggai": "Haggai.xml",
        "Zechariah": "Zechariah.xml",
        "Malachi": "Malachi.xml",
        # New Testament
        "Matthew": "Matthew.xml",
        "Mark": "Mark.xml",
        "Luke": "Luke.xml",
        "John": "John.xml",
        "Acts": "Acts.xml",
        "Romans": "Romans.xml",
        "1 Corinthians": "1 Corinthians.xml",
        "2 Corinthians": "2 Corinthians.xml",
        "Galatians": "Galatians.xml",
        "Ephesians": "Ephesians.xml",
        "Philippians": "Philippians.xml",
        "Colossians": "Colossians.xml",
        "1 Thessalonians": "1 Thessalonians.xml",
        "2 Thessalonians": "2 Thessalonians.xml",
        "1 Timothy": "1 Timothy.xml",
        "2 Timothy": "2 Timothy.xml",
        "Titus": "Titus.xml",
        "Philemon": "Philemon.xml",
        "Hebrews": "Hebrews.xml",
        "James": "James.xml",
        "1 Peter": "1 Peter.xml",
        "2 Peter": "2 Peter.xml",
        "1 John": "1 John.xml",
        "2 John": "2 John.xml",
        "3 John": "3 John.xml",
        "Jude": "Jude.xml",
        "Revelation": "Revelation.xml",
        # Apocrypha (with numbered prefixes in filenames)
        "Tobit": "70.Tobit.xml",
        "Judith": "71.Judith.xml",
        "Esther (Greek)": "72.Esther.xml",
        "Wisdom": "73.Wisdom of Solomon.xml",
        "Wisdom of Solomon": "73.Wisdom of Solomon.xml",
        "Sirach": "74.Sirach.xml",
        "Ecclesiasticus": "74.Sirach.xml",  # Alternative name
        "Baruch": "75.Baruch.xml",
        "Letter of Jeremiah": "76.Letter of Jeremiah.xml",
        "Prayer of Azariah": "77.Prayer of Azariah.xml",
        "Susanna": "78.Susanna.xml",
        "Bel and the Dragon": "79.Bel and the Dragon.xml",
        "1 Maccabees": "80.1 Maccabees.xml",
        "2 Maccabees": "81.2 Maccabees.xml",
        "1 Esdras": "82.1 Esdras.xml",
        "Prayer of Manasseh": "83.Prayer of Manasseh.xml",
        "Psalm 151": "84.Psalm 151.xml",
        "3 Maccabees": "85.3 Maccabees.xml",
        "2 Esdras": "86.2 Esdras.xml",
        "4 Maccabees": "87.4 Maccabees.xml",
    }

    def __init__(self, passage: str, version: str = "esv"):
        """
        Initialize the adapter with a passage citation.

        Args:
            passage: Scripture passage citation (e.g., "Genesis 1:1-5", "John 3:16")
            version: Translation version (should be "esv")
        """
        self.version = version.lower()
        self.original_passage = passage

        # Normalize the passage using scriptures library
        try:
            self.reference = scriptures.extract(passage)[0]
            self.book, self.start_chapter, self.start_verse, self.end_chapter, self.end_verse, _ = self.reference
            self.passage = scriptures.reference_to_string(*self.reference)
        except (IndexError, AttributeError):
            # If scriptures library can't parse it, try manual parsing
            self.passage = passage
            self._parse_passage_manually()

        # Generate the HTML
        self.html = self._generate_html()
        self.text = self._generate_text()
        self.headings = self._extract_headings()

    def _parse_passage_manually(self):
        """
        Manually parse passage when scriptures library fails (e.g., for Apocrypha).
        """
        # Try to extract book, chapter, and verses
        match = re.match(r"^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$", self.passage)
        if match:
            self.book = match.group(1).strip()
            self.start_chapter = int(match.group(2))
            self.start_verse = int(match.group(3))
            self.end_chapter = self.start_chapter
            self.end_verse = int(match.group(4)) if match.group(4) else self.start_verse
        else:
            # Try chapter range format
            match = re.match(r"^(.+?)\s+(\d+):(\d+)-(\d+):(\d+)$", self.passage)
            if match:
                self.book = match.group(1).strip()
                self.start_chapter = int(match.group(2))
                self.start_verse = int(match.group(3))
                self.end_chapter = int(match.group(4))
                self.end_verse = int(match.group(5))
            else:
                # Default to whole chapter if format doesn't match
                match = re.match(r"^(.+?)\s+(\d+)$", self.passage)
                if match:
                    self.book = match.group(1).strip()
                    self.start_chapter = int(match.group(2))
                    self.start_verse = 1
                    self.end_chapter = self.start_chapter
                    self.end_verse = 999  # Will be limited by actual verses
                else:
                    raise PassageNotFoundException(f"Could not parse passage: {self.passage}")

    def get_text(self) -> str:
        """Return plain text version of the passage."""
        return self.text

    def get_html(self) -> str:
        """Return HTML formatted version of the passage."""
        return self.html

    def get_headings(self) -> list:
        """Return list of headings in the passage."""
        return self.headings

    def _get_xml_filename(self) -> str:
        """
        Get the XML filename for the given book.

        Returns:
            Filename of the XML file

        Raises:
            PassageNotFoundException: If book is not found
        """
        # Try direct lookup
        if self.book in self.BOOK_NAME_MAP:
            return self.BOOK_NAME_MAP[self.book]

        # Try case-insensitive lookup
        for key, value in self.BOOK_NAME_MAP.items():
            if key.lower() == self.book.lower():
                return value

        raise PassageNotFoundException(f"Book not found: {self.book}")

    def _load_xml_tree(self) -> ET.Element:
        """
        Load and parse the XML file for the book.

        Returns:
            Root element of the parsed XML tree

        Raises:
            PassageNotFoundException: If file cannot be loaded
        """
        filename = self._get_xml_filename()
        filepath = self.ESV_DIR / filename

        if not filepath.exists():
            raise PassageNotFoundException(f"XML file not found: {filepath}")

        try:
            # Parse with lxml to handle entities defined in DTD
            from lxml import etree

            parser = etree.XMLParser(load_dtd=True, resolve_entities=True)
            tree = etree.parse(str(filepath), parser)
            return tree.getroot()
        except ImportError:
            # Fallback to standard library (may not handle entities properly)
            tree = ET.parse(filepath)
            return tree.getroot()

    def _generate_html(self) -> str:
        """
        Generate HTML from the XML file for the requested passage.

        Returns:
            HTML string of the formatted passage
        """
        try:
            root = self._load_xml_tree()

            # Build HTML from verses in the range
            html_parts = []

            # Process each chapter in range
            for chapter_num in range(self.start_chapter, self.end_chapter + 1):
                # Determine verse range for this chapter
                verse_start = self.start_verse if chapter_num == self.start_chapter else 1
                verse_end = self.end_verse if chapter_num == self.end_chapter else 999

                chapter_html = self._process_chapter(root, chapter_num, verse_start, verse_end)
                if chapter_html:
                    html_parts.append(chapter_html)

            if not html_parts:
                raise PassageNotFoundException(f"No verses found for passage: {self.passage}")

            return "\n".join(html_parts)

        except Exception as e:
            raise PassageNotFoundException(f"Error generating HTML: {str(e)}")

    def _process_chapter(self, root: ET.Element, chapter_num: int, verse_start: int, verse_end: int) -> str:
        """
        Process a chapter and extract verses in the specified range.

        Args:
            root: XML root element
            chapter_num: Chapter number
            verse_start: Starting verse number
            verse_end: Ending verse number

        Returns:
            HTML string for the chapter content
        """
        # Find the chapter element
        chapter = root.find(f".//cb:chapter[@num='{chapter_num}']", self.NAMESPACE)
        if chapter is None:
            return ""

        html_parts = []

        # Context tracking for proper nesting
        context = {
            "in_paragraph": False,
            "in_poetry": False,
            "in_block_indent": False,
        }

        # Track verse numbers to include
        include_verses = set(range(verse_start, min(verse_end + 1, 1000)))

        # Track if we've seen any verses in the current structural block
        verses_in_current_block = False
        pending_opening_tags = []

        # Process all child elements of the chapter
        for elem in chapter:
            tag = elem.tag.replace(f"{{{self.NAMESPACE['cb']}}}", "")

            if tag == "heading":
                # Only include heading if followed by a verse in our range
                if self._has_relevant_verse_after(elem, include_verses):
                    html_parts.extend(pending_opening_tags)
                    pending_opening_tags = []
                    html_parts.append(self._format_heading(elem))
            elif tag == "subheading":
                if self._has_relevant_verse_after(elem, include_verses):
                    html_parts.extend(pending_opening_tags)
                    pending_opening_tags = []
                    html_parts.append(self._format_subheading(elem))
            elif tag == "verse":
                verse_num = int(elem.get("num", 0))
                if verse_num in include_verses:
                    # We have a verse to include, flush any pending opening tags
                    html_parts.extend(pending_opening_tags)
                    pending_opening_tags = []
                    verses_in_current_block = True
                    verse_html = self._format_verse(elem, verse_num, context)
                    html_parts.append(verse_html)
            elif tag == "begin-paragraph":
                class_attr = elem.get("class", "")
                if class_attr == "line-group":
                    pending_opening_tags.append('<div class="poetry">')
                    context["in_poetry"] = True
                else:
                    pending_opening_tags.append("<p>")
                    context["in_paragraph"] = True
                verses_in_current_block = False
            elif tag == "end-paragraph":
                # Only add closing tag if we actually added verses in this block
                if verses_in_current_block:
                    if context["in_poetry"]:
                        html_parts.append("</div>")
                        context["in_poetry"] = False
                    elif context["in_paragraph"]:
                        html_parts.append("</p>")
                        context["in_paragraph"] = False
                else:
                    # Clear pending tags since we're closing without content
                    if context["in_poetry"]:
                        context["in_poetry"] = False
                    elif context["in_paragraph"]:
                        context["in_paragraph"] = False
                    pending_opening_tags = []
                verses_in_current_block = False
            elif tag == "begin-block-indent":
                # Only open if there will be relevant content
                if self._has_relevant_verse_after(elem, include_verses):
                    pending_opening_tags.append('<div class="block-indent">')
                    context["in_block_indent"] = True
            elif tag == "end-block-indent":
                # Only close if we actually opened it and had content
                if context["in_block_indent"] and verses_in_current_block:
                    html_parts.append("</div>")
                    context["in_block_indent"] = False
                elif context["in_block_indent"]:
                    # We opened it but no verses were added
                    context["in_block_indent"] = False

        return "\n".join(html_parts)

    def _has_relevant_verse_after(self, elem: ET.Element, include_verses: set) -> bool:
        """
        Check if there are any relevant verses after this element in the chapter.

        Args:
            elem: The element to check after
            include_verses: Set of verse numbers to include

        Returns:
            True if there are relevant verses after this element
        """
        # Check following siblings
        current = elem.getnext()
        while current is not None:
            tag = current.tag.replace(f"{{{self.NAMESPACE['cb']}}}", "")
            if tag == "verse":
                verse_num = int(current.get("num", 0))
                if verse_num in include_verses:
                    return True
            current = current.getnext()
        return False

    def _format_heading(self, elem: ET.Element) -> str:
        """Format a heading element."""
        text = "".join(elem.itertext()).strip()
        return f'<h3 class="passage-heading">{text}</h3>'

    def _format_subheading(self, elem: ET.Element) -> str:
        """Format a subheading element."""
        text = "".join(elem.itertext()).strip()
        class_attr = elem.get("class", "")
        return f'<h4 class="passage-subheading {class_attr}">{text}</h4>'

    def _format_verse(self, verse_elem: ET.Element, verse_num: int, context: dict = None) -> str:
        """
        Format a verse element with all its inline content.

        Args:
            verse_elem: The verse XML element
            verse_num: The verse number
            context: Dictionary tracking current formatting context (poetry, paragraph, etc.)

        Returns:
            HTML string for the verse
        """
        if context is None:
            context = {}

        html_parts = [f'<sup class="verse-num">{verse_num}</sup>']

        # Process the verse content
        verse_html = self._process_verse_content(verse_elem, context)
        html_parts.append(verse_html)

        return " ".join(html_parts)

    def _process_verse_content(self, elem: ET.Element, context: dict = None) -> str:
        """
        Recursively process verse content including inline elements and poetry lines.

        Args:
            elem: XML element to process
            context: Dictionary tracking current formatting context (poetry, paragraph, etc.)

        Returns:
            HTML string of the content
        """
        if context is None:
            context = {}

        html_parts = []
        in_line = False

        # Add any text before child elements
        if elem.text:
            # Strip only leading/trailing newlines and excessive indentation, preserve single spaces
            text = elem.text.replace("\n", "").replace("\t", "")
            if text.strip():  # If there's actual content
                html_parts.append(text)

        # Process child elements
        for child in elem:
            tag = child.tag.replace(f"{{{self.NAMESPACE['cb']}}}", "")

            if tag == "woc":
                # Words of Christ - red text
                woc_content = self._process_verse_content(child, context)
                html_parts.append(f'<span class="woc">{woc_content}</span>')
            elif tag == "span":
                class_attr = child.get("class", "")
                span_content = self._process_verse_content(child, context)
                if class_attr == "divine-name":
                    html_parts.append(f'<span class="divine-name">{span_content}</span>')
                elif class_attr == "small-caps":
                    html_parts.append(f'<span class="small-caps">{span_content}</span>')
                else:
                    html_parts.append(span_content)
            elif tag == "q":
                # Quotation mark
                class_attr = child.get("class", "")
                if "begin-double" in class_attr:
                    html_parts.append('"')
                elif "end-double" in class_attr:
                    html_parts.append('"')
                elif "begin-single" in class_attr:
                    html_parts.append("'")
                elif "end-single" in class_attr:
                    html_parts.append("'")
                elif "continue-double" in class_attr:
                    html_parts.append('"')
                elif "continue-single" in class_attr:
                    html_parts.append("'")
            elif tag == "crossref":
                # Cross-reference marker (superscript letter)
                letter = child.get("let", "")
                if letter:
                    html_parts.append(f'<sup class="crossref">{letter}</sup>')
            elif tag == "note":
                # Footnote marker (superscript number)
                # Extract note number from nid (e.g., "n01001006.1" -> "1")
                nid = child.get("nid", "")
                match = re.search(r"\.(\d+)$", nid)
                if match:
                    note_num = match.group(1)
                    html_parts.append(f'<sup class="footnote">{note_num}</sup>')
            elif tag == "selah":
                html_parts.append("<i>Selah</i>")
            elif tag == "begin-line":
                # Handle poetry line beginning with proper indentation
                in_line = True
                class_attr = child.get("class", "")
                if class_attr == "indent":
                    html_parts.append('<span class="line indent">')
                elif class_attr == "indent-2":
                    html_parts.append('<span class="line indent-2">')
                else:
                    html_parts.append('<span class="line">')
            elif tag == "end-line":
                # Handle poetry line ending with optional line break
                in_line = False
                html_parts.append("</span>")
                class_attr = child.get("class", "")
                if class_attr == "br":
                    html_parts.append("<br/>")
                # Add newline for readability in output
                html_parts.append("\n")
            elif tag == "i":
                # Italics (usually in footnotes)
                i_content = self._process_verse_content(child, context)
                html_parts.append(f"<i>{i_content}</i>")
            elif tag == "marker":
                # Skip markers - they're just for reference
                pass
            elif tag == "begin-paragraph":
                class_attr = child.get("class", "")
                if class_attr == "line-group":
                    html_parts.append('<div class="poetry">')
                    context["in_poetry"] = True
                else:
                    html_parts.append("<p>")
                    context["in_paragraph"] = True
            elif tag == "end-paragraph":
                if context.get("in_poetry"):
                    html_parts.append("</div>")
                    context["in_poetry"] = False
                elif context.get("in_paragraph"):
                    html_parts.append("</p>")
                    context["in_paragraph"] = False
            elif tag == "begin-block-indent":
                html_parts.append('<div class="block-indent">')
                context["in_block_indent"] = True
            elif tag == "end-block-indent":
                html_parts.append("</div>")
                context["in_block_indent"] = False
            else:
                # For unknown tags, just process their content
                child_content = self._process_verse_content(child, context)
                html_parts.append(child_content)

            # Add any text after child element
            if child.tail:
                # Remove newlines and tabs but preserve actual spaces
                tail = child.tail.replace("\n", "").replace("\t", "")
                if tail.strip():  # If there's actual content
                    html_parts.append(tail)

        return "".join(html_parts)

    def _generate_text(self) -> str:
        """
        Generate plain text version from HTML.

        Returns:
            Plain text version of the passage
        """
        if not self.html:
            return ""

        # Simple HTML to text conversion
        from html2text import html2text

        try:
            text = html2text(self.html).replace("\n", " ").replace(r"/\s\s+/", " ").strip()
            text = re.sub(r" +", " ", text)
            return text
        except Exception:
            # Fallback: strip HTML tags
            text = re.sub(r"<[^>]+>", "", self.html)
            text = re.sub(r"\s+", " ", text).strip()
            return text

    def _extract_headings(self) -> list:
        """
        Extract section headings from the passage.

        Returns:
            List of tuples (passage_reference, heading_text)
        """
        headings = []

        try:
            root = self._load_xml_tree()

            # Find all headings in the chapter range
            for chapter_num in range(self.start_chapter, self.end_chapter + 1):
                chapter = root.find(f".//cb:chapter[@num='{chapter_num}']", self.NAMESPACE)
                if chapter is None:
                    continue

                for heading in chapter.findall(".//cb:heading", self.NAMESPACE):
                    text = "".join(heading.itertext()).strip()
                    if text:
                        # Try to find the next verse to associate with the heading
                        next_verse = heading.getnext()
                        while next_verse is not None:
                            if next_verse.tag.endswith("verse"):
                                verse_num = next_verse.get("num")
                                ref = f"{self.book} {chapter_num}:{verse_num}"
                                headings.append((ref, text))
                                break
                            next_verse = next_verse.getnext()

        except Exception:
            pass

        return headings

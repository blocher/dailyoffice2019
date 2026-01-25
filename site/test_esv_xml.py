#!/usr/bin/env python3
"""
Standalone test script for ESV XML adapter.
This doesn't require Django to be fully configured.
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

# Try to import lxml if available
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False
    print("Note: lxml not available, using standard library parser")

# Try to import scriptures
try:
    import scriptures
    HAS_SCRIPTURES = True
except ImportError:
    HAS_SCRIPTURES = False
    print("Note: scriptures library not available, using manual parsing")


class SimplePassageParser:
    """Simple passage parser when scriptures library is not available."""
    
    @staticmethod
    def parse(passage):
        """Parse passage into components."""
        # Try to extract book, chapter, and verses
        match = re.match(r"^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$", passage)
        if match:
            return (
                match.group(1).strip(),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(2)),
                int(match.group(4)) if match.group(4) else int(match.group(3)),
                None
            )
        
        # Try chapter range format
        match = re.match(r"^(.+?)\s+(\d+):(\d+)-(\d+):(\d+)$", passage)
        if match:
            return (
                match.group(1).strip(),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4)),
                int(match.group(5)),
                None
            )
        
        raise ValueError(f"Could not parse passage: {passage}")


# XML namespace used in ESV files
NAMESPACE = {"cb": "http://www.crosswaybibles.org"}

# Path to ESV XML files
ESV_DIR = Path(__file__).parent / "bible" / "esv"

# Book name mapping
BOOK_NAME_MAP = {
    # Old Testament
    "Genesis": "Genesis.xml",
    "Exodus": "Exodus.xml",
    "Psalms": "Psalms.xml",
    "Psalm": "Psalms.xml",
    "Matthew": "Matthew.xml",
    "John": "John.xml",
    
    # Apocrypha
    "Tobit": "70.Tobit.xml",
    "Judith": "71.Judith.xml",
    "Wisdom": "73.Wisdom of Solomon.xml",
    "Wisdom of Solomon": "73.Wisdom of Solomon.xml",
    "Sirach": "74.Sirach.xml",
    "1 Maccabees": "80.1 Maccabees.xml",
}


def load_xml_tree(book_name):
    """Load XML tree for a book."""
    if book_name not in BOOK_NAME_MAP:
        raise ValueError(f"Book not found: {book_name}")
    
    filename = BOOK_NAME_MAP[book_name]
    filepath = ESV_DIR / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"XML file not found: {filepath}")
    
    if HAS_LXML:
        parser = etree.XMLParser(load_dtd=True, resolve_entities=True)
        tree = etree.parse(str(filepath), parser)
        return tree.getroot()
    else:
        # Fallback - won't handle entities properly
        tree = ET.parse(filepath)
        return tree.getroot()


def format_verse(verse_elem, verse_num, namespace):
    """Format a single verse element."""
    html_parts = [f'<sup class="verse-num">{verse_num}</sup> ']
    
    # Helper function to process content recursively
    def process_content(elem):
        parts = []
        if elem.text:
            parts.append(elem.text)
        
        for child in elem:
            tag = child.tag.replace(f"{{{namespace['cb']}}}", "")
            
            if tag == "woc":
                parts.append(f'<span class="woc">{process_content(child)}</span>')
            elif tag == "span":
                class_attr = child.get("class", "")
                content = process_content(child)
                if class_attr == "divine-name":
                    parts.append(f'<span class="divine-name">{content}</span>')
                else:
                    parts.append(content)
            elif tag == "q":
                class_attr = child.get("class", "")
                if "begin-double" in class_attr:
                    parts.append('"')
                elif "end-double" in class_attr:
                    parts.append('"')
                elif "begin-single" in class_attr:
                    parts.append("'")
                elif "end-single" in class_attr:
                    parts.append("'")
            elif tag == "crossref":
                letter = child.get("let", "")
                if letter:
                    parts.append(f'<sup class="crossref">{letter}</sup>')
            elif tag == "note":
                nid = child.get("nid", "")
                match = re.search(r'\.(\d+)$', nid)
                if match:
                    parts.append(f'<sup class="footnote">{match.group(1)}</sup>')
            elif tag == "selah":
                parts.append('<i>Selah</i>')
            elif tag == "i":
                parts.append(f'<i>{process_content(child)}</i>')
            else:
                # For unknown tags, process content
                parts.append(process_content(child))
            
            if child.tail:
                parts.append(child.tail)
        
        return "".join(parts)
    
    verse_html = process_content(verse_elem)
    html_parts.append(verse_html)
    
    return "".join(html_parts)


def extract_passage_html(book, start_chapter, start_verse, end_chapter, end_verse):
    """Extract HTML for a passage."""
    root = load_xml_tree(book)
    
    html_parts = []
    
    for chapter_num in range(start_chapter, end_chapter + 1):
        verse_start = start_verse if chapter_num == start_chapter else 1
        verse_end = end_verse if chapter_num == end_chapter else 999
        
        # Find the chapter
        chapter = root.find(f".//cb:chapter[@num='{chapter_num}']", NAMESPACE)
        if chapter is None:
            continue
        
        # Add chapter heading if present
        heading = chapter.find(".//cb:heading", NAMESPACE)
        if heading is not None:
            text = "".join(heading.itertext()).strip()
            html_parts.append(f'<h3 class="passage-heading">{text}</h3>')
        
        # Start paragraph
        html_parts.append("<p>")
        
        # Extract verses in range
        for verse in chapter.findall(".//cb:verse", NAMESPACE):
            verse_num = int(verse.get("num", 0))
            if verse_start <= verse_num <= verse_end:
                verse_html = format_verse(verse, verse_num, NAMESPACE)
                html_parts.append(verse_html)
        
        # End paragraph
        html_parts.append("</p>")
    
    return "\n".join(html_parts)


def test_passage(passage_text):
    """Test parsing a single passage."""
    print(f"\n{'='*60}")
    print(f"Testing: {passage_text}")
    print('='*60)
    
    try:
        # Parse passage
        if HAS_SCRIPTURES:
            try:
                ref = scriptures.extract(passage_text)[0]
                book, start_chapter, start_verse, end_chapter, end_verse, _ = ref
            except:
                ref = SimplePassageParser.parse(passage_text)
                book, start_chapter, start_verse, end_chapter, end_verse, _ = ref
        else:
            ref = SimplePassageParser.parse(passage_text)
            book, start_chapter, start_verse, end_chapter, end_verse, _ = ref
        
        print(f"Parsed: book='{book}', ch {start_chapter}:{start_verse} - ch {end_chapter}:{end_verse}")
        
        # Extract HTML
        html = extract_passage_html(book, start_chapter, start_verse, end_chapter, end_verse)
        
        print(f"\nHTML output ({len(html)} characters):")
        print(html[:800])
        if len(html) > 800:
            print(f"... [truncated, total {len(html)} chars]")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests."""
    print("ESV XML Adapter Test Suite")
    print("="*60)
    print(f"ESV XML Directory: {ESV_DIR}")
    print(f"lxml available: {HAS_LXML}")
    print(f"scriptures available: {HAS_SCRIPTURES}")
    
    # Test cases
    tests = [
        "Genesis 1:1",
        "Genesis 1:1-3",
        "Psalm 23:1",
        "Psalm 23:1-3",
        "John 3:16",
        "Tobit 1:1",
        "Tobit 1:1-3",
        "Wisdom 1:1",
    ]
    
    results = []
    for test in tests:
        results.append(test_passage(test))
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")


if __name__ == "__main__":
    main()

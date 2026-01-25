#!/usr/bin/env python3
"""Simple standalone test for include_references parameter"""

import sys
from pathlib import Path
from lxml import etree

# Define namespace
NAMESPACE = {"cb": "http://www.crosswaybibles.org"}
ESV_DIR = Path(__file__).parent / "bible" / "esv"


def extract_verse(book_file, chapter_num, verse_num, include_references):
    """Extract a single verse and test if references are included/excluded"""
    filepath = ESV_DIR / book_file
    parser = etree.XMLParser(load_dtd=True, resolve_entities=True)
    tree = etree.parse(str(filepath), parser)
    root = tree.getroot()

    chapter = root.find(f".//cb:chapter[@num='{chapter_num}']", NAMESPACE)
    if chapter is None:
        return None

    verse = chapter.find(f".//cb:verse[@num='{verse_num}']", NAMESPACE)
    if verse is None:
        return None

    # Count crossrefs and notes in verse
    crossrefs = verse.findall(".//cb:crossref", NAMESPACE)
    notes = verse.findall(".//cb:note", NAMESPACE)

    print(f"Found {len(crossrefs)} crossrefs and {len(notes)} notes in XML")

    # Now simulate processing like the adapter does
    html_parts = []

    def process_element(elem):
        parts = []
        if elem.text:
            parts.append(elem.text)

        for child in elem:
            tag = child.tag.replace(f"{{{NAMESPACE['cb']}}}", "")

            if tag == "crossref":
                if include_references:
                    letter = child.get("let", "")
                    if letter:
                        parts.append(f'<sup class="crossref">{letter}</sup>')
            elif tag == "note":
                if include_references:
                    nid = child.get("nid", "")
                    parts.append(f'<sup class="footnote">1</sup>')
            else:
                parts.append(process_element(child))

            if child.tail:
                parts.append(child.tail)

        return "".join(parts)

    verse_html = process_element(verse)
    return verse_html


# Test Genesis 1:1 (has crossrefs)
print("=" * 70)
print("TEST: Genesis 1:1 with include_references=True")
print("=" * 70)
html_with = extract_verse("Genesis.xml", 1, 1, include_references=True)
print(html_with)
has_refs_with = "crossref" in html_with or "footnote" in html_with
print(f"Contains references: {has_refs_with}")

print("\n" + "=" * 70)
print("TEST: Genesis 1:1 with include_references=False")
print("=" * 70)
html_without = extract_verse("Genesis.xml", 1, 1, include_references=False)
print(html_without)
has_refs_without = "crossref" in html_without or "footnote" in html_without
print(f"Contains references: {has_refs_without}")

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)
if has_refs_with and not has_refs_without:
    print("✓ SUCCESS: References included when True, excluded when False")
else:
    print(f"✗ FAILED: With={has_refs_with}, Without={has_refs_without}")

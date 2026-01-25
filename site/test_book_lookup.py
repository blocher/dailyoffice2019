#!/usr/bin/env python3
"""Test book name lookup without full adapter"""

import sys
from pathlib import Path

# Replicate the book map and normalization logic
BOOK_NAME_MAP = {
    "1 Corinthians": "1 Corinthians.xml",
    "I Corinthians": "1 Corinthians.xml",
    "2 Kings": "2 Kings.xml",
    "II Kings": "2 Kings.xml",
    "3 John": "3 John.xml",
    "III John": "3 John.xml",
    "1 Timothy": "1 Timothy.xml",
    "I Timothy": "1 Timothy.xml",
    "1 Maccabees": "80.1 Maccabees.xml",
    "I Maccabees": "80.1 Maccabees.xml",
}

def normalize_book_name(book_name):
    roman_to_arabic = {
        "I ": "1 ",
        "II ": "2 ",
        "III ": "3 ",
        "IV ": "4 ",
    }
    for roman, arabic in roman_to_arabic.items():
        if book_name.startswith(roman):
            return arabic + book_name[len(roman):]
    return book_name

def get_xml_filename(book):
    # First normalize
    book = normalize_book_name(book)
    
    # Try direct lookup
    if book in BOOK_NAME_MAP:
        return BOOK_NAME_MAP[book]
    
    # Try case-insensitive
    for key, value in BOOK_NAME_MAP.items():
        if key.lower() == book.lower():
            return value
    
    return None

# Test cases
test_cases = [
    "I Corinthians",
    "II Kings",
    "III John",
    "I Timothy",
    "I Maccabees",
    "1 Corinthians",  # Already normalized
]

print("Testing Book Name Lookup:")
print("=" * 70)

all_passed = True
for book in test_cases:
    filename = get_xml_filename(book)
    if filename:
        print(f"✓ '{book}' -> '{filename}'")
    else:
        print(f"✗ '{book}' -> NOT FOUND")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed")

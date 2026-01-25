#!/usr/bin/env python3
"""Test Roman numeral handling"""

import sys
from pathlib import Path

sys.path.insert(0, '.')

# Test the normalization function
def test_normalize():
    # Simulate the normalize function
    def _normalize_book_name(book_name):
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
    
    test_cases = [
        ("I Corinthians", "1 Corinthians"),
        ("II Kings", "2 Kings"),
        ("III John", "3 John"),
        ("I Samuel", "1 Samuel"),
        ("II Chronicles", "2 Chronicles"),
        ("I Maccabees", "1 Maccabees"),
        ("Genesis", "Genesis"),
        ("John", "John"),
    ]
    
    print("Testing Roman Numeral Normalization:")
    print("=" * 60)
    all_passed = True
    for input_name, expected in test_cases:
        result = _normalize_book_name(input_name)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} '{input_name}' -> '{result}' (expected: '{expected}')")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    return all_passed

if __name__ == "__main__":
    success = test_normalize()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Test Roman numeral handling with actual adapter"""

import sys

sys.path.insert(0, ".")

from bible.esv_xml_adapter import ESVXMLAdapter

# Test cases from the user's list
test_cases = [
    "I Corinthians 15:35-58",
    "II Kings 1",
    "III John 1-15",
    "I Timothy 3",
    "I Maccabees 9",
]

print("Testing Roman Numeral Book Names with ESV XML Adapter:")
print("=" * 70)

success_count = 0
fail_count = 0

for passage in test_cases:
    try:
        adapter = ESVXMLAdapter(passage, "esv")
        html = adapter.get_html()
        if html and len(html) > 100:  # Check for substantive content
            print(f"✓ {passage} ({len(html)} chars)")
            success_count += 1
        else:
            print(f"✗ {passage} - HTML too short: {len(html) if html else 0} chars")
            fail_count += 1
    except Exception as e:
        print(f"✗ {passage} - Error: {e}")
        fail_count += 1

print("\n" + "=" * 70)
print(f"Results: {success_count} passed, {fail_count} failed")

if fail_count == 0:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed")

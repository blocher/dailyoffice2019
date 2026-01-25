#!/usr/bin/env python3
"""
Test ESV XML adapter with Wisdom 6 passage directly using just the adapter code
"""

import sys
import os
from pathlib import Path

# Mock the necessary imports
class MockScriptures:
    def extract(self, text):
        return [(('Wisdom', 6, 1), ('Wisdom', 6, 18))]

sys.modules['scriptures'] = MockScriptures()

# Now import the adapter
sys.path.insert(0, '/home/runner/work/dailyoffice2019/dailyoffice2019/site')

# Mock Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'website.settings'

from bible.esv_xml_adapter import ESVXMLAdapter

print("Testing Wisdom 6:1-3 (first 3 verses)")
print("=" * 80)

try:
    adapter = ESVXMLAdapter('Wisdom 6:1-3', 'esv')
    html = adapter.get_html()
    
    print("\nGenerated HTML:")
    print(html)
    
    print("\n" + "=" * 80)
    print("Analysis:")
    print(f"  - Length: {len(html)} characters")
    print(f"  - <br/> count: {html.count('<br/>')}")
    print(f"  - <span class=\"line\"> count: {html.count('<span class=\"line\">')}")
    print(f"  - Verse numbers: {html.count('<sup class=\"verse-num\">')}")
    print(f"  - Poetry div: {'<div class=\"poetry\">' in html}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

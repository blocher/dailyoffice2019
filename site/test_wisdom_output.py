#!/usr/bin/env python3
"""Test Wisdom 6 HTML output"""

import sys
import os

# Add site directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

import django
django.setup()

from bible.esv_xml_adapter import ESVXMLAdapter

# Test Wisdom 6:1-18
print("Testing Wisdom 6:1-18")
print("=" * 80)

try:
    adapter = ESVXMLAdapter('Wisdom 6:1-18', 'esv')
    html = adapter.get_html()
    
    print("\nHTML Output:")
    print(html)
    
    print("\n" + "=" * 80)
    print("Analysis:")
    print(f"- Total length: {len(html)} characters")
    print(f"- Contains <br/> tags: {html.count('<br/>')}")
    print(f"- Contains poetry div: {'<div class=\"poetry\">' in html}")
    print(f"- Contains line spans: {html.count('<span class=\"line\">')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

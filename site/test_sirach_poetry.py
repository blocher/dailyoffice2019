#!/usr/bin/env python3
"""Test Sirach prologue and poetry indentation"""

import sys
from pathlib import Path

sys.path.insert(0, ".")

# Need to set up minimal environment
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

try:
    import django

    django.setup()
except:
    pass

from lxml import etree


# Test Sirach prologue extraction
def test_sirach_prologue():
    from bible.esv_xml_adapter import ESVXMLAdapter

    print("=" * 70)
    print("TEST: Sirach 1:1 (should include prologue)")
    print("=" * 70)

    try:
        adapter = ESVXMLAdapter("Sirach 1:1", "esv")
        html = adapter.get_html()

        print("HTML Length:", len(html))
        print("\nFirst 1000 characters:")
        print(html[:1000])
        print("\n...")

        # Check for prologue content
        has_prologue = "Prologue" in html or "many and great things" in html
        print(f"\n✓ Has prologue content: {has_prologue}")

        return has_prologue
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_poetry_indentation():
    from bible.esv_xml_adapter import ESVXMLAdapter

    print("\n" + "=" * 70)
    print("TEST: Isaiah 1:2-3 (poetry with indentation)")
    print("=" * 70)

    try:
        adapter = ESVXMLAdapter("Isaiah 1:2-3", "esv")
        html = adapter.get_html()

        print("HTML output:")
        print(html)

        # Check for proper indentation classes
        has_indent_class = 'class="line indent"' in html or 'class="indent"' in html
        has_poetry_div = 'class="poetry"' in html

        print(f"\n✓ Has poetry div: {has_poetry_div}")
        print(f"✓ Has indent class: {has_indent_class}")

        return has_indent_class and has_poetry_div
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result1 = test_sirach_prologue()
    result2 = test_poetry_indentation()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Sirach prologue: {'✓ PASS' if result1 else '✗ FAIL'}")
    print(f"Poetry indentation: {'✓ PASS' if result2 else '✗ FAIL'}")

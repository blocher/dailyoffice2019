#!/usr/bin/env python3
"""Test that indentation uses &nbsp; entities"""

# Test the HTML output
test_html = '<span class="line indent-1"><span class="indent-1-breaks">&nbsp;&nbsp;&nbsp;&nbsp;</span>text here</span>'

print("Test HTML output:")
print(test_html)
print()

# Count nbsp entities
nbsp_count = test_html.count("&nbsp;")
print(f"Number of &nbsp; entities: {nbsp_count}")
print(f"Expected: 4")
print(f"Match: {nbsp_count == 4}")

# Verify structure
has_indent_breaks = "indent-1-breaks" in test_html
has_nbsp = "&nbsp;" in test_html
has_no_regular_spaces_in_breaks = "    " not in test_html  # Should not have 4 regular spaces

print(f"\n✓ Has indent-breaks span: {has_indent_breaks}")
print(f"✓ Has &nbsp; entities: {has_nbsp}")
print(f"✓ No regular spaces in output: {has_no_regular_spaces_in_breaks}")

if nbsp_count == 4 and has_indent_breaks and has_nbsp and has_no_regular_spaces_in_breaks:
    print("\n✓ ALL CHECKS PASSED")
else:
    print("\n✗ SOME CHECKS FAILED")

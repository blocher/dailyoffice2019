#!/usr/bin/env python3
"""Simple test of Wisdom XML parsing without full Django"""

try:
    from lxml import etree as ET
    print("Using lxml")
except ImportError:
    import xml.etree.ElementTree as ET
    print("Using stdlib ET (may have issues with entities)")

import os

# Parse Wisdom XML
xml_file = 'bible/esv/73.Wisdom of Solomon.xml'
print(f"Parsing {xml_file}...")

try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    print("✓ XML parsed successfully")
    
    # Find chapter 6
    chapter = root.find('.//chapter[@num="6"]')
    if chapter is None:
        print("✗ Could not find chapter 6")
    else:
        print("✓ Found chapter 6")
        
        # Find first verse
        verse1 = chapter.find('.//verse[@num="1"]')
        if verse1:
            print("\n=== Verse 1 XML structure ===")
            xml_str = ET.tostring(verse1, encoding='unicode', method='xml')
            print(xml_str[:300])
            
            print("\n=== Analyzing verse 1 elements ===")
            for child in verse1:
                tag = child.tag if hasattr(child, 'tag') else 'text'
                tail = child.tail if hasattr(child, 'tail') and child.tail else ''
                tail_preview = tail[:50].replace('\n', '\\n') if tail else '(none)'
                print(f"  <{tag}> tail=\"{tail_preview}\"")
                
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

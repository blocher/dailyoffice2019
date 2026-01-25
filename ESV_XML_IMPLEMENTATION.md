# ESV Scripture Loader from XML Files

## Overview

This implementation provides functionality to load ESV (English Standard Version) scripture passages from XML files and convert them to beautifully formatted HTML similar to esv.org.

## Components

### 1. ESV XML Adapter (`site/bible/esv_xml_adapter.py`)

The main utility class for reading and parsing ESV XML files.

**Features:**
- Parses XML files for all 66 canonical books + Apocrypha books (70-87)
- Handles book name mapping (normalized names to XML filenames)
- Extracts specific passage ranges (e.g., "Genesis 1:1-5", "John 3:16")
- Converts XML elements to semantic HTML
- Supports complex formatting:
  - Poetry with multiple indentation levels
  - Section headings and subheadings
  - Paragraph structure
  - Quotation marks (nested quotes)
  - Words of Christ (<woc> elements)
  - Divine name formatting (<span class="divine-name">)
  - Cross-reference markers (superscript letters)
  - Footnote markers (superscript numbers)
  - Line breaks and poetry structure

**Usage:**
```python
from bible.esv_xml_adapter import ESVXMLAdapter

# Load a passage (excludes cross-references and footnotes by default)
adapter = ESVXMLAdapter('Genesis 1:1-3', 'esv')

# Load a passage with cross-references and footnotes
adapter_with_refs = ESVXMLAdapter('Genesis 1:1-3', 'esv', include_references=True)

# Get HTML output
html = adapter.get_html()

# Get plain text
text = adapter.get_text()

# Get section headings
headings = adapter.get_headings()
```

**Key Methods:**
- `__init__(passage, version, include_references)` - Initialize with a passage citation
  - `passage`: Scripture citation (e.g., "Genesis 1:1-3")
  - `version`: Translation version (default: "esv")
  - `include_references`: Include cross-references and footnotes (default: False)
- `get_html()` - Returns formatted HTML string
- `get_text()` - Returns plain text version
- `get_headings()` - Returns list of section headings

### 2. Integration with Bible Sources (`site/bible/sources.py` and `site/bible/passage.py`)

The adapter is integrated into the existing Bible passage system:

- Added `get_esv_xml_adapter()` function for lazy loading
- Added "esv_xml" version to `BibleVersions.VERSIONS`
- Updated `Passage` class to handle callable adapters

**Usage:**
```python
from bible.passage import Passage

# Use ESV XML adapter
passage = Passage('Psalm 23:1-3', source='esv_xml')
html = passage.html
```

### 3. Management Command (`site/office/management/commands/reimport_esv_scripture.py`)

Django management command to reimport ESV scripture content for all Scripture model instances.

**Features:**
- Processes all Scripture model instances
- Uses ESV XML adapter to fetch and format passages
- Replaces ESV field content (including empty, null, or "-" values)
- Handles errors prominently with detailed output
- Includes both canonical and Apocrypha citations
- Does NOT modify other translation fields (kjv, rsv, nrsvce, etc.)

**Options:**
- `--dry-run` - Run without saving changes (for testing)
- `--limit N` - Process only first N scriptures (for testing)
- `--passage "Citation"` - Process only a specific passage (for testing)
- `--include-references` - Include cross-references and footnotes in output (default: excluded)

**Usage:**
```bash
# Test with dry run (excludes references by default)
python manage.py reimport_esv_scripture --dry-run --limit 10

# Test with references included
python manage.py reimport_esv_scripture --dry-run --limit 10 --include-references

# Process a specific passage
python manage.py reimport_esv_scripture --passage "Genesis 1:1" --dry-run

# Run for real (processes all scriptures)
python manage.py reimport_esv_scripture
```

**Output:**
- Progress indicator for each scripture processed
- Preview of HTML changes
- Summary statistics (total, updated, skipped, errors)
- Prominent error messages for any failures

## XML File Structure

### Location
ESV XML files are located in `site/bible/esv/`

### Naming Convention
- Canonical books: `{BookName}.xml` (e.g., "Genesis.xml", "John.xml")
- Apocrypha books: `{Number}.{BookName}.xml` (e.g., "70.Tobit.xml", "73.Wisdom of Solomon.xml")

### Schema
Files follow the Crossway Bible schema:
- Namespace: `http://www.crosswaybibles.org`
- Root element: `<crossway-bible>`
- Structure: book → chapter → verse
- See `site/bible/esv/schema/` for full XSD definitions
- See `site/bible/esv/docs/` for formatting documentation

## HTML Output Format

The adapter produces semantic HTML with appropriate CSS classes for styling:

### Example Output

**Prose (Genesis 1:1-3):**
```html
<h3 class="passage-heading">The Creation of the World</h3>
<p>
<sup class="verse-num">1</sup> In the <sup class="crossref">a</sup>beginning, God created the heavens and the earth.
<sup class="verse-num">2</sup> The earth was <sup class="crossref">b</sup>without form and void, and darkness was over the face of the deep...
</p>
```

**Poetry (Psalm 23:1-3):**
```html
<h3 class="passage-heading">The Lord Is My Shepherd</h3>
<div class="block-indent">
<div class="poetry">
<p>
<sup class="verse-num">1</sup> <span class="line">The <span class="divine-name">Lord</span> is my shepherd;</span><br/>
<span class="line indent">I shall not want.</span><br/>
</p>
</div>
</div>
```

### CSS Classes Used

- `passage-heading` - Section headings (h3)
- `passage-subheading` - Subheadings (h4)
- `verse-num` - Verse numbers (superscript)
- `crossref` - Cross-reference letters (superscript)
- `footnote` - Footnote numbers (superscript)
- `woc` - Words of Christ
- `divine-name` - Divine name (LORD)
- `small-caps` - Small caps text
- `poetry` - Poetry container (div)
- `block-indent` - Indented block (div)
- `line` - Poetry line (span)
- `indent` - First-level indentation
- `indent-2` - Second-level indentation

## Book Name Mapping

The adapter includes comprehensive book name mapping to handle variations:

### Canonical Books (1-66)
- Old Testament: Genesis through Malachi
- New Testament: Matthew through Revelation
- Variations handled: 
  - "Psalms" vs "Psalm"
  - "Song of Solomon" vs "Song of Songs"
  - **Roman numerals**: "I Corinthians" → "1 Corinthians", "II Kings" → "2 Kings", etc.
  - Books with numbers can use either Arabic (1, 2, 3) or Roman (I, II, III) numerals

### Apocrypha Books (70-87)
All mapped with their numbered prefixes:
- 70: Tobit
- 71: Judith  
- 72: Esther (Greek)
- 73: Wisdom of Solomon
- 74: Sirach (Ecclesiasticus)
- 75: Baruch
- 76: Letter of Jeremiah
- 77: Prayer of Azariah
- 78: Susanna
- 79: Bel and the Dragon
- 80-81: 1-2 Maccabees
- 82: 1 Esdras
- 83: Prayer of Manasseh
- 84: Psalm 151
- 85-87: 3 Maccabees, 2 Esdras, 4 Maccabees

## Testing

### Test Script
`site/test_esv_xml.py` - Standalone test script that doesn't require Django

**Usage:**
```bash
cd site
python test_esv_xml.py
```

Tests various passage types:
- Prose (Genesis)
- Poetry (Psalms)
- Words of Christ (John)
- Apocrypha (Tobit, Wisdom)

### Manual Testing
```bash
# Test individual passages with the management command
python manage.py reimport_esv_scripture --passage "Genesis 1:1-3" --dry-run
python manage.py reimport_esv_scripture --passage "Psalm 23:1-6" --dry-run
python manage.py reimport_esv_scripture --passage "Tobit 1:1" --dry-run
```

## Dependencies

### Python Packages
- `lxml` - XML parsing with DTD support
- `scriptures` - Citation normalization (from github.com/blocher/python-scriptures)
- `beautifulsoup4` - HTML processing
- `html2text` - HTML to text conversion
- `Django` - For model integration and management commands

### System Requirements
- Python 3.12+
- ESV XML files in `site/bible/esv/` directory

## Implementation Notes

### Citation Normalization
The adapter uses the `scriptures` library to normalize citations before processing:
- "Gen 1:1" → "Genesis 1:1"
- "Jn 3:16" → "John 3:16"
- **Roman numerals** → Arabic numerals: "I Corinthians" → "1 Corinthians", "II Kings" → "2 Kings"
- Falls back to manual parsing for Apocrypha books not recognized by scriptures library

The adapter automatically handles both Roman numeral (I, II, III, IV) and Arabic numeral (1, 2, 3, 4) prefixes in book names.

### Error Handling
- `PassageNotFoundException` - Raised when book or passage cannot be found
- Errors are caught and reported prominently in management command
- Dry-run mode allows testing without database changes

### Performance Considerations
- Each passage requires XML file parsing (cached at file system level)
- lxml with DTD loading handles entity resolution (&emdash;, etc.)
- Batch processing via management command for efficiency

## Future Enhancements

Potential improvements:
1. Add CSS stylesheet for consistent formatting
2. Implement caching layer for frequently accessed passages
3. Add support for parallel passages and cross-references
4. Generate additional output formats (Markdown, plain text)
5. Add validation for generated HTML
6. Support for passage comparison across translations

## Completed Tasks

✅ Task 1: Created ESV XML utility with full formatting support
✅ Task 2: Built management command with error handling and options
✅ Tested with canonical books, Apocrypha, poetry, and prose
✅ Code formatted with black
✅ Integration with existing Bible passage system

## Usage Instructions

**DO NOT RUN** the management command without explicit instruction. It will update the database with new ESV content. The command has been built and tested with --dry-run mode only.

To use when ready:
1. Review the code and test with --dry-run
2. Test with --limit and specific passages
3. Back up the database
4. Run the full command: `python manage.py reimport_esv_scripture`

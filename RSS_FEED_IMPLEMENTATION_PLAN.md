# RSS/Atom Feed Implementation Plan for Daily Office 2019

## Overview

This plan outlines the implementation of RSS 2.0 and Atom feed support for the Daily Office 2019 website, providing subscribers with daily scripture readings from all four Daily Office services (Morning Prayer, Midday Prayer, Evening Prayer, and Compline).

## Requirements Summary

- **Scope**: Daily readings from all four Daily Office services
- **Feed Window**: Past 7 days (rolling window)
- **Content**: Full text of all Bible passages and psalms
- **Bible Translation**: ESV (English Standard Version)
- **Feed Formats**: Both RSS 2.0 and Atom
- **Feed Structure**: One feed item per office per day (4 items per day × 7 days = ~28 items in feed)
- **Deployment**: Served dynamically from the API server (api.dailyoffice2019.com)
- **Frontend Changes**: None required (backend-only implementation)

## Architecture Decision

### New `feeds` Django Module

The RSS/Atom feed functionality will live in a new lightweight Django module:

```
site/feeds/
├── __init__.py
├── feeds.py      # Feed generation classes
└── urls.py       # URL routing for feeds
```

**Rationale**:
- **Separation of Concerns**: Feed logic is isolated from office, bible, and other apps
- **Lightweight**: Just the essential files (feeds.py and urls.py) without extra overhead
- **Extensible**: Easy to add more feed types later without cluttering other apps
- **Follows Django Conventions**: Each feature gets its own app/module

### Why API-Served Dynamic Feeds?

The RSS/Atom feeds will be served from the Django API (api.dailyoffice2019.com) rather than being included in the static site generation. This approach offers:

1. **Always Current**: Feed automatically updates daily without manual rebuilds
2. **Minimal Changes**: No modifications to static build process or frontend code
3. **Consistent with Existing Architecture**: The Vue frontend already relies on the API for dynamic data
4. **Zero Maintenance**: No need for daily cron jobs or scheduled rebuilds

## Implementation Steps

### Step 1: Create the Feeds Module Structure

**Action**: Create the new `site/feeds/` directory and initialize it as a Django module.

**Commands**:
```bash
cd site
mkdir feeds
touch feeds/__init__.py
touch feeds/feeds.py
touch feeds/urls.py
```

**File Structure**:
```
site/
├── feeds/              # NEW MODULE
│   ├── __init__.py
│   ├── feeds.py        # Feed generation classes
│   └── urls.py         # URL routing
├── office/
├── churchcal/
├── bible/
└── ...
```

---

### Step 2: Register the Feeds Module

**Location**: `site/website/settings.py`

**Action**: Add `'feeds'` to the `INSTALLED_APPS` list.

**Code to Add**:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'office',
    'churchcal',
    'bible',
    'psalter',
    'feeds',  # ADD THIS LINE
    # ... rest of apps ...
]
```

**Rationale**: Even lightweight modules should be registered so Django recognizes them.

---

### Step 3: Create Feed Generation Classes

**Location**: `site/feeds/feeds.py` (new file)

**Action**: Create feed classes using Django's built-in syndication framework.

**Full Implementation**:

```python
"""
RSS and Atom feed generation for Daily Office 2019

This module provides RSS 2.0 and Atom feeds of daily scripture readings
from Morning Prayer, Midday Prayer, Evening Prayer, and Compline.
"""

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.http import HttpRequest
from datetime import datetime, timedelta
from django.utils.html import strip_tags
import re


class DailyOfficeFeedBase:
    """
    Base class for Daily Office feeds with shared logic

    Generates feed items for the past 7 days, with one item per office per day.
    Each item contains the full text of all psalms and scripture readings.
    """

    title = "Daily Office 2019 - Daily Scripture Readings"
    link = "https://www.dailyoffice2019.com/"
    description = (
        "Daily scripture readings from Morning Prayer, Midday Prayer, "
        "Evening Prayer, and Compline according to the Book of Common Prayer (2019)"
    )

    # Office types to include in the feed
    OFFICES = ['Morning Prayer', 'Midday Prayer', 'Evening Prayer', 'Compline']

    def items(self):
        """
        Generate feed items for the past 7 days

        Returns a list of dicts with 'date' and 'office' keys.
        Items are in reverse chronological order (newest first).
        """
        items_list = []
        today = datetime.now().date()

        # Generate 7 days of readings (past week)
        for i in range(7):
            date = today - timedelta(days=i)

            # Create items for each office
            for office_name in self.OFFICES:
                items_list.append({
                    'date': date,
                    'office': office_name,
                })

        return items_list

    def item_title(self, item):
        """
        Format item title as: 'October 17, 2025 - Morning Prayer'
        """
        return f"{item['date'].strftime('%B %d, %Y')} - {item['office']}"

    def item_description(self, item):
        """
        Generate full HTML content with all readings for this office

        This is the main content that appears in feed readers.
        Includes psalms, scripture readings, and calendar information.
        """
        try:
            return self._generate_office_content(item['date'], item['office'])
        except Exception as e:
            # Graceful fallback if content generation fails
            return f"<p>Readings for {item['office']} on {item['date'].strftime('%B %d, %Y')}</p>"

    def item_link(self, item):
        """
        Link to the office page on the website

        Format: https://www.dailyoffice2019.com/pray/{office_slug}/{date}
        """
        office_slug = item['office'].lower().replace(' ', '_')
        date_str = item['date'].strftime('%Y-%m-%d')
        return f"https://www.dailyoffice2019.com/pray/{office_slug}/{date_str}"

    def item_pubdate(self, item):
        """
        Publication date/time for the item

        Set to 6:00 AM on the reading date (approximate time offices are prayed)
        """
        return datetime.combine(item['date'], datetime.min.time().replace(hour=6))

    def item_guid(self, item):
        """
        Unique, stable identifier for each feed item

        Format: dailyoffice2019:{office_slug}:{date}
        This ensures feed readers don't show duplicates.
        """
        date_str = item['date'].strftime('%Y-%m-%d')
        office_slug = item['office'].lower().replace(' ', '_')
        return f"dailyoffice2019:{office_slug}:{date_str}"

    def _generate_office_content(self, date, office_name):
        """
        Generate the full HTML content for an office's readings

        This reuses the existing Readings class and helper functions from
        the office app to ensure consistency with the API.

        Args:
            date: datetime.date object
            office_name: str like 'Morning Prayer', 'Evening Prayer', etc.

        Returns:
            str: HTML content for the feed item
        """
        from office.api.views.index import Readings

        year, month, day = date.year, date.month, date.day

        # Create a mock request object with required attributes
        request = HttpRequest()
        request.GET = {}
        request.query_params = {}

        # Get the readings using the existing API logic
        readings = Readings(
            request,
            year, month, day,
            translation='esv',
            psalms='contemporary',
            style='whole_verse'
        )

        # Build HTML content
        html_parts = []

        # Header with office and date
        html_parts.append(f"<h2>{office_name}</h2>")
        html_parts.append(f"<p><strong>{date.strftime('%A, %B %d, %Y')}</strong></p>")

        # Add liturgical season and commemoration
        html_parts.append(f"<p><em>Season: {readings.date.season.name}</em></p>")
        if readings.date.primary:
            html_parts.append(f"<p><em>{readings.date.primary.name}</em></p>")

        # Extract and format readings for this specific office
        office_readings = self._get_office_readings(readings, office_name)

        for reading in office_readings:
            if reading:  # Skip None/empty readings
                html_parts.append(self._format_reading(reading))

        return '\n'.join(html_parts)

    def _get_office_readings(self, readings_obj, office_name):
        """
        Extract readings for a specific office from the Readings object

        Maps office names to the appropriate reading retrieval functions
        from office.api.views.index.

        Args:
            readings_obj: Readings instance with all data for the day
            office_name: str name of the office

        Returns:
            list: List of reading dicts with 'name', 'citation', 'text' keys
        """
        from office.api.views.index import (
            morning_prayer_30_day_psalms,
            standard_morning_prayer_reading_1,
            standard_morning_prayer_reading_2,
            holy_day_morning_prayer_reading_1,
            holy_day_morning_prayer_reading_2,
            evening_prayer_30_day_psalms,
            standard_evening_prayer_reading_1,
            standard_evening_prayer_reading_2,
            holy_day_evening_prayer_reading_1,
            holy_day_evening_prayer_reading_2,
        )

        # Map office names to reading functions
        # Uses holy day readings if available, otherwise standard readings
        if office_name == 'Morning Prayer':
            reading_functions = [
                morning_prayer_30_day_psalms,
            ]
            if readings_obj.holy_day_readings:
                reading_functions.extend([
                    holy_day_morning_prayer_reading_1,
                    holy_day_morning_prayer_reading_2,
                ])
            else:
                reading_functions.extend([
                    standard_morning_prayer_reading_1,
                    standard_morning_prayer_reading_2,
                ])

        elif office_name == 'Evening Prayer':
            reading_functions = [
                evening_prayer_30_day_psalms,
            ]
            if readings_obj.holy_day_readings:
                reading_functions.extend([
                    holy_day_evening_prayer_reading_1,
                    holy_day_evening_prayer_reading_2,
                ])
            else:
                reading_functions.extend([
                    standard_evening_prayer_reading_1,
                    standard_evening_prayer_reading_2,
                ])

        elif office_name == 'Midday Prayer':
            # TODO: Investigate midday prayer structure
            # Midday prayer likely has psalms but may not have scripture readings
            # Need to examine MiddayPrayerView to determine structure
            return []

        elif office_name == 'Compline':
            # TODO: Investigate compline structure
            # Compline typically has fixed psalms and may not have variable readings
            # Need to examine ComplineView to determine structure
            return []

        else:
            return []

        # Execute functions to get reading data
        readings = []
        for func in reading_functions:
            try:
                reading_data = func(readings_obj)
                # Use 'full' version of readings (not abbreviated)
                if isinstance(reading_data, dict) and 'full' in reading_data:
                    readings.append(reading_data['full'])
                else:
                    readings.append(reading_data)
            except Exception as e:
                # Skip readings that fail to load
                continue

        return readings

    def _format_reading(self, reading):
        """
        Format a single reading (psalm or scripture) as HTML

        Args:
            reading: dict with 'name', 'citation', 'text' keys

        Returns:
            str: Formatted HTML for this reading
        """
        if not reading or not isinstance(reading, dict):
            return ""

        html = f"<h3>{reading.get('name', 'Reading')}</h3>"

        citation = reading.get('citation', '')
        if citation:
            html += f"<p><strong>{citation}</strong></p>"

        text = reading.get('text', '')
        if text:
            html += text  # Text already contains HTML from the passage rendering

        return html


class DailyOfficeRSSFeed(DailyOfficeFeedBase, Feed):
    """
    RSS 2.0 feed for Daily Office readings

    Available at: /feed.rss or /feed/
    """
    feed_type = Feed.feed_type  # Uses default RSS 2.0 generator
    author_name = "Daily Office 2019"
    categories = [
        "Religion",
        "Christianity",
        "Daily Devotions",
        "Scripture",
        "Prayer Book",
        "Anglican",
        "ACNA"
    ]


class DailyOfficeAtomFeed(DailyOfficeFeedBase, Feed):
    """
    Atom feed for Daily Office readings

    Available at: /feed.atom
    """
    feed_type = Atom1Feed
    subtitle = DailyOfficeFeedBase.description
    author_name = "Daily Office 2019"
```

**Key Features**:
- **Reuses existing logic**: Leverages the `Readings` class and helper functions from `office` app
- **Error handling**: Try/except blocks to gracefully handle missing data
- **Holy day support**: Automatically uses holy day readings when appropriate
- **Extensible**: Easy to add Midday/Compline support once we understand their structure
- **Clean HTML**: Properly formatted content for feed readers

---

### Step 4: Create Feed URL Routing

**Location**: `site/feeds/urls.py` (new file)

**Action**: Define URL patterns for the feeds.

**Code**:
```python
"""
URL routing for RSS and Atom feeds
"""

from django.urls import path
from .feeds import DailyOfficeRSSFeed, DailyOfficeAtomFeed

app_name = 'feeds'

urlpatterns = [
    path('feed.rss', DailyOfficeRSSFeed(), name='rss'),
    path('feed.atom', DailyOfficeAtomFeed(), name='atom'),
    path('feed/', DailyOfficeRSSFeed(), name='default'),  # Default to RSS
]
```

---

### Step 5: Include Feeds URLs in Main URL Config

**Location**: `site/website/api_urls.py`

**Action**: Include the feeds URLs in the main API URL configuration.

**Code to Add**:
```python
from django.urls import include, path, re_path
# ... existing imports ...

urlpatterns = [
    # ... existing patterns ...

    # RSS/Atom Feeds
    path('', include('feeds.urls')),

    # ... rest of patterns ...
]
```

**Resulting Feed URLs**:
- RSS 2.0: `https://api.dailyoffice2019.com/feed.rss`
- Atom: `https://api.dailyoffice2019.com/feed.atom`
- Default (RSS): `https://api.dailyoffice2019.com/feed/`

---

### Step 6: Investigate Midday Prayer and Compline Structure

**Action**: Research the structure of Midday Prayer and Compline to complete the feed implementation.

**Investigation Tasks**:

1. **Examine the views**:
   - Look at `MiddayPrayerView` in `site/office/api/views/index.py`
   - Look at `ComplineView` in `site/office/api/views/index.py`

2. **Determine**:
   - Do they have scripture readings or only psalms?
   - What helper functions exist for extracting their content?
   - Are their readings fixed or variable by date?

3. **Update `feeds.py`**:
   - Add appropriate helper function calls to `_get_office_readings()`
   - Handle any special cases for these offices

**Example of what to look for**:
```python
# In office/api/views/index.py, search for patterns like:
class MiddayPrayerView(...)
    # What serializer does it use?
    # What modules/sections does it include?

# Look for helper functions like:
def midday_prayer_psalms(obj):
    # How are psalms retrieved?

def midday_prayer_reading(obj):
    # Are there scripture readings?
```

---

### Step 7: Add Feed Auto-Discovery (Optional)

**Location**: `app/public/index.html` or Vue app `<head>` section

**Action**: Add `<link>` tags so feed readers can auto-discover the feeds.

**Code**:
```html
<link rel="alternate" type="application/rss+xml"
      title="Daily Office 2019 - Daily Readings (RSS)"
      href="https://api.dailyoffice2019.com/feed.rss">
<link rel="alternate" type="application/atom+xml"
      title="Daily Office 2019 - Daily Readings (Atom)"
      href="https://api.dailyoffice2019.com/feed.atom">
```

**Rationale**: This is optional but recommended. It allows browsers and feed readers to automatically detect available feeds.

**Note**: This is the ONLY frontend change, and it's optional.

---

### Step 8: Testing

**Test Plan**:

#### 8.1 Local Development Testing

```bash
cd site
source env/bin/activate
python manage.py runserver

# Test in browser:
# http://127.0.0.1:8000/feed.rss
# http://127.0.0.1:8000/feed.atom
# http://127.0.0.1:8000/feed/
```

#### 8.2 Validate Feed XML

- **RSS Validator**: https://validator.w3.org/feed/
- Paste feed URL or XML content
- Fix any validation errors

#### 8.3 Test with Feed Readers

Test with popular readers:
- **Feedly**: https://feedly.com
- **Inoreader**: https://www.inoreader.com
- **NetNewsWire**: https://netnewswire.com (Mac/iOS)
- **Thunderbird**: Has built-in feed reader

Verify:
- ✅ All content renders correctly
- ✅ Full text of passages appears
- ✅ Links work properly
- ✅ Items appear in correct order (newest first)

#### 8.4 Content Quality Checks

- ✅ Feed contains 7 days of readings
- ✅ Each day has entries for Morning and Evening Prayer (Midday/Compline may be pending Step 6)
- ✅ Bible passages are complete and properly formatted
- ✅ Psalm text renders correctly
- ✅ Citations are accurate
- ✅ HTML entities are properly escaped
- ✅ Special characters (Lᴏʀᴅ, quotes, etc.) display correctly
- ✅ Links point to correct website pages

#### 8.5 Error Handling

Test edge cases:
- ✅ Feed works on holy days (uses holy day readings)
- ✅ Feed works on regular days (uses standard readings)
- ✅ Feed handles missing data gracefully
- ✅ No 500 errors in various date ranges

---

### Step 9: Documentation

#### 9.1 Create Feed Documentation

**Location**: `site/feeds/README.md` (new file)

**Content**:
```markdown
# RSS/Atom Feeds

This module provides RSS 2.0 and Atom feeds of daily scripture readings from the Daily Office.

## Feed URLs

- **RSS 2.0**: https://api.dailyoffice2019.com/feed.rss
- **Atom**: https://api.dailyoffice2019.com/feed.atom
- **Default** (RSS): https://api.dailyoffice2019.com/feed/

## Feed Content

Each feed contains:
- **Past 7 days** of readings (rolling window)
- **All Daily Office services**: Morning Prayer, Midday Prayer, Evening Prayer, Compline
- **Full text** of psalms and scripture readings (ESV translation)
- **Liturgical calendar** information (season, commemorations)
- **Links** back to corresponding pages on dailyoffice2019.com

## Feed Structure

- **One item per office per day** (4 items/day × 7 days = 28 total items)
- Items sorted in **reverse chronological order** (newest first)
- Each item includes:
  - **Title**: "Date - Office Name" (e.g., "October 17, 2025 - Morning Prayer")
  - **Full text** of all psalms and readings for that office
  - **Calendar info**: Season, commemorations, collect
  - **Link** to the office page on the website

## Subscribing

Users can subscribe in any RSS/Atom reader:
- Feedly, Inoreader, NetNewsWire, Thunderbird, and many others
- Simply paste the feed URL into your reader's "Add Feed" function

## Technical Implementation

### Files

- `feeds/feeds.py`: Feed generation classes
- `feeds/urls.py`: URL routing
- `feeds/README.md`: This documentation

### Architecture

The feeds use:
- **Django's syndication framework** (`django.contrib.syndication`)
- **Existing office API logic** (reuses `Readings` class from `office` app)
- **Dynamic generation** (always current, no static build needed)

### Feed Classes

- `DailyOfficeFeedBase`: Shared logic for both feed types
- `DailyOfficeRSSFeed`: RSS 2.0 implementation
- `DailyOfficeAtomFeed`: Atom implementation

### Content Generation

For each feed item:
1. Create mock request object
2. Instantiate `Readings` class with date
3. Extract readings using helper functions from `office.api.views.index`
4. Format as HTML for feed content
5. Add calendar metadata and links

### Performance

- Each feed request generates ~28 items
- Each item fetches readings from database
- Estimated generation time: 1-2 seconds
- Consider adding caching if this becomes an issue

## Future Enhancements

Possible additions:
- Separate feeds per office type
- Custom date ranges via URL parameters
- Multiple Bible translations
- Podcast-style audio feeds
- Caching layer
```

#### 9.2 Update Main README

**Location**: `/README.md` (root of repository)

**Action**: Add RSS feed section.

**Code to Add**:
```markdown
## RSS/Atom Feeds

Subscribe to daily scripture readings via RSS or Atom:

- **RSS Feed**: https://api.dailyoffice2019.com/feed.rss
- **Atom Feed**: https://api.dailyoffice2019.com/feed.atom

The feeds include the past 7 days of readings from all Daily Office services (Morning Prayer, Midday Prayer, Evening Prayer, and Compline), with full text of all psalms and scripture passages in the ESV translation.

See [site/feeds/README.md](site/feeds/README.md) for details.
```

---

### Step 10: Deployment

#### 10.1 Run Local Tests

```bash
cd site
source env/bin/activate

# Run any existing tests
python manage.py test

# Start local server and manually test feeds
python manage.py runserver
# Visit http://127.0.0.1:8000/feed.rss
```

#### 10.2 Commit Changes

```bash
git add site/feeds/
git add site/website/settings.py
git add site/website/api_urls.py
git add site/feeds/README.md
git add README.md
# Add any other changed files

git commit -m "Add RSS/Atom feeds for daily scripture readings

- Create new feeds module with RSS 2.0 and Atom support
- Include past 7 days of readings from all offices
- Full text of psalms and scripture passages (ESV)
- Served dynamically from API (no static build changes)
- Closes #206"
```

#### 10.3 Deploy to Production

- Push changes to your repository
- Deploy to `api.dailyoffice2019.com` using your normal deployment process
- No static site rebuild needed (this is API-only)

#### 10.4 Verify Production

```bash
# Test production feeds
curl https://api.dailyoffice2019.com/feed.rss | head -50
curl https://api.dailyoffice2019.com/feed.atom | head -50

# Or test in browser:
# https://api.dailyoffice2019.com/feed.rss
# https://api.dailyoffice2019.com/feed.atom
```

- Subscribe to feeds in a feed reader
- Verify content loads correctly
- Check server logs for any errors

---

## Module Structure Summary

```
site/
├── feeds/                  # NEW MODULE
│   ├── __init__.py
│   ├── feeds.py            # Feed generation classes
│   ├── urls.py             # URL routing
│   └── README.md           # Documentation
├── office/                 # Existing - provides reading data
├── churchcal/              # Existing - provides calendar data
├── bible/                  # Existing - may provide passage text
├── psalter/                # Existing - provides psalm text
└── website/
    ├── settings.py         # MODIFIED: Add 'feeds' to INSTALLED_APPS
    └── api_urls.py         # MODIFIED: Include feeds.urls
```

**Dependencies**:
- `feeds` module depends on `office`, `churchcal`, and `psalter`
- No other modules depend on `feeds` (clean separation)

---

## Future Enhancements (Out of Scope for MVP)

1. **Multiple Feed Options**:
   - Separate feeds per office: `/feed/morning_prayer.rss`, `/feed/evening_prayer.rss`
   - Different time windows: `/feed/today.rss`, `/feed/next-30-days.rss`
   - Bible translation options: `/feed.rss?translation=kjv`

2. **Feed Parameters**:
   - URL parameters: `/feed.rss?office=morning&days=30&translation=esv`
   - Allow users to customize feed content

3. **Podcast Feed**:
   - Create podcast-style RSS with audio enclosures
   - Leverage existing audio generation features

4. **Analytics**:
   - Track subscriber counts
   - Monitor popular items

5. **Caching**:
   - Add Redis/Memcached caching
   - Cache feeds for 1 hour to reduce load

6. **Models** (convert from lightweight to full app):
   - Add `FeedSubscription` model
   - Track feed access patterns
   - Store cached feed data

---

## Estimated Implementation Time

- **Step 1**: Create module structure - 5 minutes
- **Step 2**: Register in settings - 2 minutes
- **Step 3**: Create feed classes - 2-3 hours
- **Step 4**: Include URLs - 5 minutes
- **Step 5**: Investigate Midday/Compline - 30-60 minutes
- **Step 6**: Auto-discovery tags (optional) - 15 minutes
- **Step 7**: Testing - 1 hour
- **Step 8**: Documentation - 30 minutes
- **Step 9**: Deployment - 30 minutes

**Total**: ~5-6 hours for complete implementation and testing

**MVP (Steps 1-5, 7, 9 only)**: ~3-4 hours

---

## Success Criteria

✅ **Module created**: `site/feeds/` exists with proper structure

✅ **Feeds accessible**: Both RSS and Atom feeds available at specified URLs

✅ **Validation passes**: Feeds validate using W3C Feed Validator

✅ **Feed readers work**: Feeds display correctly in Feedly, Inoreader, NetNewsWire

✅ **Full content**: Feed items contain complete psalm and scripture text

✅ **Correct scope**: Feed covers exactly past 7 days

✅ **All offices**: Morning and Evening Prayer included (Midday/Compline pending Step 6)

✅ **Links work**: Feed item links navigate to correct website pages

✅ **Proper formatting**: Dates, times, and HTML render correctly

✅ **No errors**: Clean server logs, no exceptions during feed generation

---

## Questions to Resolve

1. ✅ **Module structure**: Decided on lightweight module at `site/feeds/`

2. **Midday/Compline readings**: Need to investigate their structure in Step 6

3. **Holy day handling**: Current implementation uses holy day readings when available - is this correct?

4. **Link format**: Assuming `/pray/{office}/{date}` - need to verify actual URL structure

5. **Character encoding**: Need to test special characters (Lᴏʀᴅ, curly quotes, etc.)

---

## Conclusion

This implementation plan creates a clean, minimal RSS/Atom feed solution as a dedicated lightweight Django module. By isolating feed logic in `site/feeds/`, we:

- Keep the codebase organized
- Make feeds easy to maintain and extend
- Follow Django best practices
- Avoid cluttering other apps

The feeds leverage Django's built-in syndication framework and reuse existing API logic, delivering a robust solution with minimal code and no frontend changes.

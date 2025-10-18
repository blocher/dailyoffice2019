"""
RSS feed generation for Daily Office 2019

This module provides RSS 2.0 feeds of daily scripture readings
from Morning Prayer, Midday Prayer, Evening Prayer, and Compline.
"""

from django.contrib.syndication.views import Feed
from datetime import datetime


class DailyOfficeRSSFeed(Feed):
    """
    RSS 2.0 feed for Daily Office readings

    Generates feed items for today only, with one item per office.
    Each item contains the full text of all psalms and scripture readings.
    """

    title = "Daily Office 2019 - Daily Scripture Readings"
    link = "https://www.dailyoffice2019.com/"
    description = (
        "Daily scripture readings from Morning Prayer, Midday Prayer, "
        "Evening Prayer, and Compline according to the Book of Common Prayer (2019)"
    )
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

    # Office types to include in the feed
    OFFICES = ['Morning Prayer', 'Evening Prayer']  # Start with these two, add Midday/Compline later

    def __init__(self, psalter_cycle=30):
        """Initialize feed with specified psalter cycle (30 or 60 days)"""
        super().__init__()
        self.psalter_cycle = psalter_cycle

    def items(self):
        """
        Generate feed items for today only

        Returns a list of dicts with 'date' and 'office' keys.
        """
        items_list = []
        today = datetime.now().date()

        # Create items for each office for today
        for office_name in self.OFFICES:
            items_list.append({
                'date': today,
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
            import traceback
            error_details = traceback.format_exc()
            return f"<p>Readings for {item['office']} on {item['date'].strftime('%B %d, %Y')}</p><p>Error: {str(e)}</p><pre>{error_details}</pre>"

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

        Directly accesses the database to get readings without requiring
        full calendar data.

        Args:
            date: datetime.date object
            office_name: str like 'Morning Prayer', 'Evening Prayer', etc.

        Returns:
            str: HTML content for the feed item
        """
        from office.models import StandardOfficeDay, ThirtyDayPsalterDay
        from psalter.utils import get_psalms

        # Get the standard office day for this date
        office_day = StandardOfficeDay.objects.select_related('officeday_ptr').get(
            month=date.month,
            day=date.day
        )

        # Get psalms based on cycle
        if self.psalter_cycle == 60:
            # For 60-day cycle, psalms come from office_day
            # Use the appropriate fields from the office day
            psalms_source = office_day.officeday_ptr
        else:
            # For 30-day cycle, psalms come from ThirtyDayPsalterDay
            psalms_source = ThirtyDayPsalterDay.objects.get(day=date.day)

        # Build HTML content
        html_parts = []

        # Header with office and date
        html_parts.append(f"<h2>{office_name}</h2>")
        html_parts.append(f"<p><strong>{date.strftime('%A, %B %d, %Y')}</strong></p>")

        # Add readings based on office type
        if office_name == 'Morning Prayer':
            # Add psalms
            psalms_text = get_psalms(
                psalms_source.mp_psalms,
                simplified_citations=True,
                language_style='contemporary',
                headings='whole_verse'
            )
            psalm_count = len(psalms_source.mp_psalms.split(','))
            psalm_plural = 's' if psalm_count > 1 else ''
            html_parts.append(f"<h3>The Psalm{psalm_plural}</h3>")
            html_parts.append(f"<p><strong>Psalm{psalm_plural} {psalms_source.mp_psalms.replace(',', ', ')}</strong></p>")
            html_parts.append(psalms_text)

            # Add readings
            html_parts.append(f"<h3>The First Lesson</h3>")
            html_parts.append(f"<p><strong>{office_day.officeday_ptr.mp_reading_1}</strong></p>")
            if office_day.officeday_ptr.mp_reading_1_text:
                html_parts.append(office_day.officeday_ptr.mp_reading_1_text)

            html_parts.append(f"<h3>The Second Lesson</h3>")
            html_parts.append(f"<p><strong>{office_day.officeday_ptr.mp_reading_2}</strong></p>")
            if office_day.officeday_ptr.mp_reading_2_text:
                html_parts.append(office_day.officeday_ptr.mp_reading_2_text)

        elif office_name == 'Evening Prayer':
            # Add psalms
            psalms_text = get_psalms(
                psalms_source.ep_psalms,
                simplified_citations=True,
                language_style='contemporary',
                headings='whole_verse'
            )
            psalm_count = len(psalms_source.ep_psalms.split(','))
            psalm_plural = 's' if psalm_count > 1 else ''
            html_parts.append(f"<h3>The Psalm{psalm_plural}</h3>")
            html_parts.append(f"<p><strong>Psalm{psalm_plural} {psalms_source.ep_psalms.replace(',', ', ')}</strong></p>")
            html_parts.append(psalms_text)

            # Add readings
            html_parts.append(f"<h3>The First Lesson</h3>")
            html_parts.append(f"<p><strong>{office_day.officeday_ptr.ep_reading_1}</strong></p>")
            if office_day.officeday_ptr.ep_reading_1_text:
                html_parts.append(office_day.officeday_ptr.ep_reading_1_text)

            html_parts.append(f"<h3>The Second Lesson</h3>")
            html_parts.append(f"<p><strong>{office_day.officeday_ptr.ep_reading_2}</strong></p>")
            if office_day.officeday_ptr.ep_reading_2_text:
                html_parts.append(office_day.officeday_ptr.ep_reading_2_text)

        return '\n'.join(html_parts)

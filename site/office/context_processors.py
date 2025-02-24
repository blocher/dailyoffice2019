from django.utils.safestring import mark_safe

from website.settings import APP_VERSION
from website.settings import MODE


def get_on(path):
    if path == "/":
        return "now-button"

    if "about" in path:
        return "about-button"

    if "church_year" in path:
        return "calendar-button"

    if "settings" in path:
        return "settings-button"

    return None


settings_dict = [
    {
        "title": "Psalter Cycle",
        "name": "psalter",
        "help_text": mark_safe(
            "During Morning and Evening Prayer, pray through all the Psalms either every <strong>60 days</strong> (fewer psalms per day) or once every <strong>30 days</strong> (more psalms per day)."
        ),
        "options": [
            {
                "value": "60",
                "hide": ["psalter-thirty"],
                "show": ["psalter-sixty"],
                "heading": "60 Day",
                "text": "Pray through the psalms once every 60 days",
            },
            {
                "value": "30",
                "hide": ["psalter-sixty"],
                "show": ["psalter-thirty"],
                "heading": "30 Day",
                "text": "Pray through the psalms once every 30 days",
            },
        ],
    },
    {
        "title": "Reading Cycle",
        "name": "reading_cycle",
        "help_text": mark_safe(
            "Read through most of the Bible during Morning and Evening Prayer every <strong>1 year</strong> or every <strong>2 years</strong>.  The one year cycle is best if you do <strong>both</strong> Morning and Evening prayer daily; the two year cycle is best if you do only one."
        ),
        "options": [
            {
                "value": "1",
                "hide": [],
                "show": [],
                "heading": "One Year",
                "text": mark_safe(
                    "Read through most of the Bible each year. (Use if you pray <strong>both</strong> Morning and Evening Prayer)"
                ),
            },
            {
                "value": "2",
                "hide": [],
                "show": [],
                "heading": "Two Year",
                "text": mark_safe(
                    "Read through most of the Bible in two years. (Use if you pray <strong>either</strong> Morning <strong>or</strong> Evening prayer)"
                ),
            },
        ],
    },
    {
        "title": "Reading Length",
        "name": "reading_length",
        "help_text": "Always use the full readings, or use the shortened readings (when there are suggested abbreviations).",
        "options": [
            {
                "value": "full",
                "hide": [],
                "show": [],
                "heading": "Full",
                "text": "The full readings will always be used.",
            },
            {
                "value": "abbreviated",
                "hide": [],
                "show": [],
                "heading": "Abbreviated",
                "text": "Suggested abbreviations, when available.",
            },
        ],
    },
    {
        "title": "Reading Audio",
        "name": "reading_audio",
        "help_text": "Show or hide an audio player to listen to the scripture readings during Morning and Evening Prayer.  Audio is provided by esv.org and currently does not include the Deuterocanon/Apocrypha.",
        "options": [
            {
                "value": "off",
                "hide": ["bible-audio"],
                "show": [],
                "heading": "Disable Audio",
                "text": "No audio controls for scripture readings",
            },
            {
                "value": "on",
                "hide": [],
                "show": ["bible-audio"],
                "heading": "Enable Audio",
                "text": "Enable audio player for scripture readings",
            },
        ],
    },
    {
        "title": "Canticle Rotation",
        "name": "canticle_rotation",
        "help_text": "",
        "options": [
            {
                "value": "default",
                "hide": ["canticle-1979", "canticle-2011"],
                "show": ["canticle-default"],
                "heading": "Traditional",
                "text": "The traditional fixed canticles each day",
            },
            {
                "value": "2011",
                "hide": ["canticle-1979", "canticle-default"],
                "show": ["canticle-2011"],
                "heading": "Seasonal Rotation",
                "text": "One fixed canticle and one canticle that rotates by season",
            },
            {
                "value": "1979",
                "hide": ["canticle-default", "canticle-2011"],
                "show": ["canticle-1979"],
                "heading": "Daily Rotation",
                "text": "A rotating set of canticles by day of week and season",
            },
        ],
    },
]

minor_settings_dict = [
    {
        "title": "Substitute Sunday/Holy Day (Eucharistic) Lectionary",
        "name": "lectionary",
        "help_text": "On Sundays and major holy days, do you want to use the standard Daily Office readings or substitute the 3-year Sunday/Holy Day cycle? When the Daily Office is used for the principal service of a church, the prayer book instructs you to replace the Daily Office readings with the three year cycle of Sunday and Holy Day readings.  This is generally done only in churches and not when using the Daily Office as a personal devotion at home.",
        "options": [
            {
                "value": "daily-office-readings",
                "hide": ["mass-readings-feria", "mass-readings-sunday"],
                "show": ["daily-office-readings-sunday", "daily-office-readings-feria"],
                "heading": "Standard Daily Office",
                "text": "",
                "tags": {},
            },
            {
                "value": "mass-readings",
                "hide": ["mass-reading-feria", "daily-office-readings-sunday"],
                "show": ["mass-readings-sunday", "mass-readingss-feria"],
                "heading": "Sundays & Holy Days",
                "text": "",
                "tags": {},
            },
        ],
    },
    {
        "title": "Confession Intro Length",
        "name": "confession",
        "help_text": "Use either the short or long exhortation before the confession.",
        "options": [
            {
                "value": "long-on-fast",
                "hide": ["confession-long-form", "confession-short-form"],
                "show": ["confession-fast-only"],
                "heading": "Long Intro Only on Fast Days",
                "text": "The long form of the intro and absolution are used only on fast days",
            },
            {
                "value": "short",
                "hide": ["confession-fast-only", "confession-long-form"],
                "show": ["confession-short-form"],
                "heading": "Short Intro Always",
                "text": "The short form of the intro and absolution are used every day",
            },
            {
                "value": "long",
                "hide": ["confession-fast-only", "confession-short-form"],
                "show": ["confession-long-form"],
                "heading": "Long Intro Always",
                "text": "The long form of the intro and absolution are used every day",
            },
        ],
    },
    {
        "title": "Absolution Style",
        "name": "absolution",
        "help_text": "After the confession, read an absolution suitable for a priest or a prayer suitable for a deacon or lay person.",
        "options": [
            {
                "value": "lay",
                "hide": ["priest"],
                "show": ["lay"],
                "heading": "Deacon or Lay Person",
                "text": "A prayer suitable for a deacon or lay person to read",
            },
            {
                "value": "priest",
                "hide": ["lay"],
                "show": ["priest"],
                "heading": "Priest or Bishop",
                "text": "An absolution suitable for a priest to pronounce",
            },
        ],
    },
    {
        "title": "Morning Prayer Invitatory",
        "name": "morning_prayer_invitatory",
        "help_text": "Open with the Venite (Psalm 95) always (traditional), have a special celebratory invitatory on Sundays and feasts (Pascha Nostrum during Eastertide or Jubilate/Psalm 100 otherwise), or rotate between the normal and celebratory invitatory each day. Regardless of which setting you choose, the Pascha Nostrum is always used during the first week of Easter, and the invitatory will never be the same as one of the day's appointed psalms.",
        "options": [
            {
                "value": "invitatory_traditional",
                "hide": [
                    "invitatory_jubilate_on_feasts",
                    "invitatory_rotating",
                    "invitatory_celebratory_always",
                ],
                "show": ["invitatory_traditional"],
                "heading": "Venite always",
                "text": "Always use the Venite (except on days when Pslam 95 is appointed)",
            },
            {
                "value": "invitatory_jubilate_on_feasts",
                "hide": ["invitatory_traditional", "invitatory_rotating", "invitatory_celebratory_always"],
                "show": ["invitatory_jubilate_on_feasts"],
                "heading": "Celebratory Sundays and feasts",
                "text": "Use the Jubilate on Feasts and Sundays, Venite on other days ",
            },
            {
                "value": "invitatory_rotating",
                "hide": [
                    "invitatory_traditional",
                    "invitatory_jubilate_on_feasts",
                    "invitatory_celebratory_always",
                ],
                "show": ["invitatory_rotating"],
                "heading": "Rotating each day",
                "text": "Rotate between the Venite and Jubilate",
            },
            {
                "value": "celebratory_always",
                "hide": ["invitatory_traditional", "invitatory_jubilate_on_feasts", "invitatory_rotating"],
                "show": ["invitatory_celebratory_always"],
                "heading": "Celebratory Always",
                "text": "Always use the Jubilate (or Pascha Nostrum, in Eastertide)",
            },
        ],
    },
    {
        "title": "Reading Headings",
        "name": "reading_headings",
        "help_text": "Show or hide headings from the English Standard Version of the Bible in scripture readings ",
        "options": [
            {
                "value": "off",
                "hide": ["reading-heading"],
                "show": [],
                "heading": "Hide",
                "text": "Hide ESV headings in readings",
            },
            {
                "value": "on",
                "hide": [],
                "show": ["reading-heading"],
                "heading": "Show",
                "text": "Show ESV headings in readings",
            },
        ],
    },
    {
        "title": "Language Style for Prayers",
        "name": "language_style",
        "help_text": "Traditional and contemporary language options are available for the Kyrie (Lord have mercy) and the Lord's Prayer",
        "options": [
            {
                "value": "traditional",
                "hide": ["contemporary"],
                "show": ["traditional"],
                "heading": "Traditional",
                "text": "Traditional language for the Kyrie and Our Father",
            },
            {
                "value": "contemporary",
                "hide": ["traditional"],
                "show": ["contemporary"],
                "heading": "Contemporary",
                "text": "Modern language for the Kyrie and Our Father",
            },
        ],
    },
    {
        "title": "National Holiday Collects",
        "name": "national_holidays",
        "help_text": "Show country-specific commemorations for the United States, Canada, or both.",
        "options": [
            {
                "value": "all",
                "hide": ["national_none"],
                "show": ["canada", "us", "election"],
                "heading": "All",
                "text": "Both U.S. and Canadian Holidays",
            },
            {
                "value": "us",
                "hide": ["canada", "national_none"],
                "show": ["us", "election"],
                "heading": "United States",
                "text": "United States Holidays",
            },
            {
                "value": "canada",
                "hide": ["us", "national_none", "election"],
                "show": ["canada"],
                "heading": "Canada",
                "text": "Canadian Holidays",
            },
            {
                "value": "national_none",
                "hide": ["us", "canada"],
                "show": ["national_none", "election"],
                "heading": "None",
                "text": "No Holidays",
            },
        ],
    },
    {
        "title": "Evening Prayer Suffrages",
        "name": "suffrages",
        "help_text": "Choose which set of short prayers to be used each evening",
        "options": [
            {
                "value": "rotating",
                "hide": ["suffrages-a", "suffrages-b"],
                "show": ["suffrages-rotating"],
                "heading": "Rotating",
                "text": "Rotate between the traditional and new set each day",
            },
            {
                "value": "traditional",
                "hide": ["suffrages-b", "suffrages-rotating"],
                "show": ["suffrages-a"],
                "heading": "Traditional",
                "text": "Always use the traditional set (same as Morning Prayer)",
            },
            {
                "value": "new",
                "hide": ["suffrages-a", "suffrages-rotating"],
                "show": ["suffrages-b"],
                "heading": "New",
                "text": 'Always use the newer set, each ending with "We entreat you, O Lord"',
            },
        ],
    },
    {
        "title": "Additional Collects",
        "name": "collects",
        "help_text": "Use a different collect for each day of the week, or use the same two collects (from the classic prayer books) each day.",
        "options": [
            {
                "value": "rotating",
                "hide": ["fixed"],
                "show": ["rotating"],
                "heading": "Rotating",
                "text": "A different collect is said for each day of the week",
            },
            {
                "value": "fixed",
                "hide": ["rotating"],
                "show": ["fixed"],
                "heading": "Fixed",
                "text": "The two traditional collects are said every day",
            },
        ],
    },
    {
        "title": "Prayers in the Time of Pandemic",
        "name": "pandemic_prayers",
        "help_text": "Include a rotating set of collects for the duration of this pandemic",
        "options": [
            {
                "value": "pandemic_yes",
                "hide": [],
                "show": ["pandemic_prayers"],
                "heading": "On",
                "text": "Include extra collects during the pandemic",
            },
            {
                "value": "pandemic_no",
                "hide": ["pandemic_prayers"],
                "show": [],
                "heading": "Off",
                "text": "Do not include extra collects during the pandemic",
            },
        ],
    },
    {
        "title": "Great Litany at Morning Prayer",
        "name": "mp_great_litany",
        "help_text": "Include the Great Litany after the collects at Morning Prayer",
        "options": [
            {
                "value": "mp_litany_off",
                "hide": ["litany-mp-wfs", "litany-mp-not-wfs"],
                "show": ["mission-mp-wfs", "mission-mp-not-wfs"],
                "heading": "Off",
                "text": "Do not use the litany",
            },
            {
                "value": "mp_litany_w_f_s",
                "hide": ["litany-mp-not-wfs", "mission-mp-wfs"],
                "show": ["litany-mp-wfs", "mission-mp-not-wfs"],
                "heading": "Wed, Fri, & Sun.",
                "text": "Litany on Wednesday, Friday, and Sunday (the traditional days)",
            },
            {
                "value": "mp_litany_everyday",
                "hide": ["mission-mp-wfs", "mission-mp-not-wfs"],
                "show": ["litany-mp-wfs", "litany-mp-not-wfs"],
                "heading": "Everyday",
                "text": "Litany every day",
            },
        ],
    },
    {
        "title": "Great Litany at Evening Prayer",
        "name": "ep_great_litany",
        "help_text": "Include the Great Litany after the collects at Evening Prayer",
        "options": [
            {
                "value": "ep_litany_off",
                "hide": ["litany-ep-wfs", "litany-ep-not-wfs"],
                "show": ["mission-ep-wfs", "mission-ep-not-wfs"],
                "heading": "Off",
                "text": "Do not use the litany",
            },
            {
                "value": "ep_litany_w_f_s",
                "hide": ["litany-ep-not-wfs", "mission-ep-wfs"],
                "show": ["litany-ep-wfs", "mission-ep-not-wfs"],
                "heading": "Wed, Fri, & Sun.",
                "text": "Litany on Wednesday, Friday, and Sunday (the traditional days)",
            },
            {
                "value": "ep_litany_everyday",
                "hide": ["mission-ep-wfs", "mission-ep-not-wfs"],
                "show": ["litany-ep-wfs", "litany-ep-not-wfs"],
                "heading": "Everyday",
                "text": "Litany every day",
            },
        ],
    },
    {
        "title": "General Thanksgiving",
        "name": "general_thanksgiving",
        "help_text": "Pray the General Thanksgiving at the end of Morning and Evening Prayer",
        "options": [
            {
                "value": "on",
                "hide": [],
                "show": ["general_thanksgiving"],
                "heading": "On",
                "text": "Add the prayer of general thanksgiving at the end of the office",
            },
            {
                "value": "off",
                "hide": ["general_thanksgiving"],
                "show": [""],
                "heading": "Off",
                "text": "Hide the prayer of general thanksgiving at the end of the office",
            },
        ],
    },
    {
        "title": "Prayer of St. John Chrysostom",
        "name": "chrysostom",
        "help_text": "Pray the Prayer of St. John Chrysostom at the end of Morning and Evening Prayer.  This prayer is suitable when praying in a group.",
        "options": [
            {
                "value": "on",
                "hide": [],
                "show": ["chrysostom"],
                "heading": "On",
                "text": "For use when praying in groups of two or more",
            },
            {
                "value": "off",
                "hide": ["chrysostom"],
                "show": [""],
                "heading": "Off",
                "text": "For when praying individually",
            },
        ],
    },
    {
        "title": "The Grace",
        "name": "grace",
        "help_text": "Rotate each day through the three provided conclusions, or always use the same one from the classic prayer books.",
        "options": [
            {
                "value": "rotating",
                "hide": ["fixed-grace"],
                "show": ["rotating-grace"],
                "heading": "Rotating",
                "text": "Rotate through three different verses daily",
            },
            {
                "value": "traditional",
                "hide": ["rotating-grace"],
                "show": ["fixed-grace"],
                "heading": "Traditional",
                "text": "Conclude with the traditional grace each day",
            },
        ],
    },
    {
        "title": 'Advent "O" Antiphons',
        "name": "o_antiphons",
        "help_text": 'The traditional "O" Antiphons are used before and after the first canticle in Evening Prayer during the last eight days of Advent. You can use literal translations of the original Latin, or the familiar paraphrases used in the hymn "O Come, O Come Emmanuel"',
        "options": [
            {
                "value": "literal",
                "hide": ["antiphon_paraphrase, antiphon_latin"],
                "show": ["antiphon_literal"],
                "heading": "Literal",
                "text": "Literal translation of the original Latin",
            },
            {
                "value": "paraphrase",
                "hide": ["antiphon_literal, antiphon_latin"],
                "show": ["antiphon_paraphrase"],
                "heading": "Hymnal",
                "text": mark_safe("Paraphrase used in, <em>O Come, O Come Emmanuel</em>"),
            },
            {
                "value": "latin",
                "hide": ["antiphon_paraphrase, antiphon_literal"],
                "show": ["antiphon_latin"],
                "heading": "Latin",
                "text": "Original Latin",
            },
            {
                "value": "none",
                "hide": ["antiphon_paraphrase, antiphon_latin", "antiphon_literal"],
                "show": [""],
                "heading": "None",
                "text": "Hide the antiphons",
            },
        ],
    },
]
family_settings_dict = [
    {
        "title": "Readings",
        "name": "family_readings",
        "help_text": "",
        "options": [
            {
                "value": "brief",
                "hide": ["family-reading-long"],
                "show": ["family-reading-brief"],
                "heading": "Brief",
                "text": "A brief scripture reading appointed for the time of day",
            },
            {
                "value": "long",
                "hide": ["family-reading-brief"],
                "show": ["family-reading-long"],
                "heading": "Long",
                "text": "A longer scripture reading from the continuous lectionary",
            },
        ],
    },
    {
        "title": "Reading Audio",
        "name": "family_reading_audio",
        "help_text": "Show or hide an audio player to listen to the scripture readings during Morning and Evening Prayer.  Audio is provided by esv.org and currently does not include the Deuterocanon/Apocrypha.",
        "options": [
            {
                "value": "off",
                "hide": ["family-bible-audio"],
                "show": [],
                "heading": "Disable Audio",
                "text": "No audio controls for scripture readings",
            },
            {
                "value": "on",
                "hide": [],
                "show": ["family-bible-audio"],
                "heading": "Enable Audio",
                "text": "Enable audio player for scripture readings",
            },
        ],
    },
    {
        "title": "Collect",
        "name": "family_collect",
        "help_text": "",
        "options": [
            {
                "value": "time_of_day",
                "hide": ["collect-day-of-year", "collect-day-of-week"],
                "show": ["collect-time-of-day"],
                "heading": "By Time of Day",
                "text": "The prayer appointed for the time of day from Family Prayer",
            },
            {
                "value": "day_of_week",
                "hide": ["collect-day-of-year", "collect-time-of-day"],
                "show": ["collect-day-of-week"],
                "heading": "By Day of Week",
                "text": "The prayer appointed for the day of the week from the Daily Office",
            },
            {
                "value": "day_of_year",
                "hide": ["collect-day-of-week", "collect-time-of-day"],
                "show": ["collect-day-of-year"],
                "heading": "By Day of the Year",
                "text": "The prayer appointed for the specific day of the year (or the previous Sunday if there is no feast)",
            },
        ],
    },
]
family_minor_settings_dict = [
    {
        "title": "Opening Sentence",
        "name": "family-opening-sentence",
        "help_text": "Use the same opening sentences each day based on the time of the day, or use the seasonal options from the Daily Office",
        "options": [
            {
                "value": "family-opening-sentence-fixed",
                "hide": ["opening-seasonal"],
                "show": ["opening-fixed"],
                "heading": "Fixed by Time of Day",
                "text": "No creed",
            },
            {
                "value": "family-opening-sentence-seasonal",
                "hide": ["opening-fixed"],
                "show": ["opening-seasonal"],
                "heading": "Seasonal",
                "text": "Include Creed",
            },
        ],
    },
    {
        "title": "Apostles' Creed",
        "name": "family-creed",
        "help_text": "Include the Apostle's Creed before the prayers during 'In the Morning' and 'In the Early Evening' Family Prayer",
        "options": [
            {
                "value": "family-creed-no",
                "hide": ["family-creed"],
                "show": [],
                "heading": "No",
                "text": "No creed",
            },
            {
                "value": "family-creed-yes",
                "hide": [],
                "show": ["family-creed"],
                "heading": "Yes",
                "text": "Include Creed",
            },
        ],
    },
]


def settings(request):
    return {
        "mode": MODE,
        "filename": "index.html" if MODE == "app" else "",
        "app_version": APP_VERSION,
        "on": get_on(request.path),
        "show_settings_class": "" if get_on(request.path) == "settings-button" else "off",
        "family": "family" in request.path,
        "settings": settings_dict,
        "minor_settings": minor_settings_dict,
        "family_settings": family_settings_dict,
        "family_minor_settings": family_minor_settings_dict,
    }

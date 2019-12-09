from django.utils.safestring import mark_safe

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

def settings(request):
    return {
        "on": get_on(request.path),
        "show_settings_class": "" if get_on(request.path) == "settings-button" else "off",
        "settings": [
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
                "title": "Psalter Cycle",
                "name": "psalter",
                "help_text": mark_safe("During Morning and Evening Prayer, pray through all the Psalms either every <strong>60 days</strong> (fewer psalms per day) or once every <strong>30 days</strong> (more psalms per day)."),
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
                "help_text": mark_safe("Read through most of the Bible during Morning and Evening Prayer every <strong>1 year</strong> or every <strong>2 years</strong>.  The one year cycle is best if you do <strong>both</strong> Morning and Evening prayer daily; the two year cycle is best if you do only one."),
                "options": [
                    {
                        "value": "1",
                        "hide": ["alternate-reading"],
                        "show": ["main-reading"],
                        "heading": "One Year",
                        "text": mark_safe(
                            "Read through most of the Bible each year. (Use if you pray <strong>both</strong> Morning and Evening Prayer)"),
                    },
                    {
                        "value": "2",
                        "hide": ["main-reading"],
                        "show": ["alternate-reading"],
                        "heading": "Two Year",
                        "text": mark_safe(
                            "Read through most of the Bible in two years. (Use if you pray <strong>either</strong> Morning <strong>or</strong> Evening prayer)"),
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
                        "hide": ["abbreviated-reading"],
                        "show": ["full-reading"],
                        "heading": "Full",
                        "text": "The full readings will always be used.",
                    },
                    {
                        "value": "abbreviated",
                        "hide": ["full-reading"],
                        "show": ["abbreviated-reading"],
                        "heading": "Abbreviated",
                        "text": "Suggested abbreviations, when available.",
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
                        "text": "Turn on audio player for scripture readings (Apocrypha not available yet)",
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
                        "hide": [],
                        "show": ["canada", "us"],
                        "heading": "All",
                        "text": "Both U.S. and Canadian Holidays",
                    },
                    {
                        "value": "us",
                        "hide": ["canada"],
                        "show": ["us"],
                        "heading": "United States",
                        "text": "United States Holidays",
                    },
                    {
                        "value": "canada",
                        "hide": ["us"],
                        "show": ["canada"],
                        "heading": "Canada",
                        "text": "Canadian Holidays",
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
                    }
                ],
            },
            {
                "title": 'Advent "O" Antiphons',
                "name": "o_antiphons",
                "help_text": "The traditional \"O\" Antiphons are used before and after the first canticle in Evening Prayer during the last eight days of Advent. You can use literal translations of the original Latin, or the familiar paraphrases used in the hymn \"O Come, O Come Emmanuel\"",
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
    }

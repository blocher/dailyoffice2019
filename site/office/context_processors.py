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
                "title": "Psalter Cycle",
                "name": "psalter",
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
                "options": [
                    {
                        "value": "1",
                        "hide": ["alternate-reading"],
                        "show": ["main-reading"],
                        "heading": "One Year",
                        "text": mark_safe(
                            "Read through most of the bible each year. (Use if you pray <strong>both</strong> morning and evening prayer)"),
                    },
                    {
                        "value": "2",
                        "hide": ["main-reading"],
                        "show": ["alternate-reading"],
                        "heading": "Two Year",
                        "text": mark_safe(
                            "Read through most of the bible in two years. (Use if you pray <strong>either</strong> morning <strong>or</strong> evening prayer)"),
                    },
                ],
            },
            {
                "title": "Reading Length",
                "name": "reading_length",
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
                "title": "Language Style",
                "name": "language_style",
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
                "title": "Collects",
                "name": "collects",
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
                "title": "Absolution",
                "name": "absolution",
                "options": [
                    {
                        "value": "lay",
                        "hide": ["priest"],
                        "show": ["lay"],
                        "heading": "Lay Person",
                        "text": "A prayer suitable for a deacon or lay person to read",
                    },
                    {
                        "value": "priest",
                        "hide": ["lay"],
                        "show": ["priest"],
                        "heading": "Priest",
                        "text": "An absolution suitable for a priest to pronounce",
                    },
                ],
            },
            {
                "title": "General Thanksgiving",
                "name": "general_thanksgiving",
                "options": [
                    {
                        "value": "on",
                        "hide": [],
                        "show": ["general_thanksgiving"],
                        "heading": "On",
                        "text": "Add the prayer of general thanksgiving to the end of the office",
                    },
                    {
                        "value": "off",
                        "hide": ["general_thanksgiving"],
                        "show": [""],
                        "heading": "Off",
                        "text": "Hide the prayer of general thanksgiving to the end of the office",
                    },
                ],
            },
            {
                "title": "Prayer of St. John Chrysostom",
                "name": "chrysostom",
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
                "title": "National Holidays",
                "name": "national_holidays",
                "options": [
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
                    {
                        "value": "all",
                        "hide": [],
                        "show": ["canada", "us"],
                        "heading": "All",
                        "text": "Both U.S. and Canadian Holidays",
                    },
                ],
            },
            {
                "title": 'Advent "O" Antiphons',
                "name": "o_antiphons",
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

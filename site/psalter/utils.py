from django.utils.html import format_html

from office.api.line import Line
from psalter.models import PsalmVerse


def parse_single_psalm(psalm):
    psalm = psalm.replace(" ", "").split(":")

    # e.g., 138
    if len(psalm) == 1:
        return psalm[0]

    # e.g., 138:1-10
    verses = psalm[1].split(",")
    if len(verses) == 1:
        return "{}:{}".format(psalm[0], psalm[1])

    # e.g., 138:1-10,12-14
    citations = []
    for verse in verses:
        citations.append("{}:{}".format(psalm[0], verse))
    return ",".join(citations)


def normalize_citations(citations):
    citations = str(citations)
    citations = citations.replace(" ", "").replace("or", ",").split(",")
    cleaned = []
    chapter = None
    for citation in citations:
        verses = None
        citation_parts = citation.split(":")
        if len(citation_parts) > 1:
            chapter = citation_parts[0]
            verses = citation_parts[1]
        elif "-" not in citation:
            chapter = citation
            cleaned.append(f"{chapter}")
        else:
            verses = citation
        if verses:
            cleaned.append(f"{chapter}:{verses}")

    return cleaned


def _psalm_has_language(verses, display_language):
    """Check if a majority of verses in a psalm have the target language.
    If so, we use that language for the entire psalm (no mixing)."""
    if display_language == "english":
        return False
    field = "first_half_spanish" if display_language == "spanish" else "first_half_chinese"
    total = len(verses)
    if total == 0:
        return False
    has_lang = sum(1 for v in verses if getattr(v, field, None))
    # Use non-English language if at least 50% of verses are available
    return has_lang >= total * 0.5


def _get_verse_text(verse, language_style, display_language, use_target_language=False):
    """Get the first_half and second_half text for a verse based on language settings.
    If use_target_language is True, use the target language and skip missing verses
    rather than falling back to English (prevents language mixing)."""
    if use_target_language:
        if display_language == "spanish":
            fh = verse.first_half_spanish
            sh = verse.second_half_spanish
            if fh:
                return fh, sh if sh else fh
            return None, None  # skip this verse entirely
        elif display_language in ("chinese-traditional", "chinese-simplified"):
            fh = verse.first_half_chinese
            sh = verse.second_half_chinese
            if fh:
                return fh, sh if sh else fh
            return None, None  # skip this verse entirely
    else:
        if display_language == "spanish":
            fh = verse.first_half_spanish
            sh = verse.second_half_spanish
            if fh:
                return fh, sh if sh else fh
        elif display_language in ("chinese-traditional", "chinese-simplified"):
            fh = verse.first_half_chinese
            sh = verse.second_half_chinese
            if fh:
                return fh, sh if sh else fh
    # Fall back to English
    if language_style == "traditional":
        return verse.first_half_tle, verse.second_half_tle
    return verse.first_half, verse.second_half


def _has_verse_text(verse, language_style, display_language, use_target_language=False):
    """Check if a verse has text for the given language settings."""
    if use_target_language:
        if display_language == "spanish":
            return bool(verse.first_half_spanish)
        if display_language in ("chinese-traditional", "chinese-simplified"):
            return bool(verse.first_half_chinese)
        # For English, always has text
    if display_language == "spanish" and verse.first_half_spanish:
        return True
    if display_language in ("chinese-traditional", "chinese-simplified") and verse.first_half_chinese:
        return True
    if language_style == "traditional":
        return bool(verse.first_half_tle)
    return bool(verse.first_half)


def get_psalms(
    citations, api=False, simplified_citations=False, language_style="contemporary",
    headings="whole_verse", display_language="english"
):
    citations = normalize_citations(citations)
    html = ""
    lines = []
    for citation in citations:
        citation_parts = citation.split(":")
        if len(citation_parts) > 1:
            start, end = citation_parts[1].split("-")
            verses = (
                PsalmVerse.objects.filter(psalm__number=citation_parts[0], number__gte=start, number__lte=end)
                .order_by("number")
                .select_related("psalm")
                .all()
            )
        else:
            verses = PsalmVerse.objects.filter(psalm__number=citation).order_by("number").select_related("psalm").all()
        html = html + psalm_html(
            citation,
            verses,
            simplified_citations=simplified_citations,
            language_style=language_style,
            headings=headings,
            display_language=display_language,
        )
        lines = lines + psalm_api_lines(
            citation, verses, language_style=language_style, headings=headings,
            display_language=display_language,
        )
    if api:
        return lines
    return html


def psalm_api_lines(citation, verses, heading=True, language_style="contemporary",
                    headings="whole_verse", display_language="english"):
    # Decide at the psalm level: use target language for all verses, or English for all
    use_target = _psalm_has_language(verses, display_language)

    lines = []
    if heading:
        if use_target:
            psalm_label = {"spanish": "Salmo", "chinese-traditional": "詩篇", "chinese-simplified": "詩篇"}.get(display_language, "Psalm")
        else:
            psalm_label = "Psalm"
        lines.append(Line("{} {}".format(psalm_label, citation), "heading"))
        lines.append(Line(verses[0].psalm.latin_title, "subheading"))

    filtered_verses = [v for v in verses if _has_verse_text(v, language_style, display_language, use_target)]

    for i, verse in enumerate(filtered_verses):
        first_half, second_half = _get_verse_text(verse, language_style, display_language, use_target)
        if first_half is None:
            continue

        if headings == "half_verse":
            style = "leader"
        elif headings in ["none", "unison"]:
            style = "congregation"
        else:  # whole_verse
            if i % 2 == 0:
                style = "leader"
            else:
                style = "congregation"
        lines.append(
            Line(
                "{} *".format(first_half),
                style,
                preface=verse.number,
                indented="hangingIndent",
            )
        )
        if headings == "half_verse":
            style = "congregation"
        elif headings in ["none", "unison"]:
            style = "congregation"
        else:  # whole_verse
            if i % 2 == 0:
                style = "leader"
            else:
                style = "congregation"
        lines.append(
            Line(
                second_half,
                style,
                indented="indent",
            )
        )
    return lines


def psalm_html(
    citation, verses, heading=True, simplified_citations=False, language_style="contemporary",
    headings="whole_verse", display_language="english"
):
    # Decide at the psalm level: use target language for all verses, or English for all
    use_target = _psalm_has_language(verses, display_language)

    if use_target:
        psalm_label = {"spanish": "Salmo", "chinese-traditional": "詩篇", "chinese-simplified": "詩篇"}.get(display_language, "Psalm")
    else:
        psalm_label = "Psalm"
    html = "<div class='psalm'>"
    if heading and simplified_citations:
        html = html + format_html("<h3>{}</h3>", citation)
    elif heading:
        html = html + format_html("<h3>{} {}</h3>", psalm_label, citation)
        html = html + format_html("<h4>{}</h4>", verses[0].psalm.latin_title)
    for i, verse in enumerate(verses):
        first_half, second_half = _get_verse_text(verse, language_style, display_language, use_target)
        if first_half and second_half:
            if headings == "half_verse":
                html = html + format_html(
                    "<p class='hanging-indent'><sup class='versenum'>{}</sup> {} <span class='asterisk'>*</span> </p>",
                    verse.number,
                    first_half,
                )
                html = html + format_html(
                    "<p class='indent'><strong>{}</strong></p>",
                    second_half,
                )
            elif headings in ["none", "unison"]:
                html = html + format_html(
                    "<p class='hanging-indent'><sup class='versenum'>{}</sup> {} <span class='asterisk'>*</span> </p>",
                    verse.number,
                    first_half,
                )
                html = html + format_html(
                    "<p class='indent'>{}</p>",
                    second_half,
                )
            else:  # whole_verse
                if (i % 2) == 0:
                    html = html + format_html(
                        "<p class='hanging-indent'><sup class='versenum'>{}</sup> {} <span class='asterisk'>*</span> </p>",
                        verse.number,
                        first_half,
                    )
                    html = html + format_html(
                        "<p class='indent'>{}</p>",
                        second_half,
                    )
                else:
                    html = html + format_html(
                        "<p class='hanging-indent'><sup class='versenum'>{}</sup> <strong>{}</strong> <span class='asterisk'>*</span> </p>",
                        verse.number,
                        first_half,
                    )
                    html = html + format_html(
                        "<p class='indent'><strong>{}</strong></p>",
                        second_half,
                    )
    html = html + "</div>"
    return html

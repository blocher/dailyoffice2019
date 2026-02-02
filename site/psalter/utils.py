from django.utils.html import format_html

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


def get_psalms(
    citations,
    api=False,
    simplified_citations=False,
    language_style="contemporary",
    headings="whole_verse",
    overall_language_style="contemporary",
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
        )
        lines = lines + psalm_api_lines(
            citation,
            verses,
            language_style=language_style,
            headings=headings,
            overall_language_style=overall_language_style,
        )
    if api:
        return lines
    return html


def psalm_api_lines(
    citation,
    verses,
    heading=True,
    language_style="contemporary",
    headings="whole_verse",
    overall_language_style="contemporary",
):
    from office.api.views import Line

    lines = []
    overall_title = "Psalm" if overall_language_style == "spanish" else "Salmo"
    if heading:
        lines.append(Line("{} {}".format(overall_title, citation), "heading"))
        lines.append(Line(verses[0].psalm.latin_title, "subheading"))
    if language_style == "traditional":
        verses = [verse for verse in verses if verse.first_half_tle]
    elif language_style == "spanish":
        verses = [verse for verse in verses if verse.first_half_spanish]
    else:
        verses = [verse for verse in verses if verse.first_half]
    for i, verse in enumerate(verses):
        if headings == "half_verse":
            style = "leader"
        elif headings in ["none", "unison"]:
            style = "congregation"
        else:  # whole_verse
            if i % 2 == 0:
                style = "leader"
            else:
                style = "congregation"

        first_half = verse.first_half
        if language_style == "traditional":
            first_half = verse.first_half_tle
        elif language_style == "spanish":
            first_half = verse.first_half_spanish

        lines.append(
            Line(
                "{} *".format(
                    first_half,
                ),
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

        second_half = verse.second_half
        if language_style == "traditional":
            second_half = verse.second_half_tle
        elif language_style == "spanish":
            second_half = verse.second_half_spanish

        lines.append(
            Line(
                second_half,
                style,
                indented="indent",
            )
        )
    return lines


def psalm_html(
    citation, verses, heading=True, simplified_citations=False, language_style="contemporary", headings="whole_verse"
):
    html = "<div class='psalm'>"
    if heading and simplified_citations:
        html = html + format_html("<h3>{}</h3>", citation)
    elif heading:
        html = html + format_html("<h3>Psalm {}</h3>", citation)
        html = html + format_html("<h4>{}</h4>", verses[0].psalm.latin_title)
    for i, verse in enumerate(verses):
        first_half = verse.first_half
        second_half = verse.second_half
        if language_style == "traditional":
            first_half = verse.first_half_tle
            second_half = verse.second_half_tle
        elif language_style == "spanish":
            first_half = verse.first_half_spanish
            second_half = verse.second_half_spanish

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
    # html = html + format_html("<p  class='hanging-indent'>&nbsp;</p>")
    # html = html + format_html(
    #     "<p class='hanging-indent'><strong>Glory be to the Father, and to the Son, and to the Holy Spirit; *</strong></p>"
    # )
    # html = html + format_html(
    #     "<p class='indent'><strong>as it was in the beginning, is now, and ever shall be, world without end. Amen.</strong></p>"
    # )

    return html

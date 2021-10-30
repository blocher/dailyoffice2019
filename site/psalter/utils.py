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


def get_psalms(citations, api=False):
    citations = str(citations)
    citations = citations.replace(" ", "").split(",")
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
        html = html + psalm_html(citation, verses)
        lines = lines + psalm_api_lines(citation, verses)
    if api:
        return lines
    return html


def psalm_api_lines(citation, verses, heading=True):
    from office.api.views import Line

    lines = []
    if heading:
        lines.append(Line(citation, "heading"))
        lines.append(Line(verses[0].psalm.latin_title, "subheading"))
    for verse in verses:
        lines.append(
            Line(
                "{} {} *".format(
                    verse.number,
                    verse.first_half,
                    verse.number,
                    verse.first_half,
                ),
                "leader",
            )
        )
        lines.append(Line(verse.second_half, "congregation"))
    return lines


def psalm_html(citation, verses, heading=True):
    html = ""
    if heading:
        html = format_html("<h3>Psalm {}</h3>", citation)
        html = html + format_html("<h4>{}</h4>", verses[0].psalm.latin_title)
    for verse in verses:
        html = html + format_html(
            "<p class='hanging-indent'><sup class='versenum'>{}</sup> {}<span class='asterisk'>*</span> </p>",
            verse.number,
            verse.first_half,
        )
        html = html + format_html("<p class='indent'><strong>{}</strong></p>", verse.second_half)
    # html = html + format_html("<p  class='hanging-indent'>&nbsp;</p>")
    # html = html + format_html(
    #     "<p class='hanging-indent'><strong>Glory be to the Father, and to the Son, and to the Holy Spirit; *</strong></p>"
    # )
    # html = html + format_html(
    #     "<p class='indent'><strong>as it was in the beginning, is now, and ever shall be, world without end. Amen.</strong></p>"
    # )

    return html

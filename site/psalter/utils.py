from django.utils.html import format_html

from psalter.models import PsalmVerse


def get_psalms(citations):
    citations = citations.replace(" ", "").split(",")
    html = ""
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
    return html


def psalm_html(citation, verses):
    html = format_html("<h3>Psalm {}</h3>", citation)
    html = html + format_html("<h4>{}</h4>", verses[0].psalm.latin_title)
    for verse in verses:
        html = html + format_html(
            "<p class='hanging-indent'><sup class='versenum'>{}</sup> {}<span class='asterisk'>*</span> </p>",
            verse.number,
            verse.first_half,
        )
        html = html + format_html("<p class='indent'><strong>{}</strong></p>", verse.second_half)
    html = html + format_html("<p  class='hanging-indent'>&nbsp;</p>")
    html = html + format_html(
        "<p class='hanging-indent'><strong>Glory be to the Father, and to the Son, and to the Holy Spirit; *</strong></p>"
    )
    html = html + format_html(
        "<p class='indent'><strong>as it was in the beginning, is now, and ever shall be, world without end. Amen.</strong></p>"
    )

    return html

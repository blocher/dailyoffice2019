from datetime import date

from bs4 import BeautifulSoup
from django.core import serializers
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from docx.shared import RGBColor
from icalendar import Calendar, Event
from meta.views import Meta

from churchcal.calculations import ChurchYear
from churchcal.models import Season, SanctoraleCommemoration
from office.compline import Compline
from office.evening_prayer import EveningPrayer
from office.family_close_of_day import FamilyCloseOfDay
from office.family_early_evening import FamilyEarlyEvening
from office.family_midday import FamilyMidday
from office.family_morning import FamilyMorning
from office.midday_prayer import MiddayPrayer
from office.models import AboutItem, UpdateNotice, StandardOfficeDay, HolyDayOfficeDay
from office.morning_prayer import MorningPrayer
from office.offices import Office
from office.utils import passage_to_citation, testament_to_closing, testament_to_closing_response
from psalter.models import PsalmTopic, Psalm, PsalmVerse, PsalmTopicPsalm
from psalter.utils import get_psalms
from website.settings import (
    FIRST_BEGINNING_YEAR,
    LAST_BEGINNING_YEAR,
    MODE,
    FIRST_BEGINNING_YEAR_APP,
    LAST_BEGINNING_YEAR_APP,
)

generic_title = "The Daily Office | Morning and Evening Prayer according to the Book of Common Prayer (2019)"
generic_description = "This site invites you to join with Christians around the world in praying with the Church, at any time or in any place you may find yourself. It makes it easy to pray daily morning, midday, evening, and compline (bedtime) prayer without flipping pages, searching for scripture readings or calendars, or interpreting rubrics. The prayers are presented from <em><em>The Book of Common Prayer (2019)</em></em> of the Anglican Church in North America  (ACNA) and reflect the ancient patterns of daily prayer Christians have used since the earliest days of the church."
meta_defaults = {
    "title": generic_title,
    "og_title": generic_title,
    "twitter_title": generic_title,
    "gplus_title": generic_title,
    "description": generic_description,
    "og_description": generic_description,
    "url": "https://www.dailyoffice2019.com",
    "image": static("office/img/bcp_evening_prayer.jpg"),
    "image_width": 5897,
    "image_height": 3931,
    "object_type": "website",
    "site_name": generic_title,
    "extra_props": {
        "twitter:image": static("office/img/bcp_evening_prayer.jpg"),
        "twitter:card": "summary_large_image",
        "twitter:site": "@dailyoffice2019",
    },
    "extra_custom_props": [("http-equiv", "Content-Type", "text/html; charset=UTF-8")],
}
meta = Meta(**meta_defaults)


def morning_prayer(request, year, month, day):
    mp = MorningPrayer("{}-{}-{}".format(year, month, day))
    mp_meta = meta_defaults.copy()
    mp_meta["title"] = mp_meta["og_title"] = mp_meta["twitter_title"] = mp_meta["gplus_title"] = mp.title
    mp_meta["description"] = mp.description
    mp_meta["url"] = reverse("morning_prayer", kwargs={"year": year, "month": month, "day": day})
    mp_meta["image"] = static("office/img/bcp.jpg")
    mp_meta["image_width"] = 1000
    mp_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": mp, "meta": Meta(**mp_meta)})


def evening_prayer(request, year, month, day):
    ep = EveningPrayer("{}-{}-{}".format(year, month, day))
    ep_meta = meta_defaults.copy()
    ep_meta["title"] = ep_meta["og_title"] = ep_meta["twitter_title"] = ep_meta["gplus_title"] = ep.title
    ep_meta["description"] = ep.description
    ep_meta["url"] = reverse("evening_prayer", kwargs={"year": year, "month": month, "day": day})
    return render(request, "office/office.html", {"office": ep, "meta": Meta(**ep_meta)})


def compline(request, year, month, day):
    cp = Compline("{}-{}-{}".format(year, month, day))
    compline_meta = meta_defaults.copy()
    compline_meta["title"] = compline_meta["og_title"] = compline_meta["twitter_title"] = compline_meta[
        "gplus_title"
    ] = cp.title
    compline_meta["description"] = cp.description
    compline_meta["url"] = reverse("compline", kwargs={"year": year, "month": month, "day": day})
    compline_meta["image"] = static("office/img/bcp.jpg")

    compline_meta["image_width"] = 1000
    compline_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": cp, "meta": Meta(**compline_meta)})


def midday_prayer(request, year, month, day):
    md = MiddayPrayer("{}-{}-{}".format(year, month, day))
    midday_meta = meta_defaults.copy()
    midday_meta["title"] = midday_meta["og_title"] = midday_meta["twitter_title"] = midday_meta[
        "gplus_title"
    ] = md.title
    midday_meta["description"] = md.description
    midday_meta["url"] = reverse("midday_prayer", kwargs={"year": year, "month": month, "day": day})
    midday_meta["image"] = static("office/img/bcp.jpg")
    midday_meta["image_width"] = 1000
    midday_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": md, "meta": Meta(**midday_meta)})


def family_morning_prayer(request, year, month, day):
    fm = FamilyMorning("{}-{}-{}".format(year, month, day))
    family_morning_meta = meta_defaults.copy()
    family_morning_meta["title"] = family_morning_meta["og_title"] = family_morning_meta[
        "twitter_title"
    ] = family_morning_meta["gplus_title"] = fm.title
    family_morning_meta["description"] = fm.description
    family_morning_meta["url"] = reverse("family_morning_prayer", kwargs={"year": year, "month": month, "day": day})
    family_morning_meta["image"] = static("office/img/bcp.jpg")
    family_morning_meta["image_width"] = 1000
    family_morning_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": fm, "meta": Meta(**family_morning_meta)})


def family_midday_prayer(request, year, month, day):
    fm = FamilyMidday("{}-{}-{}".format(year, month, day))
    family_morning_meta = meta_defaults.copy()
    family_morning_meta["title"] = family_morning_meta["og_title"] = family_morning_meta[
        "twitter_title"
    ] = family_morning_meta["gplus_title"] = fm.title
    family_morning_meta["description"] = fm.description
    family_morning_meta["url"] = reverse("family_midday_prayer", kwargs={"year": year, "month": month, "day": day})
    family_morning_meta["image"] = static("office/img/bcp.jpg")
    family_morning_meta["image_width"] = 1000
    family_morning_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": fm, "meta": Meta(**family_morning_meta)})


def family_early_evening_prayer(request, year, month, day):
    fm = FamilyEarlyEvening("{}-{}-{}".format(year, month, day))
    family_morning_meta = meta_defaults.copy()
    family_morning_meta["title"] = family_morning_meta["og_title"] = family_morning_meta[
        "twitter_title"
    ] = family_morning_meta["gplus_title"] = fm.title
    family_morning_meta["description"] = fm.description
    family_morning_meta["url"] = reverse(
        "family_early_evening_prayer", kwargs={"year": year, "month": month, "day": day}
    )
    family_morning_meta["image"] = static("office/img/bcp.jpg")
    family_morning_meta["image_width"] = 1000
    family_morning_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": fm, "meta": Meta(**family_morning_meta)})


def family_close_of_day_prayer(request, year, month, day):
    fm = FamilyCloseOfDay("{}-{}-{}".format(year, month, day))
    family_morning_meta = meta_defaults.copy()
    family_morning_meta["title"] = family_morning_meta["og_title"] = family_morning_meta[
        "twitter_title"
    ] = family_morning_meta["gplus_title"] = fm.title
    family_morning_meta["description"] = fm.description
    family_morning_meta["url"] = reverse(
        "family_close_of_day_prayer", kwargs={"year": year, "month": month, "day": day}
    )
    family_morning_meta["image"] = static("office/img/bcp.jpg")
    family_morning_meta["image_width"] = 1000
    family_morning_meta["image_height"] = 1333
    return render(request, "office/office.html", {"office": fm, "meta": Meta(**family_morning_meta)})


def settings(request):
    settings_meta = meta_defaults.copy()
    settings_meta["title"] = settings_meta["og_title"] = settings_meta["twitter_title"] = settings_meta[
        "gplus_title"
    ] = "Daily Office Settings | {}".format(generic_title)
    settings_meta["url"] = reverse("settings")
    return render(
        request, "office/settings.html", {"h1": True, "title": "Daily Office Settings", "meta": Meta(**settings_meta)}
    )


def family_settings(request):
    settings_meta = meta_defaults.copy()
    settings_meta["title"] = settings_meta["og_title"] = settings_meta["twitter_title"] = settings_meta[
        "gplus_title"
    ] = "Family Prayer Settings | {}".format(generic_title)
    settings_meta["url"] = reverse("settings")
    return render(
        request,
        "office/settings.html",
        {"h1": True, "title": "Family Prayer Settings", "meta": Meta(**settings_meta), "family": True},
    )


def signup_thank_you(request):
    settings_meta = meta_defaults.copy()
    settings_meta["title"] = settings_meta["og_title"] = settings_meta["twitter_title"] = settings_meta[
        "gplus_title"
    ] = "Thank you | {}".format(generic_title)
    settings_meta["url"] = reverse("settings")
    return render(request, "office/signup_thank_you.html", {"h1": True, "meta": Meta(**settings_meta)})


def church_year(request, start_year, end_year=None, family=False):
    church_year = ChurchYear(start_year)
    months = []
    for date_str, date in church_year.dates.items():
        month = date.date.strftime("%b %Y")
        if month not in months:
            months.append(month)

    seasons = Season.objects.filter(calendar__abbreviation="ACNA_BCP2019").order_by("order").all()

    year_meta = meta_defaults.copy()
    year_meta["title"] = year_meta["og_title"] = year_meta["twitter_title"] = year_meta[
        "gplus_title"
    ] = "Calendar for liturgical year {}-{} | {}".format(start_year, start_year + 1, generic_title)
    year_meta[
        "description"
    ] = "Start date: {}, End date: {}, Calendar for liturgical year {}-{} according to the use of the Anglican Church in North America including links to Morning Prayer, Midday Prayer, Evening Prayer, and Compline".format(
        "{dt:%A} {dt:%B} {dt.day}, {dt.year}".format(dt=church_year.start_date),
        "{dt:%A} {dt:%B} {dt.day}, {dt.year}".format(dt=church_year.end_date),
        start_year,
        start_year + 1,
    )
    year_meta["url"] = reverse("church_year", kwargs={"start_year": start_year, "end_year": end_year})
    return render(
        request,
        "office/church_year.html",
        {
            "hide_previous": start_year == FIRST_BEGINNING_YEAR
            if MODE == "web"
            else start_year == FIRST_BEGINNING_YEAR_APP,
            "hide_next": start_year == LAST_BEGINNING_YEAR if MODE == "web" else start_year == LAST_BEGINNING_YEAR_APP,
            "start_year": start_year,
            "end_year": start_year + 1,
            "church_year": church_year,
            "seasons": seasons,
            "months": months,
            "meta": Meta(**year_meta),
            "family": family,
        },
    )


def church_year_family(request, start_year, end_year=None):
    return church_year(request, start_year, end_year, family=True)


def about(request):
    about_meta = meta_defaults.copy()
    about_meta["title"] = about_meta["og_title"] = about_meta["twitter_title"] = about_meta[
        "gplus_title"
    ] = "About | {}".format(generic_title)
    about_meta["url"] = reverse("about")

    items = AboutItem.objects.order_by("order")
    if MODE == "app":
        items = items.filter(app_mode=True)
    else:
        items = items.filter(web_mode=True)

    items = items.all()

    for item in items:
        item.question = item.question.replace("{medium}", "app" if MODE == "app" else "site")
        item.answer = item.answer.replace("{medium}", "app" if MODE == "app" else "site")
        item.question_json = BeautifulSoup(item.question.replace('"', '\\"').replace("\n", ""), "lxml").text
        item.answer_json = (
            item.answer.replace('"', '\\"')
            .replace("\n", "")
            .replace("<h5>", "")
            .replace("</h5>", "")
            .replace("<p>", "")
            .replace("</p>", "")
        )

    return render(request, "office/about.html", {"items": items, "meta": Meta(**about_meta)})


def now(request):
    return render(
        request,
        "office/evening_prayer/redirect.html",
        {"title": "The Daily Office", "redirect_id": "redirect-to-today", "meta": meta},
    )


def family(request):
    family_meta = meta_defaults.copy()
    family_meta["title"] = family_meta["og_title"] = family_meta["twitter_title"] = family_meta[
        "gplus_title"
    ] = "Family Prayer | Devotions according to the Book of Common Prayer (2019)"
    family_meta["image"] = static("office/img/bcp.jpg")
    return render(
        request,
        "office/evening_prayer/redirect.html",
        {"title": "Family Prayer", "redirect_id": "redirect-to-today-family", "meta": Meta(**family_meta)},
    )


def handle404(request, exception):
    response = render(request, "404.html")
    response.status_code = 404
    return response


def four_oh_four(request):
    return render(request, "404.html")


def robots(request):
    return render(request, "robots.txt", content_type="text/plain")


def psalms(request):
    topics = PsalmTopic.objects.prefetch_related("psalmtopicpsalm_set__psalm").order_by("order").all()
    psalms = Psalm.objects.prefetch_related(
        Prefetch("psalmverse_set", queryset=PsalmVerse.objects.order_by("number"), to_attr="verses")
    ).all()
    for key, psalm in enumerate(psalms):
        psalms[key].first_half = psalm.verses[0].first_half.strip(";,.,\"'")
    return render(request, "office/psalm_directory.html", {"psalms": psalms, "topics": topics})


def psalm(request, number):
    psalm_text = get_psalms(number)
    psalm = Psalm.objects.prefetch_related(
        Prefetch("psalmtopicpsalm_set__psalm_topic", queryset=PsalmTopic.objects.order_by("order").all())
    ).get(number=number)
    topics = (
        PsalmTopic.objects.prefetch_related(
            Prefetch(
                "psalmtopicpsalm_set", queryset=PsalmTopicPsalm.objects.select_related("psalm").order_by("order").all()
            )
        )
        .filter(psalmtopicpsalm__psalm=psalm)
        .order_by("order")
        .distinct()
        .all()
    )
    return render(
        request, "office/psalm.html", {"number": number, "psalm": psalm, "psalm_text": psalm_text, "topics": topics}
    )


def update_notices(request, type="app"):
    items = UpdateNotice.objects.order_by("-version", "-created")
    if type == "app":
        items = items.filter(app_mode=True)
    if type == "web":
        items = items.filter(web_mode=True)
    items = items.all()
    data = serializers.serialize("json", items)
    return HttpResponse(data, content_type="application/json")


def privacy_policy(request):
    return render(request, "office/privacy.html")


def calendar(request):
    cal = Calendar()
    cal.add("prodid", "-//Daily Office//mxm.dk//")
    cal.add("version", "2.0")

    years = range(FIRST_BEGINNING_YEAR, LAST_BEGINNING_YEAR + 1)
    for year in years:
        year = ChurchYear(year)
        for datestring, calendardate in year.dates.items():
            office = Office(datestring)
            event = Event()
            event.add("SUMMARY", calendardate.primary.name)
            event.add("DTSTART", date(calendardate.date.year, calendardate.date.month, calendardate.date.day))
            event.add(
                "URL",
                "https://www.dailyoffice2019.com/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                ),
            )
            event.add(
                "LOCATION",
                "https://www.dailyoffice2019.com/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                ),
            )
            fast_day = calendardate.fast_day != calendardate.FAST_NONE
            feast_day = calendardate.primary.rank.precedence_rank <= 4
            description_lines = []
            for feast in calendardate.all:
                description_lines.append(feast.name)

            if fast_day:
                description_lines.append("")
                description_lines.append("FAST DAY")

            if feast_day:
                description_lines.append("")
                description_lines.append("SUNDAY OR MAJOR HOLY DAY")

            description_lines.append("")
            description_lines.append("MORNING PRAYER (or year 1)")
            description_lines.append("Psalms {} (30 day cycle)".format(office.thirty_day_psalter_day.mp_psalms))
            description_lines.append("Psalms {} (60 day cycle)".format(office.office_readings.mp_psalms))
            description_lines.append(office.office_readings.mp_reading_1)
            description_lines.append(office.office_readings.mp_reading_2)
            description_lines.append("")
            description_lines.append("EVENING PRAYER (or year 2)")
            description_lines.append("Psalms {} (30 day cycle)".format(office.thirty_day_psalter_day.ep_psalms))
            description_lines.append("Psalms {} (60 day cycle)".format(office.office_readings.ep_psalms))
            description_lines.append(office.office_readings.ep_reading_1)
            description_lines.append(office.office_readings.ep_reading_2)

            if calendardate.primary.rank.precedence_rank <= 4:
                description_lines.append("")
                description_lines.append("EUCHARIST")
                for reading in calendardate.mass_readings:
                    description_lines.append(reading.long_citation)

            description_lines.append("")
            description_lines.append(
                "Morning Prayer: https://www.dailyoffice2019.com/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Midday Prayer: https://www.dailyoffice2019.com/midday_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Evening Prayer: https://www.dailyoffice2019.com/evening_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Compline: https://www.dailyoffice2019.com/compline/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )

            description_lines.append(
                "Family Prayer in the Morning: https://www.dailyoffice2019.com/family/morning_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer at Midday: https://www.dailyoffice2019.com/family/midday_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer in the Early Evening: https://www.dailyoffice2019.com/family/early_evening_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )
            description_lines.append(
                "Family Prayer at the Close of Day: https://www.dailyoffice2019.com/family/close_of_day_prayer/{}-{}-{}/".format(
                    calendardate.date.year, calendardate.date.month, calendardate.date.day
                )
            )

            event.add("DESCRIPTION", "\n".join(description_lines))

            cal.add_component(event)

    res = cal.to_ical()
    response = HttpResponse(res, content_type="text/calendar")
    response["Content-Disposition"] = "attachment; filename=dailyoffice.ics"
    return HttpResponse(res)


def readings_data(testament=""):
    commemorations = SanctoraleCommemoration.objects.filter(calendar__year=2019).select_related("rank").all()

    def general_decorator(day):
        day.show_mp = (
            testament == "" or day.mp_reading_1_testament in testaments or day.mp_reading_2_testament in testaments
        )
        day.show_mp_1 = testament == "" or day.mp_reading_1_testament in testaments
        day.show_mp_2 = testament == "" or day.mp_reading_2_testament in testaments
        day.show_ep = (
            testament == "" or day.ep_reading_1_testament in testaments or day.ep_reading_2_testament in testaments
        )
        day.show_ep_1 = testament == "" or day.ep_reading_1_testament in testaments
        day.show_ep_2 = testament == "" or day.ep_reading_2_testament in testaments

        if testament == "GOSPELS":
            gospels = ["Matthew", "Mark", "Luke", "John"]
            mp_1 = day.mp_reading_1.split(" ")[0]
            mp_2 = day.mp_reading_2.split(" ")[0]
            ep_1 = day.ep_reading_1.split(" ")[0]
            ep_2 = day.ep_reading_2.split(" ")[0]
            day.show_mp_1 = mp_1 in gospels
            day.show_mp_2 = mp_2 in gospels
            day.show_ep_1 = ep_1 in gospels
            day.show_ep_2 = ep_2 in gospels
            day.show_mp = day.show_mp_1 or day.show_mp_2
            day.show_ep = day.show_ep_1 or day.show_ep_2

        day.mp_reading_1_passage = passage_to_citation(day.mp_reading_1)
        day.mp_reading_2_passage = passage_to_citation(day.mp_reading_2)
        day.ep_reading_1_passage = passage_to_citation(day.ep_reading_1)
        day.ep_reading_2_passage = passage_to_citation(day.ep_reading_2)

        day.mp_reading_1_closing = testament_to_closing(day.mp_reading_1_testament)
        day.mp_reading_1_closing_response = testament_to_closing_response(day.mp_reading_1_testament)
        day.mp_reading_2_closing = testament_to_closing(day.mp_reading_2_testament)
        day.mp_reading_2_closing_response = testament_to_closing_response(day.mp_reading_2_testament)
        day.ep_reading_1_closing = testament_to_closing(day.ep_reading_1_testament)
        day.ep_reading_1_closing_response = testament_to_closing_response(day.ep_reading_1_testament)
        day.ep_reading_2_closing = testament_to_closing(day.ep_reading_2_testament)
        day.ep_reading_2_closing_response = testament_to_closing_response(day.ep_reading_2_testament)

        return day

    def day_decorator(day):
        import calendar

        day.date_string = "{} {}".format(calendar.month_name[day.month], day.day)
        matches = [
            commemoration
            for commemoration in commemorations
            if commemoration.day == day.day and commemoration.month == day.month
        ]
        day.commemoration = matches[0] if matches else None
        return day

    testament = testament.upper()
    if testament == "OT":
        testament = "OT,DC"
    testaments = testament.split(",")

    days = StandardOfficeDay.objects.order_by("month", "day").all()
    others = HolyDayOfficeDay.objects.select_related("commemoration__rank").order_by("order").all()
    data = {
        "days": [general_decorator(day_decorator(day)) for day in days],
        "others": [general_decorator(other) for other in others],
        "testament": testament,
    }
    return data


def readings(request, testament=""):
    return render(request, "export/export_base.html", readings_data(testament))


def readings_doc(request, testament=""):
    from docx import Document
    from htmldocx import HtmlToDocx

    def normalize_document_styles(doc):
        for style in document.styles:
            if hasattr(style, "font"):
                style.font.name = "Helvetica"
                style.font.color.rgb = RGBColor(0, 0, 0)
        return doc

    document = Document()
    document = normalize_document_styles(document)
    new_parser = HtmlToDocx()

    html = render_to_string("export/export_base.html", readings_data(testament))
    soup = BeautifulSoup(html, "html.parser")
    for div in soup.find_all("h3", {"class": "reading-heading"}):
        div.decompose()
    for div in soup.find_all("p", {"class": "hide-in-doc"}):
        div.decompose()
    for div in soup.find_all("table", {"class": "hide-in-doc"}):
        div.decompose()
    for div in soup.find_all("a", {"class": "hide-in-doc"}):
        div.decompose()
    html = str(soup)
    html_parts = html.split('<span class="pagebreak"></span>')
    for part in html_parts:
        new_parser.add_html_to_document(part.strip(), document)
        document.add_page_break()
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response["Content-Disposition"] = "attachment; filename=bcp_2019_daily_office_readings.docx"
    document.save(response)

    return response

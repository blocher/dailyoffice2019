"""Episode titles and show notes, written from the calendar and the office text."""

import re
from datetime import datetime, time
from html import escape
from zoneinfo import ZoneInfo

from django.conf import settings

from podcasts.catalog import LANDING_PAGE_URL, SUPPORT_URL, SYNTHESIZED_VOICE_NOTE

ESV_NOTICE = (
    "Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), copyright © "
    "2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved."
)
WEEKDAY_AFTER = re.compile(r"^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) after (?:the )?(.+)$")
READING_MODULE = re.compile(r"Reading|Lesson|Scripture|Gospel|Epistle|Psalm", re.IGNORECASE)
PSALM_HEADING = re.compile(r"^Psalms? \d")
CANTICLE_MODULE = re.compile(r"Canticle|Invitatory", re.IGNORECASE)
MIN_CHAPTER_SECONDS = 5


def plain(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text or "")).strip()


ROMAN = {"I", "II", "III", "IV"}


def citation(text):
    """'HEBREWS 13:20-21' -> 'Hebrews 13:20-21' (citations in the text are set in capitals)."""
    if text != text.upper():
        return text
    return " ".join(word if word in ROMAN or not word.isalpha() else word.title() for word in text.split(" "))


def short_name(name):
    """'The Twentieth Sunday after Pentecost, or the Nineteenth Sunday after Trinity (Proper 23)'
    -> 'The Twentieth Sunday after Pentecost'."""
    return plain(name).split(", or the ")[0].strip()


def published_at(day, hour=None):
    """Episodes appear at PODCAST_PUBLISH_HOUR (Eastern) on their own day, or at ``hour``."""
    if hour is None:
        hour = getattr(settings, "PODCAST_PUBLISH_HOUR", 3)
    return datetime.combine(day, time(hour, 0), tzinfo=ZoneInfo("America/New_York"))


def long_date(day):
    return f"{day:%A}, {day:%B} {day.day}, {day.year}"


def commemorations(feed, calendar_date):
    if feed.is_readings and feed.proper_days_only:
        return [calendar_date.primary]
    return list(calendar_date.all_evening if feed.evening else calendar_date.all)


def headline(feed, calendar_date):
    """The name an episode is known by: the feast, else the week of the season."""
    days = commemorations(feed, calendar_date)
    if not days:
        return ""
    primary = days[0]
    if "FERIA" in (primary.rank.name if primary.rank else "") and len(days) > 1:
        return short_name(days[1].name)
    name = short_name(primary.name)
    week = WEEKDAY_AFTER.match(name)
    return f"Week of the {week.group(1)}" if week else name


def episode_title(feed, day, calendar_date):
    name = headline(feed, calendar_date)
    return f"{long_date(day)}: {name}" if name else long_date(day)


def module_citations(module):
    """A reading module's psalm headings, or the first citation of its lesson."""
    found = []
    if READING_MODULE.search(module.get("name", "")):
        for line in module.get("lines", []):
            content = citation(plain(str(line.get("content", ""))))
            kind = line.get("line_type")
            if kind == "heading" and PSALM_HEADING.match(content):
                found.append(content)
            elif kind in ("subheading", "citation") and re.search(r"\d", content) and not found:
                found.append(content)
    return found


def readings(modules):
    """[(section, [citations])] from the office text, in order.

    Psalm headings and the first citation of each reading module. The readings
    podcast labels modules "Morning Prayer: The Psalms"; those group by office.
    """
    sections = []
    for module in modules or []:
        name = module.get("name", "")
        section = name.split(":")[0] if ":" in name else ""
        found = module_citations(module)
        if not found:
            continue
        if sections and sections[-1][0] == section:
            sections[-1][1].extend(citation for citation in found if citation not in sections[-1][1])
        else:
            sections.append((section, found))
    return sections


def show_notes(feed, day, calendar_date, modules):
    """(plain-text summary, HTML description) for an episode."""
    days = commemorations(feed, calendar_date)
    names = [plain(commemoration.name) for commemoration in days]
    about = next(
        (
            re.sub(r"\s*\[\d+\]", "", plain(commemoration.ai_one_sentence))
            for commemoration in days
            if getattr(commemoration, "ai_one_sentence", None) and "FERIA" not in commemoration.rank.name
        ),
        "",
    )
    sections = readings(modules)
    follow = feed.follow_along_url(day)

    opening = f"{feed.office_name} for {long_date(day)}."
    text = [opening]
    html = [f"<p>{escape(opening)}</p>"]
    if names:
        text.append("; ".join(names) + ".")
        html.append(f"<p><strong>{escape('; '.join(names))}</strong></p>")
    if about:
        text.append(about)
        html.append(f"<p>{escape(about)}</p>")
    if sections:
        parts_text, parts_html = [], []
        for section, citations in sections:
            joined = " · ".join(citations)
            parts_text.append(f"{section}: {joined}" if section else joined)
            parts_html.append(f"<strong>{escape(section)}:</strong> {escape(joined)}" if section else escape(joined))
        text.append("Readings: " + ". ".join(parts_text) + ".")
        html.append("<p><strong>Readings:</strong> " + "<br>".join(parts_html) + "</p>")
    pray_along = "Read the day's readings" if feed.is_readings else "Pray along with the full text"
    text.append(f"{pray_along}: {follow}")
    html.append(f'<p><a href="{escape(follow)}">{pray_along}</a> at dailyoffice2019.com.</p>')
    details = f"{feed.style_label}. {SYNTHESIZED_VOICE_NOTE}"
    text.append(details)
    html.append(f"<p>{escape(details)}</p>")
    more = "More podcasts from the Daily Office, and the free website and app"
    text.append(f"{more}: {LANDING_PAGE_URL}. Support this work: {SUPPORT_URL}")
    html.append(f'<p><a href="{LANDING_PAGE_URL}">{more}</a>. ' f'<a href="{SUPPORT_URL}">Support this work</a>.</p>')
    if feed.settings.get("bible_translation", feed.settings.get("translation")) == "esv":
        text.append(ESV_NOTICE)
        html.append(f"<p><small>{escape(ESV_NOTICE)}</small></p>")
    return "\n\n".join(text), "\n".join(html)


def module_detail(module):
    """What a chapter is: 'Psalm 119:1-24', 'II Kings 8', or a canticle's name ('Te Deum Laudamus')."""
    found = module_citations(module)
    if found:
        return ", ".join(found)
    if CANTICLE_MODULE.search(module.get("name", "")):
        for line in module.get("lines", []):
            if line.get("line_type") == "heading":
                return citation(plain(str(line.get("content", ""))))
    return ""


def sections(track_list):
    """[(start, title)]: the player's section timeline, one entry per named module.

    Unnamed modules (the generic default) stay within the section before.
    """
    result = []
    for section in track_list or []:
        title = plain(section.get("name", ""))
        if not title or title == "Daily Office Module" or (result and result[-1][1] == title):
            continue
        result.append((round(float(section.get("start_time") or 0), 2), title))
    return result


def chapters(track_list, modules=None):
    """Podcasting 2.0 chapters from the player's section timeline.

    Titled by the office's modules, with the psalms, lesson, or canticle each one
    holds ("First Reading (II Kings 8)"). A chapter only a moment long, such as a
    heading spoken just before its first section, gives way to the next (never
    the opening one).
    """
    details = {}
    for module in modules or []:
        details.setdefault(plain(module.get("name", "")), module_detail(module))
    result = []
    for start, title in sections(track_list):
        if len(result) > 1 and start - result[-1]["startTime"] < MIN_CHAPTER_SECONDS:
            start = result.pop()["startTime"]
        detail = details.get(title, "")
        result.append({"startTime": start, "title": f"{title} ({detail})" if detail else title})
    return result

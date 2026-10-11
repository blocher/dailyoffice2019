"""Resolve reviewed alternates without mutating appointed lectionary records."""

import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup

from office.models import AlternateReading, OfficeDay, Scripture

logger = logging.getLogger(__name__)
EMPTY_TEXT = {"", "-", "<html><head></head><body>-</body></html>"}


@dataclass(frozen=True)
class ReadingSelection:
    scripture: Scripture
    testament: str
    text: str
    translation: str

    @property
    def passage(self):
        return self.scripture.passage


def scripture_translation(scripture, translation):
    translation = Scripture.normalize_bible_translation(translation)
    for candidate in dict.fromkeys(
        (translation, OfficeDay.TRANSLATION_FALLBACKS.get(translation, "nrsvce"), "nrsvce")
    ):
        text = getattr(scripture, candidate, None)
        if text and text.strip() not in EMPTY_TEXT:
            soup = BeautifulSoup(text, "html.parser")
            for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                heading.decompose()
            if soup.get_text(strip=True) not in ("", "-"):
                return text, candidate
    return None, translation


def alternate_first_lesson(day, office, settings, year, translation, abbreviated=False):
    if settings.get("apocrypha_readings", "appointed") != "alternate":
        return None
    if not hasattr(day, "_alternate_first_lesson_mapping"):
        day._alternate_first_lesson_mapping = (
            AlternateReading.objects.filter(office_day_id=day.pk)
            .select_related("whole", "morning", "evening", "short_whole", "short_morning", "short_evening")
            .first()
        )
    mapping = day._alternate_first_lesson_mapping
    if not mapping:
        return None
    donor = mapping.donor_office
    other = "ep" if donor == "mp" else "mp"
    if (
        getattr(day, other + "_reading_1_testament") not in ("AP", "DC")
        or getattr(day, donor + "_reading_1_testament") not in ("OT", "NT")
        or getattr(day, donor + "_reading_1") != mapping.whole.passage
        or (mapping.short_whole_id and getattr(day, donor + "_reading_1_abbreviated") != mapping.short_whole.passage)
    ):
        logger.warning("Stale alternate first-lesson mapping for %s", day.pk)
        return None
    if int(settings.get("reading_cycle", 1)) == 2:
        selected_office = "ep" if year % 2 == 0 else "mp"
        if selected_office == donor:
            return None
        scripture = mapping.short_whole if abbreviated and mapping.short_whole_id else mapping.whole
        text, actual_translation = scripture_translation(scripture, translation)
    else:
        short = abbreviated and bool(mapping.short_whole_id)
        morning = mapping.short_morning if short else mapping.morning
        evening = mapping.short_evening if short else mapping.evening
        if not morning or not evening:
            logger.warning("Incomplete alternate first-lesson mapping for %s", day.pk)
            return None
        # Both Offices must be usable before substituting either portion.
        texts = [scripture_translation(passage, translation) for passage in (morning, evening)]
        if not all(text for text, _ in texts):
            logger.warning("Missing alternate first-lesson text for %s", day.pk)
            return None
        scripture = morning if office == "mp" else evening
        text, actual_translation = texts[0 if office == "mp" else 1]
    if not text:
        logger.warning("Missing alternate first-lesson text for %s", day.pk)
        return None
    return ReadingSelection(scripture, getattr(day, donor + "_reading_1_testament"), text, actual_translation)

"""Spoken Scripture readings, without the rest of the office.

Used by the audio player on the Readings page and by the two readings podcasts
(see ``podcasts.catalog``). A ``ReadingsAudioOffice`` is an ordinary ``Office``
whose modules are only the appointed readings, so it goes through exactly the
same audio pipeline as the offices: the same voices, clip cache, background
builds, and combined track. ``audio_ceremony.frame_tracks`` opens it with a
"Readings for ..." announcement and the bells.

Kinds (matching the Readings page tabs):

* ``morning_prayer`` / ``evening_prayer``: the psalms and lessons of one office.
  Position 1 on a holy day is the sequential (ordinary weekday) table.
* ``daily_office``: Morning Prayer's then Evening Prayer's readings, the
  readings podcast's daily episode.
* ``holy_eucharist``: the collect and lessons of one Eucharist on the Readings
  page, in that page's order. ``position=principal`` is the day's principal
  service, which the Holy Eucharist podcast uses.
"""

import re
from functools import partial

from django.http import Http404
from num2words import num2words

from churchcal.calculations import get_church_year
from office.alternate_readings import scripture_translation
from office.api.line import Line
from office.api.views import Module
from office.api.views.index import (
    EPPsalms,
    MPPsalms,
    Office,
    OfficeAPIView,
    ReadingModule,
    get_collects_for_readings,
    get_reading_name_from_reading_number,
)
from office.models import Scripture, StandardOfficeDay
from office.utils import passage_to_citation
from psalter.utils import get_psalms

KINDS = ("morning_prayer", "evening_prayer", "daily_office", "holy_eucharist")
PRINCIPAL = "principal"
SERVICE_NAMES = {
    "morning_prayer": "Morning Prayer",
    "evening_prayer": "Evening Prayer",
    "daily_office": "the Daily Office",
    "holy_eucharist": "the Holy Eucharist",
}
EVANGELISTS = ("Matthew", "Mark", "Luke", "John")


def plain(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def spoken_psalm(heading):
    """'Psalm 119:1-24' -> 'Psalm one hundred nineteen, verses one through twenty-four.'"""
    match = re.match(r"^Psalm\s+(\d+)(?::(\d+)(?:\s*[-–]\s*(\d+))?)?", heading or "")
    if not match:
        return None
    psalm, first, last = match.groups()
    words = f"Psalm {num2words(int(psalm))}"
    if first and last:
        words += f", verses {num2words(int(first))} through {num2words(int(last))}"
    elif first:
        words += f", verse {num2words(int(first))}"
    return words + "."


def announce_psalms(lines):
    """Readings audio names each psalm before it is read (headings are silent)."""
    announced = []
    for line in lines:
        announced.append(line)
        if line and line.get("line_type") == "heading":
            words = spoken_psalm(line.get("content"))
            if words:
                announced.append(Line(words, "speaker"))
    return announced


def has_proper_eucharist(calendar_date):
    """True when the day has its own Eucharistic readings.

    Sundays, principal feasts, holy days, and the privileged days of Lent and
    Easter (precedence 1-4). Weekdays repeat the previous Sunday's readings and
    lesser feasts use a common of saints, so they have nothing new to publish.
    """
    primary = calendar_date.primary
    if not primary or not primary.rank or primary.rank.precedence_rank > 4:
        return False
    readings = list(calendar_date.mass_readings)
    return bool(readings) and not any(reading.common_id for reading in readings)


def first_per_reading_number(readings):
    """One reading for each place in the service (the first of any alternatives)."""
    chosen = {}
    for reading in readings:
        chosen.setdefault(reading.reading_number, reading)
    return [chosen[number] for number in sorted(chosen)]


def eucharist_services(calendar_date, mass_year):
    """The Readings page's Holy Eucharist services, in its order.

    Mirrors ``ReadingsSerializer.get_services``: each commemoration's readings
    grouped by service, those of ranked days before those of ferias.
    """
    ranked, ferias = {}, {}
    for commemoration in calendar_date.morning_and_evening:
        grouped = {}
        for reading in commemoration.get_all_mass_readings_for_year(mass_year):
            grouped.setdefault(reading.service or "-", []).append(reading)
        for service, readings in grouped.items():
            name = f"{commemoration.name} ({service}) " if service not in ["", "-"] else f"{commemoration.name}"
            target = ferias if "FERIA" in commemoration.rank.name else ranked
            target[name] = (commemoration, service, readings)
    return [
        {"name": name, "commemoration": commemoration, "service": service, "readings": readings}
        for name, (commemoration, service, readings) in {**ranked, **ferias}.items()
    ]


class AnnouncedPsalms(Module):
    """The appointed psalms (30- or 60-day cycle), each psalm announced."""

    def __init__(self, office, psalms_class, name):
        super().__init__(office)
        self.psalms = psalms_class(office)
        self.name = name

    def get_lines(self):
        return announce_psalms(self.psalms.get_lines())


class Lesson(ReadingModule):
    def __init__(self, office, office_code, number, name):
        super().__init__(office)
        self.office_code = office_code
        self.number = number
        self.name = name

    def get_lines(self):
        heading = "The First Lesson" if self.number == 1 else "The Second Lesson"
        return [Line(heading, "heading")] + (self.get_lines_for_reading(self.office_code, self.number) or [])


class Announcement(Module):
    """Audio-only words between the two offices of the daily readings."""

    def __init__(self, office, text, name):
        super().__init__(office)
        self.text = text
        self.name = name

    def get_lines(self):
        return [Line(self.text, "speaker")]


class EucharistCollect(Module):
    name = "The Collect of the Day"

    def __init__(self, office, collects):
        super().__init__(office)
        self.collects = collects

    def get_lines(self):
        lines = [Line("The Collect of the Day", "heading")]
        for collect in self.collects:
            text = plain(collect)
            text = re.sub(r"\s*Amen\.?$", "", text).strip()
            if text:
                lines += [Line(text, "leader"), Line("Amen.", "congregation")]
        return lines


class EucharistReading(ReadingModule):
    """One lesson, psalm, or Gospel of the Eucharist, with its liturgical frame."""

    def __init__(self, office, reading):
        super().__init__(office)
        self.reading = reading
        self.name = get_reading_name_from_reading_number(reading)

    @property
    def traditional(self):
        return self.office.settings.get("language_style") == "traditional"

    def psalm_lines(self, citation):
        psalms = citation.replace("Psalms", "").replace("Psalm", "").strip()
        lines = get_psalms(
            psalms,
            api=True,
            language_style=self.office.settings["psalm_translation"],
            headings=self.office.settings["psalm_style"],
            display_language=self.language,
        )
        return [Line(self.name, "heading")] + announce_psalms(lines)

    def get_lines(self):
        reading = self.reading
        citation = reading.long_citation
        if reading.reading_type == "psalm" and "psalm" in citation.lower():
            return self.psalm_lines(citation)
        text = None
        if reading.long_scripture:
            text, _ = scripture_translation(reading.long_scripture, self.bible_translation)
        text = text or reading.long_text
        if not text:
            return []
        text = self.remove_headings_if_needed(text)
        from office.api.views.index import GenericDailyOfficeSerializer

        voice = GenericDailyOfficeSerializer.reading_voice(text)
        text = GenericDailyOfficeSerializer.handle_html(text, html=True, no_generate=True, voice=voice)
        book = (citation.split(" ")[0] or "").title()
        is_gospel = reading.reading_type == "gospel" or book in EVANGELISTS
        if is_gospel:
            evangelist = next((name for name in EVANGELISTS if name.upper() in citation.upper()), book)
            opening = [
                Line(f"The Holy Gospel of our Lord Jesus Christ according to {evangelist}.", "reader"),
                Line(
                    "Glory be to thee, O Lord." if self.traditional else "Glory to you, Lord Christ.", "congregation"
                ),
            ]
            closing = [
                Line("The Gospel of the Lord.", "reader", silence_before=1.3),
                Line(
                    "Praise be to thee, O Christ." if self.traditional else "Praise to you, Lord Christ.",
                    "congregation",
                ),
            ]
        else:
            opening = [Line(passage_to_citation(citation, language=self.language), "reader")]
            closing = [Line(self.closing(reading.testament), "reader", silence_before=1.3)]
            response = self.closing_response(reading.testament)
            if response:
                closing.append(Line(response, "congregation"))
        lines = (
            [Line(self.name, "heading"), Line(citation, "subheading")]
            + opening
            + [Line(text, "html", silence_before=1.3)]
            + closing
        )
        for line in lines:
            if line["line_type"] in {"reader", "html"}:
                line["audio_voice"] = voice
        return lines


class ReadingsAudioOffice(Office):
    """The readings of one service (or of the whole Daily Office), read aloud."""

    tag = "readings"

    def __init__(self, request, year, month, day, kind="morning_prayer", position=0):
        super().__init__(request, year, month, day)
        if kind not in KINDS:
            raise Http404("Unknown readings service.")
        self.kind = kind
        self.position = position
        query = request.GET
        translation = Scripture.normalize_bible_translation(
            query.get("translation") or self.settings.get("bible_translation")
        )
        psalms = query.get("psalms") or self.settings.get("psalm_translation") or "contemporary"
        psalms = psalms if psalms in ("contemporary", "traditional") else "contemporary"
        style = query.get("style") or self.settings.get("psalm_style") or "whole_verse"
        style = style if style in ("whole_verse", "half_verse", "unison") else "whole_verse"
        psalter = query.get("psalter") or self.settings.get("psalter") or "60"
        # The Readings page's own choices take the place of the office settings;
        # the readings are always read whole, without headings or ESV players.
        self.settings.update(
            bible_translation=translation,
            psalm_translation=psalms,
            language_style=psalms,
            psalm_style=style,
            psalter=psalter if psalter in ("30", "60") else "60",
            lectionary="daily-office-readings",
            reading_cycle="1",
            reading_length="full",
            reading_headings="off",
            reading_audio="off",
        )
        if kind in ("morning_prayer", "evening_prayer") and position == 1:
            # The second Morning/Evening Prayer on a holy day is the sequential table.
            self.office_readings = StandardOfficeDay.objects.get(month=self.date.date.month, day=self.date.date.day)
        elif position not in (0, None) and kind != "holy_eucharist":
            raise Http404("No such readings service.")
        self.eucharist = self.select_eucharist() if kind == "holy_eucharist" else None

    def select_eucharist(self):
        if self.position == PRINCIPAL:
            if not has_proper_eucharist(self.date):
                raise Http404("This day has no proper Eucharistic readings.")
            readings = list(self.date.mass_readings)
            service = readings[0].service if readings else "-"
            return {"commemoration": self.date.primary, "service": service, "readings": readings}
        mass_year = get_church_year(self.date.date.strftime("%Y-%m-%d")).mass_year
        services = eucharist_services(self.date, mass_year)
        try:
            return services[int(self.position or 0)]
        except (IndexError, TypeError, ValueError):
            raise Http404("No such Eucharist.")

    @property
    def name(self):
        return f"Readings for {SERVICE_NAMES[self.kind]}"

    @property
    def audio_evening(self):
        return self.kind == "evening_prayer"

    @property
    def audio_commemorations(self):
        if self.eucharist:
            return [self.eucharist["commemoration"]]
        if self.kind == "evening_prayer":
            return self.date.all_evening
        return self.date.all

    def office_modules(self, code, prefix=""):
        psalms_class = MPPsalms if code == "mp" else EPPsalms
        label = f"{prefix}: " if prefix else ""
        return [
            AnnouncedPsalms(self, psalms_class, f"{label}The Psalms"),
            Lesson(self, code, 1, f"{label}The First Lesson"),
            Lesson(self, code, 2, f"{label}The Second Lesson"),
        ]

    def get_modules(self):
        if self.kind == "morning_prayer":
            return self.office_modules("mp")
        if self.kind == "evening_prayer":
            return self.office_modules("ep")
        if self.kind == "daily_office":
            return (
                [Announcement(self, "At Morning Prayer.", "Morning Prayer")]
                + self.office_modules("mp", "Morning Prayer")
                + [Announcement(self, "At Evening Prayer.", "Evening Prayer")]
                + self.office_modules("ep", "Evening Prayer")
            )
        eucharist = self.eucharist
        style = "traditional" if self.settings["language_style"] == "traditional" else "contemporary"
        collects = get_collects_for_readings(eucharist["service"], eucharist["commemoration"], self.date, style=style)
        return [EucharistCollect(self, collects)] + [
            EucharistReading(self, reading) for reading in first_per_reading_number(eucharist["readings"])
        ]


class ReadingsAudioView(OfficeAPIView):
    """``/api/v1/readings_audio/<kind>/<date>?include_audio_links=true``

    Takes the Readings page's ``translation``, ``psalms``, ``style`` and
    ``psalter`` choices and a ``position`` (which of the day's services).
    """

    def get(self, request, kind, year, month, day):
        if kind not in KINDS:
            raise Http404("Unknown readings service.")
        position = request.GET.get("position", "0")
        if position != PRINCIPAL:
            try:
                position = int(position)
            except ValueError:
                raise Http404("No such readings service.")
        office_class = partial(ReadingsAudioOffice, kind=kind, position=position)
        return self.office_response(request, office_class, year, month, day)

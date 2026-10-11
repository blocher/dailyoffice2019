"""Frozen, local-only extraction and seed logic for migration 0033.

Do not import runtime Office/Scripture models here. Source text stays in the
existing licensed Scripture store; the JSON contains editorial metadata only.
"""

import hashlib
import json
import re
import uuid
from pathlib import Path

from bs4 import BeautifulSoup, Comment
from django.db.models import Max, Q

NAMESPACE = uuid.UUID("b76c0c63-dc55-453b-aa35-6c3886135221")
TRANSLATIONS = (
    "esv",
    "kjv",
    "rsv",
    "nrsvce",
    "nabre",
    "niv",
    "nasb",
    "coverdale",
    "renewed_coverdale",
    "cuvs",
    "cuv",
    "sigao",
    "znsigao",
    "nvi",
    "rv1960",
)


def owned_id(key):
    return uuid.uuid5(NAMESPACE, key)


def plan():
    rows = json.loads(Path(__file__).with_suffix(".json").read_text())
    for row in rows:
        for prefix in ("", "short_") if "short_verses" in row else ("",):
            expected = set(row[prefix + "verses"])
            cut = row[prefix + "cut"]
            for office in ("mp", "ep"):
                citation = row[prefix + office]
                match = re.fullmatch(r"(.+) (\d+):([\d,-]+)", citation)
                if not match or int(match[2]) != row["chapter"] or match[1] != re.match(r"(.+) \d+", row["donor"])[1]:
                    raise ValueError(f"Invalid reviewed citation {citation!r}")
                actual = set()
                for part in match[3].split(","):
                    bounds = list(map(int, part.split("-")))
                    actual.update(range(bounds[0], bounds[-1] + 1))
                selected = {v for v in expected if (v <= cut if office == "mp" else v > cut)}
                if not selected or actual != selected:
                    raise ValueError(f"Reviewed citation {citation!r} does not match its extraction verses")
    return rows


def present(text):
    return bool(text and BeautifulSoup(text, "html.parser").get_text(strip=True) not in ("", "-"))


def marker(tag):
    for value in tag.get("class", []):
        match = re.fullmatch(r"[A-Za-z0-9]+-(\d+)-(\d+)", value)
        if match:
            return tuple(map(int, match.groups()))
    return None


def extract(text, chapter, expected, selected, book_marker=None):
    """Prune verse-marked HTML, preserving selected ancestors/paragraphs.

    Validate every non-whitespace text node and every verse before pruning.
    Mislabeled verse markers are safe only if the explicit number agrees on
    which side of the split the complete chunk belongs.
    """
    soup = BeautifulSoup(text, "html.parser")
    expected, selected = set(expected), set(selected)
    for node in soup.find_all(string=lambda s: isinstance(s, Comment)):
        node.extract()
    for node in soup.select(".footnotes, .crossrefs, sup.footnote, sup.crossreference"):
        node.decompose()
    seen = set()
    for tag in soup.select("span.text"):
        pos = marker(tag)
        if (
            not pos
            or pos[0] != chapter
            or (book_marker and f"{book_marker}-{pos[0]}-{pos[1]}" not in tag.get("class", []))
        ):
            raise ValueError("Unsupported or cross-chapter verse markup")
        numbers = {pos[1]}
        # Explicit numbers must never place a chunk on both sides of a split.
        for number in tag.select("sup.versenum"):
            value = number.get_text(strip=True)
            if not value.isdigit():
                raise ValueError(f"Unsupported verse number {value!r}")
            numbers.add(int(value))
        if not numbers <= expected or len({v in selected for v in numbers}) != 1:
            raise ValueError(f"Verse markers cross the split or donor range: {numbers}")
        if not tag.find_parent(["h1", "h2", "h3", "h4", "h5", "h6"]):
            seen.update(numbers)
    if seen != expected:
        raise ValueError(f"Incomplete donor verse markup: missing {expected-seen}, extra {seen-expected}")
    for node in soup.find_all(string=True):
        if not node.strip():
            continue
        ancestors = list(node.parents)
        if not any(marker(t) for t in ancestors if getattr(t, "attrs", None) is not None):
            if not any(
                t.name in ("h1", "h2", "h3", "h4", "h5", "h6") or "chapternum" in t.get("class", []) for t in ancestors
            ):
                raise ValueError(f"Unmarked donor text: {str(node)[:70]!r}")
    # Remove complete verse chunks, including their heading chunks, outside this portion.
    for tag in list(soup.select("span.text")):
        if tag.parent is not None and marker(tag)[1] not in selected:
            tag.decompose()
    # Drop headings whose marked verse content was removed (or is unsupported).
    for tag in list(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])):
        if not tag.select("span.text"):
            tag.decompose()
    for tag in list(soup.select(".chapternum")):
        if not tag.find_parent("span", class_="text"):
            tag.decompose()
    # Drop empty formatting containers left behind by pruning.
    for tag in reversed(list(soup.find_all())):
        if tag.name != "br" and not tag.get_text(strip=True) and not tag.select("span.text"):
            tag.decompose()
    result = str(soup)
    if not present(result):
        raise ValueError("Extraction produced empty Scripture")
    return result


def scripture_texts(source, row, short=False):
    expected = row["short_verses"] if short else row["verses"]
    cut = row["short_cut"] if short else row["cut"]
    book = re.match(r"(.+) \d+", row["donor"])[1]
    book_marker = {
        "Exodus": "Exod",
        "Acts": "Acts",
        "Judges": "Judg",
        "II Chronicles": "2Chr",
        "II Kings": "2Kgs",
        "II John": "2John",
        "Isaiah": "Isa",
        "Song of Songs": "Song",
    }[book]
    values = [{}, {}]
    for translation in TRANSLATIONS:
        text = getattr(source, translation)
        if not present(text):
            continue
        # NABRE's Song 6/7 chapter boundaries differ from the canonical citations.
        # Use NRSVCE fallback for both portions; never relabel divergent verse text.
        if translation == "nabre" and row["donor"] in ("Song of Songs 6", "Song of Songs 7"):
            for fields in values:
                fields["nabre"] = None
            continue
        if translation == "rsv" and row["donor"] == "II Chronicles 20":
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup.find_all("span", class_="2Chr-20-21"):
                if (
                    hashlib.sha256(tag.get_text().encode()).hexdigest()
                    == "dc57512a83cb30ef8152f98ac5cb0af5f8c972d47bba3994de1311663c3f586d"
                ):
                    tag["class"] = ["text", "2Chr-20-22"]
            text = str(soup)
        for index, selected in enumerate(([v for v in expected if v <= cut], [v for v in expected if v > cut])):
            try:
                values[index][translation] = extract(text, row["chapter"], expected, selected, book_marker=book_marker)
            except ValueError as exc:
                raise ValueError(f"{source.passage} ({translation}): {exc}") from exc
    for fields in values:
        if not present(fields.get("esv")) or not present(fields.get("nrsvce")):
            raise ValueError(f"{source.passage}: populated ESV and NRSVCE donors are required")
    return values


def body_text(text):
    soup = BeautifulSoup(text or "", "html.parser")
    for tag in soup.select(
        "h1, h2, h3, h4, h5, h6, .chapternum, .versenum, sup.footnote, sup.crossreference, .footnotes, .crossrefs"
    ):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def forward(apps, schema_editor):
    database = schema_editor.connection.alias
    Scripture = apps.get_model("office", "Scripture")
    OfficeDay = apps.get_model("office", "OfficeDay")
    Alternate = apps.get_model("office", "AlternateReading")
    Setting = apps.get_model("office", "Setting")
    Option = apps.get_model("office", "SettingOption")
    scriptures = Scripture.objects.using(database)
    plans = {row["donor"]: row for row in plan()}

    def whole(passage):
        matches = list(scriptures.filter(passage=passage))
        if len(matches) != 1:
            raise ValueError(f"Alternate readings require exactly one existing Scripture row for {passage!r}")
        return matches[0]

    def portion(passage, texts):
        matches = list(scriptures.filter(passage=passage))
        if len(matches) > 1:
            raise ValueError(f"Ambiguous pre-existing Scripture: {passage}")
        if matches:
            existing = matches[0]
            for name, value in texts.items():
                if body_text(getattr(existing, name)) != body_text(value):
                    raise ValueError(f"Pre-existing {passage} ({name}) differs from donor; no user text overwritten")
            return existing
        return scriptures.create(uuid=owned_id("scripture:" + passage), passage=passage, **texts)

    # An empty fresh database has no lectionary to seed; importing a lectionary
    # later requires rerunning this deterministic seed via the management command.
    for day in OfficeDay.objects.using(database).filter(
        Q(mp_reading_1_testament__in=["AP", "DC"]) | Q(ep_reading_1_testament__in=["AP", "DC"])
    ):
        ap = [office for office in ("mp", "ep") if getattr(day, office + "_reading_1_testament") in ("AP", "DC")]
        if len(ap) != 1:
            raise ValueError(f"{day.pk}: both first lessons are Apocrypha; editorial review required")
        donor_office = "ep" if ap[0] == "mp" else "mp"
        donor = getattr(day, donor_office + "_reading_1")
        row = plans.get(donor)
        if not row or getattr(day, ap[0] + "_reading_1") != row["apocrypha"] or donor_office != row["donor_office"]:
            raise ValueError(f"{day.pk}: unreviewed Apocrypha/donor pairing {donor!r}")
        if getattr(day, donor_office + "_reading_1_testament") != row["testament"]:
            raise ValueError(f"{day.pk}: donor testament differs from reviewed plan")
        source = whole(donor)
        texts = scripture_texts(source, row)
        defaults = {
            "donor_office": donor_office,
            "whole": source,
            "morning": portion(row["mp"], texts[0]),
            "evening": portion(row["ep"], texts[1]),
            "short_whole": None,
            "short_morning": None,
            "short_evening": None,
        }
        short_donor = getattr(day, donor_office + "_reading_1_abbreviated")
        if short_donor != row.get("short_donor"):
            raise ValueError(f"{day.pk}: abbreviated donor differs from reviewed plan")
        if short_donor:
            source = whole(short_donor)
            texts = scripture_texts(source, row, short=True)
            defaults.update(
                short_whole=source,
                short_morning=portion(row["short_mp"], texts[0]),
                short_evening=portion(row["short_ep"], texts[1]),
            )
        existing = Alternate.objects.using(database).filter(office_day=day).first()
        if existing:
            if any(
                getattr(existing, key + "_id") != value.pk if hasattr(value, "pk") else getattr(existing, key) != value
                for key, value in defaults.items()
            ):
                raise ValueError(f"{day.pk}: pre-existing alternate mapping differs; no user mapping overwritten")
        else:
            Alternate.objects.using(database).create(
                uuid=owned_id("mapping:" + str(day.pk)), office_day=day, **defaults
            )

    settings = Setting.objects.using(database)
    existing_settings = list(settings.filter(name="apocrypha_readings"))
    if existing_settings:
        if len(existing_settings) != 1 or existing_settings[0].site != 1:
            raise ValueError("Ambiguous pre-existing apocrypha_readings setting; no settings overwritten")
        setting = existing_settings[0]
        options = list(Option.objects.using(database).filter(setting=setting).order_by("order"))
        if [(option.value, option.abbreviation) for option in options] != [("appointed", "A"), ("alternate", "B")]:
            raise ValueError("Pre-existing apocrypha_readings options differ; no settings overwritten")
        if settings.exclude(pk=setting.pk).filter(setting_string_order=setting.setting_string_order).exists():
            raise ValueError(
                "Apocrypha share-link position conflicts with an existing setting; no positions overwritten"
            )
    else:
        last = settings.aggregate(value=Max("setting_string_order"))["value"]
        display = settings.filter(site=1, setting_type=1).aggregate(value=Max("order"))["value"]
        setting = settings.create(
            uuid=owned_id("setting"),
            name="apocrypha_readings",
            title="Apocrypha Readings",
            description="As appointed, or divide the other first lesson between the two Offices (BCP 2019, p. 737). "
            "In the two-year cycle, replace an Apocrypha first lesson with the whole other first lesson.",
            site=1,
            setting_type=1,
            order=(display or 0) + 1,
            setting_string_order=0 if last is None else last + 1,
        )
        for order, (name, value, abbreviation) in enumerate(
            [("As appointed", "appointed", "A"), ("Use alternate readings", "alternate", "B")]
        ):
            Option.objects.using(database).create(
                uuid=owned_id("option:" + value),
                setting=setting,
                order=order,
                name=name,
                value=value,
                abbreviation=abbreviation,
            )


def backward(apps, schema_editor):
    database = schema_editor.connection.alias
    Alternate = apps.get_model("office", "AlternateReading")
    for mapping in Alternate.objects.using(database).all():
        if mapping.pk == owned_id("mapping:" + str(mapping.office_day_id)):
            mapping.delete(using=database)
    # Retain Scripture rows: readers/admins may have reused or edited them since
    # deployment. Reversing must not remove that data. Reapplication reuses them.
    # Retain the appended setting/options too: saved preferences and admin edits
    # must survive a rollback. They are inert in the previous application version.

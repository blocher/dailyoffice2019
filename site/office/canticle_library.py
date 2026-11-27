"""The canticle library: every canticle the offices use, with its texts and
the schemes that appoint it.

The office modules decide which canticle to say on a given day by running the
rule classes in ``office.canticles`` (and the invitatory rules on
``MPInvitatory``). This module turns those same rules into a browsable
catalog for the Canticles page: one entry per canticle, both language styles,
and for each canticle rotation a table of what is said on each day of the
week in each season.

The rotation tables are computed by running the real rule classes over a
model week in every season, so they cannot drift from what the offices say.
Only the few date-specific exceptions (April 29, November 13, Psalm 67) are
written out by hand as notes.
"""

from datetime import date
from functools import lru_cache
from types import SimpleNamespace

from office.api.line import file_to_lines
from office.canticles import (
    BCP1979CanticleTable,
    DefaultCanticles,
    EP1,
    EP2,
    MP1,
    MP2,
    MP3,
    O1,
    O2,
    REC2011CanticleTable,
    S1,
    S10,
    S2,
    S3,
    S4,
    S5,
    S6,
    S7,
    S8,
    S9,
)

OFFICES = [
    {"key": "morning", "label": "Morning Prayer"},
    {"key": "evening", "label": "Evening Prayer"},
    {"key": "compline", "label": "Compline"},
]

CATEGORIES = [
    {"key": "invitatory", "label": "Invitatories", "description": "Said at the opening of Morning Prayer."},
    {
        "key": "evening_hymn",
        "label": "The Evening Hymn",
        "description": "Said or sung at the opening of Evening Prayer.",
    },
    {"key": "morning", "label": "Morning Canticles", "description": "The canticles of Morning Prayer."},
    {"key": "evening", "label": "Evening Canticles", "description": "The canticles of Evening Prayer and Compline."},
    {
        "key": "supplemental",
        "label": "Supplemental Canticles",
        "description": "Canticles that may replace the usual canticles of Morning and Evening Prayer.",
    },
    {"key": "other", "label": "Other Canticles", "description": ""},
]

# The seasons a rotation is evaluated in, in the order of the year. The
# rules treat Holy Week exactly as Lent, so they share one bucket.
SEASONS = [
    {"key": "advent", "label": "Advent", "season": "Advent"},
    {"key": "christmas", "label": "Christmas", "season": "Christmastide"},
    {"key": "epiphany", "label": "Epiphany", "season": "Epiphanytide"},
    {"key": "lent", "label": "Lent & Holy Week", "season": "Lent"},
    {"key": "easter", "label": "Easter", "season": "Eastertide"},
    {"key": "pentecost", "label": "After Pentecost", "season": "Season After Pentecost"},
]

# Monday 2 June 2025 to Sunday 8 June 2025: an ordinary week whose dates hit
# none of the date-specific exceptions (the 12th, April 29, November 13).
MODEL_WEEK = {weekday: date(2025, 6, 2 + weekday) for weekday in range(7)}

DAYS = [
    {"key": "sunday", "label": "Sunday", "weekday": 6},
    {"key": "monday", "label": "Monday", "weekday": 0},
    {"key": "tuesday", "label": "Tuesday", "weekday": 1},
    {"key": "wednesday", "label": "Wednesday", "weekday": 2},
    {"key": "thursday", "label": "Thursday", "weekday": 3},
    {"key": "friday", "label": "Friday", "weekday": 4},
    {"key": "saturday", "label": "Saturday", "weekday": 5},
    {"key": "feast", "label": "Principal Feasts", "weekday": 2, "feast": True},
]

SLOTS = [
    {"key": "mp1", "office": "morning", "label": "First Canticle", "method": "get_mp_canticle_1"},
    {"key": "mp2", "office": "morning", "label": "Second Canticle", "method": "get_mp_canticle_2"},
    {"key": "ep1", "office": "evening", "label": "First Canticle", "method": "get_ep_canticle_1"},
    {"key": "ep2", "office": "evening", "label": "Second Canticle", "method": "get_ep_canticle_2"},
]

# Canticle classes to library slugs. O2 is the Jubilate, which is also an
# invitatory; the library lists it once.
CLASS_SLUGS = {
    MP1: "te-deum",
    MP2: "benedictus-es-domine",
    MP3: "benedictus",
    EP1: "magnificat",
    EP2: "nunc-dimittis",
    S1: "magna-et-mirabilia",
    S2: "surge-illuminare",
    S3: "kyrie-pantokrator",
    S4: "quaerite-dominum",
    S5: "cantemus-domino",
    S6: "dignus-es",
    S7: "cantate-domino",
    S8: "ecce-deus",
    S9: "deus-misereatur",
    S10: "benedicite",
    O1: "gloria-in-excelsis",
    O2: "jubilate",
}

INVITATORIES = [
    {
        "slug": "venite",
        "file": "venite",
        "latin_name": "Venite",
        "english_name": "O Come",
        "category": "invitatory",
        "suggested": ["Most days"],
        "notes": ["In Lent the whole psalm is said; at other times the last verses may be omitted."],
    },
    {
        "slug": "jubilate",
        "file": "jubilate",
        "latin_name": "Jubilate",
        "english_name": "Be Joyful",
        "category": "invitatory",
        "suggested": ["Sundays and feasts", "When Psalm 95 is appointed"],
        "notes": [],
    },
    {
        "slug": "pascha-nostrum",
        "file": "pascha_nostrum",
        "latin_name": "Pascha Nostrum",
        "english_name": "Christ Our Passover",
        "category": "invitatory",
        "suggested": ["Easter Week", "Eastertide"],
        "notes": [],
    },
    {
        "slug": "phos-hilaron",
        "file": "phos_hilaron",
        "latin_name": "Phos Hilaron",
        "english_name": "O Gladsome Light",
        "category": "evening_hymn",
        "suggested": ["Every evening"],
        "notes": [],
    },
]

CANTICLE_CATEGORIES = {
    MP1: "morning",
    MP2: "morning",
    MP3: "morning",
    EP1: "evening",
    EP2: "evening",
    O1: "other",
}

ROTATIONS = [
    {
        "key": "default",
        "setting_value": "default",
        "name": "Traditional",
        "description": "The traditional fixed canticles each day.",
        "rules": DefaultCanticles,
        "notes": [],
    },
    {
        "key": "2011",
        "setting_value": "2011",
        "name": "Seasonal Rotation",
        "description": "One fixed canticle and one canticle that rotates by season.",
        "rules": REC2011CanticleTable,
        "notes": [
            {
                "slot": "mp1",
                "text": "On weekdays that keep the Ascension or Pentecost, the Dignus es is said.",
                "canticles": ["dignus-es"],
            },
            {
                "slot": "mp2",
                "text": "On April 29 the Jubilate is said in place of the Benedictus.",
                "canticles": ["jubilate"],
            },
            {
                "slot": "ep1",
                "text": "On November 13 the Cantate Domino is said in place of the Magnificat.",
                "canticles": ["cantate-domino"],
            },
            {
                "slot": "ep2",
                "text": "In Epiphany and after Pentecost, the Nunc dimittis replaces the Deus misereatur "
                "whenever Psalm 67 is appointed that evening.",
                "canticles": ["nunc-dimittis", "deus-misereatur"],
            },
        ],
    },
    {
        "key": "1979",
        "setting_value": "1979",
        "name": "Daily Rotation",
        "description": "A rotating set of canticles by day of week and season.",
        "rules": BCP1979CanticleTable,
        "notes": [],
    },
]

INVITATORY_ROTATIONS = [
    {
        "key": "invitatory_traditional",
        "name": "Venite always",
        "description": "Always the Venite, except on days when Psalm 95 is appointed.",
        "appointments": [
            {"when": "Easter Week", "canticles": ["pascha-nostrum"]},
            {"when": "All other days", "canticles": ["venite"]},
            {"when": "When Psalm 95 is appointed", "canticles": ["jubilate"]},
        ],
    },
    {
        "key": "invitatory_jubilate_on_feasts",
        "name": "Celebratory Sundays and feasts",
        "description": "The Jubilate on Sundays and feasts, the Venite on other days.",
        "appointments": [
            {"when": "Easter Week", "canticles": ["pascha-nostrum"]},
            {"when": "Sundays and feasts in Eastertide", "canticles": ["pascha-nostrum"]},
            {"when": "Sundays and feasts", "canticles": ["jubilate"]},
            {"when": "Other days", "canticles": ["venite"]},
        ],
    },
    {
        "key": "invitatory_rotating",
        "name": "Rotating each day",
        "description": "Alternate between the Venite and the Jubilate.",
        "appointments": [
            {"when": "Easter Week", "canticles": ["pascha-nostrum"]},
            {"when": "Every third day of Eastertide", "canticles": ["pascha-nostrum"]},
            {"when": "Alternating days", "canticles": ["venite", "jubilate"]},
        ],
    },
    {
        "key": "celebratory_always",
        "name": "Celebratory always",
        "description": "Always the Jubilate, or the Pascha Nostrum in Eastertide.",
        "appointments": [
            {"when": "Eastertide", "canticles": ["pascha-nostrum"]},
            {"when": "All other days", "canticles": ["jubilate"]},
            {"when": "When Psalm 100 is appointed", "canticles": ["venite"]},
        ],
    },
]

INVITATORY_NOTE = (
    "Whatever the setting, the invitatory is never the same as one of the day's appointed psalms: "
    "the Jubilate replaces the Venite when Psalm 95 is appointed, and the Venite replaces the "
    "Jubilate when Psalm 100 is."
)

# Lines that frame a text in the office (its titles and the rubric over it)
# rather than belong to it; the library shows those in its own header.
FRAME_LINE_TYPES = {"heading", "subheading", "rubric", "spacer"}


def _model_day(weekday, season, feast=False):
    """A stand-in for a churchcal day, just rich enough for the canticle rules."""
    rank = SimpleNamespace(
        precedence_rank=1 if feast else 7,
        name="PRINCIPAL_FEAST" if feast else "FERIA",
    )
    primary = SimpleNamespace(name="A Principal Feast" if feast else "A Weekday", rank=rank)
    return SimpleNamespace(
        date=MODEL_WEEK[weekday],
        season=SimpleNamespace(name=season),
        primary=primary,
        all=[primary],
    )


def _appointed(rules, slot, day):
    method = getattr(rules, slot["method"])
    if slot["key"] == "ep2" and isinstance(rules, REC2011CanticleTable):
        result = method(day, SimpleNamespace(ep_psalms=""))
    else:
        result = method(day)
    # A rule may answer differently for the thirty- and sixty-day psalters.
    results = result if isinstance(result, tuple) else (result,)
    return [CLASS_SLUGS[canticle] for canticle in results]


def rotation_table(rules):
    """Each day's canticles in every season, grouped where the seasons agree.

    Returns rows like ``{"key": "monday", "label": "Monday", "cells": {"mp1":
    [{"canticles": ["ecce-deus"], "seasons": []}]}}``; an empty ``seasons``
    list means every season.
    """
    rows = []
    for day in DAYS:
        cells = {}
        for slot in SLOTS:
            groups = []
            for season in SEASONS:
                canticles = _appointed(rules, slot, _model_day(day["weekday"], season["season"], day.get("feast")))
                group = next((g for g in groups if g["canticles"] == canticles), None)
                if group is None:
                    group = {"canticles": canticles, "seasons": []}
                    groups.append(group)
                group["seasons"].append(season["key"])
            if len(groups) == 1:
                groups[0]["seasons"] = []
            cells[slot["key"]] = groups
        rows.append({"key": day["key"], "label": day["label"], "days": [day["key"]], "cells": cells})

    # A rotation that never varies by day is shown as a single row.
    if all(row["cells"] == rows[0]["cells"] for row in rows):
        return [
            {"key": "every_day", "label": "Every day", "days": [day["key"] for day in DAYS], "cells": rows[0]["cells"]}
        ]

    # Neighbouring weekdays that agree share a row: "Monday – Friday".
    merged = []
    for row in rows:
        previous = merged[-1] if merged else None
        if previous and row["key"] != "feast" and previous["key"] != "feast" and previous["cells"] == row["cells"]:
            previous["days"].append(row["key"])
            first = next(day["label"] for day in DAYS if day["key"] == previous["days"][0])
            previous["label"] = f"{first} – {row['label']}"
            previous["key"] = f"{previous['days'][0]}-{row['key']}"
        else:
            merged.append(row)
    return merged


def _split_frame(lines):
    """Strip the office's titles and rubric, returning (body, citation)."""
    start = 0
    while start < len(lines) and lines[start]["line_type"] in FRAME_LINE_TYPES:
        start += 1
    body = lines[start:]
    citations = []
    while body and body[-1]["line_type"] == "citation":
        citations.insert(0, body[-1]["content"])
        body = body[:-1]
    return body, "; ".join(citations)


def _indent(value):
    # A few older text files spell it "hangingIdent".
    return "hangingIndent" if value == "hangingIdent" else value


def _clean(lines):
    return [
        {
            "content": line["content"].strip(),
            "line_type": line["line_type"],
            "indented": _indent(line.get("indented", False)),
            "extra_space_before": line.get("extra_space_before", False),
        }
        for line in lines
    ]


def _load(filename):
    """A text file's lines, with the padding of its columns trimmed."""
    lines = file_to_lines(filename) or []
    for line in lines:
        line["line_type"] = (line.get("line_type") or "congregation").strip()
        if isinstance(line.get("indented"), str):
            line["indented"] = line["indented"].strip()
        line["content"] = line["content"].strip()
    return lines


def _texts(filename, gloria):
    texts = {}
    citation = ""
    for style, suffix in (("contemporary", ""), ("traditional", "_traditional")):
        lines = _load(filename + suffix + ".csv") or _load(filename + ".csv")
        body, found_citation = _split_frame(lines)
        citation = citation or found_citation
        if gloria:
            body = body + _load("gloria_patri" + suffix + ".csv")
        texts[style] = _clean(body)
    return texts, citation


LATIN_PROPER = {"deus", "deum", "domine", "domini", "domino", "dominum", "pantokrator"}


def _latin_case(text):
    """'BENEDICTUS ES, DOMINE' -> 'Benedictus es, Domine', as the book sets it."""
    words = text.lower().split(" ")
    return " ".join(
        word[:1].upper() + word[1:] if index == 0 or word.strip(",") in LATIN_PROPER else word
        for index, word in enumerate(words)
    )


def _title_case(text):
    small = {"of", "the", "and", "to", "for", "a", "in"}
    words = text.lower().split(" ")
    return " ".join(
        word if index and word in small else word[:1].upper() + word[1:] for index, word in enumerate(words)
    )


def _canticle_entries():
    entries = []
    for invitatory in INVITATORIES:
        texts, citation = _texts(invitatory["file"], gloria=False)
        entries.append(
            {
                "slug": invitatory["slug"],
                "latin_name": _latin_case(invitatory["latin_name"]),
                "english_name": invitatory["english_name"],
                "citation": citation,
                "category": invitatory["category"],
                "suggested": invitatory["suggested"],
                "gloria": False,
                "notes": invitatory["notes"],
                "texts": texts,
            }
        )

    for canticle, slug in CLASS_SLUGS.items():
        if canticle is O2:
            continue
        texts, _ = _texts(canticle.template.replace(".html", ""), gloria=canticle.gloria)
        entries.append(
            {
                "slug": slug,
                "latin_name": _latin_case(canticle.latin_name),
                "english_name": canticle.english_name,
                "citation": _title_case(canticle.citation) if canticle.citation else "",
                "category": CANTICLE_CATEGORIES.get(canticle, "supplemental"),
                "suggested": list(canticle.seasons),
                "gloria": canticle.gloria,
                "notes": [],
                "texts": texts,
            }
        )
    return entries


def _uses(entries, rotations, invitatory_rotations):
    """Where each canticle is said: offices, rotations and slots."""
    uses = {entry["slug"]: {"offices": set(), "rotations": set(), "slots": set()} for entry in entries}

    for rotation in rotations:
        for row in rotation["rows"]:
            for slot in SLOTS:
                for group in row["cells"][slot["key"]]:
                    for slug in group["canticles"]:
                        uses[slug]["offices"].add(slot["office"])
                        uses[slug]["rotations"].add(rotation["key"])
                        uses[slug]["slots"].add(slot["key"])
        for note in rotation["notes"]:
            office = next(slot["office"] for slot in SLOTS if slot["key"] == note["slot"])
            for slug in note["canticles"]:
                uses[slug]["offices"].add(office)
                uses[slug]["rotations"].add(rotation["key"])
                uses[slug]["slots"].add(note["slot"])

    for rotation in invitatory_rotations:
        for appointment in rotation["appointments"]:
            for slug in appointment["canticles"]:
                uses[slug]["offices"].add("morning")
                uses[slug]["slots"].add("invitatory")

    uses["phos-hilaron"]["offices"].add("evening")
    uses["phos-hilaron"]["slots"].add("evening_hymn")
    uses["nunc-dimittis"]["offices"].add("compline")
    uses["nunc-dimittis"]["slots"].add("compline")
    # The Gloria in excelsis is not appointed by any rotation; the rubrics
    # allow it in place of a canticle, most often at Morning Prayer.
    uses["gloria-in-excelsis"]["offices"].add("morning")

    office_order = [office["key"] for office in OFFICES]
    rotation_order = [rotation["key"] for rotation in rotations]
    return {
        slug: {
            "offices": sorted(use["offices"], key=office_order.index),
            "rotations": sorted(use["rotations"], key=rotation_order.index),
            "slots": sorted(use["slots"]),
        }
        for slug, use in uses.items()
    }


@lru_cache(maxsize=1)
def canticle_library():
    """The whole library, as the Canticles page reads it."""
    rotations = [
        {
            "key": rotation["key"],
            "setting_value": rotation["setting_value"],
            "name": rotation["name"],
            "description": rotation["description"],
            "rows": rotation_table(rotation["rules"]()),
            "notes": rotation["notes"],
        }
        for rotation in ROTATIONS
    ]
    entries = _canticle_entries()
    uses = _uses(entries, rotations, INVITATORY_ROTATIONS)
    for entry in entries:
        entry.update(uses[entry["slug"]])

    return {
        "canticles": entries,
        "categories": CATEGORIES,
        "offices": OFFICES,
        "seasons": [{"key": season["key"], "label": season["label"]} for season in SEASONS],
        "slots": [{key: slot[key] for key in ("key", "office", "label")} for slot in SLOTS],
        "rotations": rotations,
        "invitatory_rotations": INVITATORY_ROTATIONS,
        "invitatory_note": INVITATORY_NOTE,
    }

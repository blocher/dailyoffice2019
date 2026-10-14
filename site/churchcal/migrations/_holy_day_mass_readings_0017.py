"""Seed logic for migration 0017.

import_mass_readings mapped the sheet codes "Paul" and "JohnTheBaptist" to the
wrong commemorations ("Peter and Paul, Apostles" and "The Beheading of John the
Baptist"), so the Conversion of Paul (January 25) and the Nativity of John the
Baptist (June 24) had no Holy Eucharist readings. This moves those rows to the
right holy days, creating them if they are missing, and links each citation to
an office.Scripture row the way import_scripture and
link_mass_readings_to_scripture do.

The readings are those appointed in the BCP 2019 Sunday, Holy Day, and
Commemoration Lectionary (p. 730), the same for Years A, B, and C. Citations
are formatted as import_mass_readings formats them (e.g. "Acts 13:14b-26"
becomes "Acts 13:14-26").
"""

CALENDAR = "ACNA_BCP2019"

# (abbreviation, commemoration name, readings)
# reading: (reading_number, order, reading_type, book, testament, long_citation)
HOLY_DAYS = (
    (
        "Paul",
        "Conversion of Paul the Apostle",
        (
            (1, 873, "epistle", "Acts", "NT", "Acts 26:9-21"),
            (2, 874, "psalm", "Psalms", "OT", "Psalms 67"),
            (3, 875, "epistle", "Galatians", "NT", "Galatians 1:11-24"),
            (4, 876, "gospel", "Matthew", "NT", "Matthew 10:16-25"),
        ),
    ),
    (
        "JohnTheBaptist",
        "The Nativity of John the Baptist",
        (
            (1, 911, "prophecy", "Isaiah", "OT", "Isaiah 40:1-11"),
            (2, 912, "psalm", "Psalms", "OT", "Psalms 85:7-13"),
            (3, 913, "epistle", "Acts", "NT", "Acts 13:14-26"),
            (4, 914, "gospel", "Luke", "NT", "Luke 1:57-80"),
        ),
    ),
)


def scripture_for(Scripture, passage):
    if not passage:
        return None
    scripture = Scripture.objects.filter(passage__iexact=passage).first()
    if not scripture:
        scripture = Scripture.objects.create(passage=passage)
    return scripture


def text_for(MassReading, scripture, citation):
    existing = MassReading.objects.filter(long_citation=citation).exclude(long_text__isnull=True).first()
    if existing:
        return existing.long_text
    return scripture.esv if scripture else None


def forward(apps, schema_editor):
    Calendar = apps.get_model("churchcal", "Calendar")
    Commemoration = apps.get_model("churchcal", "Commemoration")
    MassReading = apps.get_model("churchcal", "MassReading")
    Scripture = apps.get_model("office", "Scripture")

    calendar = Calendar.objects.filter(abbreviation=CALENDAR).first()
    if not calendar:
        return

    for abbreviation, name, readings in HOLY_DAYS:
        commemoration = Commemoration.objects.filter(calendar=calendar, name=name).first()
        if not commemoration:
            continue
        for reading_number, order, reading_type, book, testament, citation in readings:
            reading = MassReading.objects.filter(
                calendar=calendar, abbreviation=abbreviation, long_citation=citation
            ).first()
            if not reading:
                reading = MassReading(
                    calendar=calendar,
                    abbreviation=abbreviation,
                    long_citation=citation,
                    short_citation="",
                    service="",
                    years="ABC",
                    reading_type=reading_type,
                    book=book,
                    testament=testament,
                    reading_number=reading_number,
                    order=order,
                )
            reading.commemoration = commemoration
            reading.proper = None
            reading.common = None
            if not reading.long_scripture_id:
                reading.long_scripture = scripture_for(Scripture, reading.long_citation)
            if reading.short_citation and not reading.short_scripture_id:
                reading.short_scripture = scripture_for(Scripture, reading.short_citation)
            if not reading.long_text:
                reading.long_text = text_for(MassReading, reading.long_scripture, reading.long_citation)
            reading.save()


def backward(apps, schema_editor):
    # Pointing the readings back at the wrong holy days would only restore the bug.
    pass

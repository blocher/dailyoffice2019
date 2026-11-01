"""The log of content changes that devices use to refresh offline downloads.

See ``office.models.ContentChange`` for how devices use it. This module writes
entries (admin edits, ``manage.py invalidate_offline``) and summarizes the
entries after a version for ``/api/v1/content_changes``.
"""

import datetime
import logging

from django.utils import timezone

from office.models import ContentChange

logger = logging.getLogger(__name__)

# Admin edits to these never change an office, a reading, or the calendar, so
# they leave downloads alone. Keys are (app_label, model).
IGNORED_APPS = {"admin", "auth", "contenttypes", "sessions", "analytics", "patrons", "podcasts"}
IGNORED_MODELS = {
    ("office", "contentchange"),
    ("office", "sitemessage"),
    ("office", "audioclip"),
    ("office", "pronunciationoverride"),
    ("office", "updatenotice"),
}

# More entries than this after a version: the device refreshes everything,
# rather than reading a long list.
MAX_ENTRIES = 200

# Entries are kept this long: longer than any device keeps a download (60
# days ahead). A device that last synced before the oldest one refreshes
# everything (changes_since).
KEEP_FOR = datetime.timedelta(days=180)


def record_change(start_date=None, end_date=None, urgent=False, source=ContentChange.SOURCE_MANUAL, note=""):
    if start_date and not end_date:
        end_date = start_date
    if start_date and end_date and end_date < start_date:
        start_date, end_date = end_date, start_date
    ContentChange.objects.filter(created__lt=timezone.now() - KEEP_FOR).delete()
    return ContentChange.objects.create(
        start_date=start_date,
        end_date=end_date,
        urgent=urgent,
        source=source,
        note=(note or "")[:255],
    )


def affects_offline_content(log_entry):
    content_type = getattr(log_entry, "content_type", None)
    if content_type is None:
        return False
    if content_type.app_label in IGNORED_APPS:
        return False
    return (content_type.app_label, content_type.model) not in IGNORED_MODELS


def record_admin_change(log_entry):
    """A soft, every-date change for an admin add, change, or delete.

    Admin edits can't be mapped to dates reliably (the lectionary is keyed by
    month and day, collects and canticles by rank and season), so they cover
    every date, softly: devices refresh today and tomorrow now, and the rest
    as each day comes near.
    """
    if not affects_offline_content(log_entry):
        return None
    content_type = log_entry.content_type
    note = f"{content_type.app_label}.{content_type.model}: {log_entry.object_repr or ''}"
    try:
        return record_change(source=ContentChange.SOURCE_ADMIN, note=note)
    except Exception:
        # Never let the offline log break an admin save.
        logger.warning("Could not record an offline content change", exc_info=True)
        return None


def latest_version():
    # Ids as versions: two entries saved at the same moment could commit out
    # of order, and a device reading between them would miss the first. Each
    # entry is one short autocommit insert, so the window is tiny; accepted.
    return ContentChange.objects.order_by("-id").values_list("id", flat=True).first() or 0


def changes_since(since):
    """What changed after version ``since``, for devices.

    Returns ``{"version", "all", "urgent", "dates"}``:

    - ``dates`` lists the ``[first, last]`` ISO date ranges of dated changes
      (merged where they touch). Devices always refresh these at once.
    - ``all`` is true when some change covers every date, and ``urgent`` when
      one of those is urgent (devices refresh everything at once rather than
      as each day comes near). Dated changes don't make ``all`` urgent, and
      an every-date change doesn't hide the dated ones.

    A device that has never synced (``since`` missing or 0) only learns the
    current version: it has nothing old to refresh.
    """
    version = latest_version()
    summary = {"version": version, "all": False, "urgent": False, "dates": []}
    if not since or since >= version:
        return summary
    oldest = ContentChange.objects.order_by("id").values_list("id", flat=True).first()
    if oldest and since < oldest - 1:
        # Entries after `since` have been removed (KEEP_FOR): what they said
        # is unknown, so everything is out of date.
        summary.update({"all": True, "urgent": True})
        return summary
    entries = list(
        ContentChange.objects.filter(id__gt=since)
        .order_by("id")
        .values("start_date", "end_date", "urgent")[: MAX_ENTRIES + 1]
    )
    if len(entries) > MAX_ENTRIES:
        summary.update({"all": True, "urgent": any(e["urgent"] for e in entries)})
        return summary
    ranges = []
    for entry in entries:
        if not entry["start_date"]:
            summary["all"] = True
            summary["urgent"] = summary["urgent"] or entry["urgent"]
            continue
        ranges.append((entry["start_date"], entry["end_date"] or entry["start_date"]))
    summary["dates"] = [[start.isoformat(), end.isoformat()] for start, end in merge_ranges(ranges)]
    return summary


def merge_ranges(ranges):
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + datetime.timedelta(days=1):
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

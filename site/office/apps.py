from django.apps import AppConfig
from django.db.models.signals import post_save


def clear_office_cache_on_admin_change(sender, **kwargs):
    """Every admin add/change/delete writes a LogEntry; show the edit at once.

    Cleared after commit, so a request racing the save cannot re-cache old data.
    """
    from django.db import transaction

    from office import response_cache

    transaction.on_commit(response_cache.clear)


def record_offline_change_on_admin_change(sender, instance=None, created=False, **kwargs):
    """Admin edits also tell devices to refresh their offline downloads.

    See office/offline_content.py. Recorded after commit, like the cache clear.
    """
    if not created or instance is None:
        return
    from django.db import transaction

    from office import offline_content

    transaction.on_commit(lambda: offline_content.record_admin_change(instance))


def announce_bulk_admin_log_entries():
    """Send ``post_save`` for log entries the admin writes in bulk.

    ``LogEntryManager.log_actions`` saves one entry normally but uses
    ``bulk_create`` for several (the "Delete selected" action), which sends no
    signals: without this, a bulk delete would neither clear the response cache
    nor tell devices to refresh.
    """
    from django.contrib.admin.models import LogEntry, LogEntryManager

    original = LogEntryManager.log_actions
    if getattr(original, "announces_bulk_entries", False):
        return

    def log_actions(self, *args, **kwargs):
        entries = original(self, *args, **kwargs)
        if isinstance(entries, list) and len(entries) > 1:
            for entry in entries:
                post_save.send(sender=LogEntry, instance=entry, created=True, raw=False, using=self.db)
        return entries

    log_actions.announces_bulk_entries = True
    LogEntryManager.log_actions = log_actions


class OfficeConfig(AppConfig):
    name = "office"

    def ready(self):
        from django.contrib.admin.models import LogEntry

        announce_bulk_admin_log_entries()

        post_save.connect(
            clear_office_cache_on_admin_change, sender=LogEntry, dispatch_uid="office_response_cache_admin_clear"
        )
        post_save.connect(
            record_offline_change_on_admin_change,
            sender=LogEntry,
            dispatch_uid="office_offline_content_admin_change",
        )

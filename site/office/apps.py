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
    nor tell devices to refresh. The entries are for one queryset, so the first
    one speaks for them all: one cache clear and one change, however many rows.
    """
    from django.contrib.admin.models import LogEntry, LogEntryManager

    original = LogEntryManager.log_actions
    if getattr(original, "announces_bulk_entries", False):
        return

    def log_actions(self, *args, **kwargs):
        entries = original(self, *args, **kwargs)
        if isinstance(entries, list) and len(entries) > 1:
            post_save.send(sender=LogEntry, instance=entries[0], created=True, raw=False, using=self.db)
        return entries

    log_actions.announces_bulk_entries = True
    LogEntryManager.log_actions = log_actions


def run_delete_selected_atomically():
    """Run the admin's "Delete selected" action in a transaction.

    It logs the deletions before deleting, and nothing else makes it atomic, so
    the after-commit cache clear and change record above would run before the
    rows were gone: a device syncing in between would store the old content as
    new. Inside a transaction they wait for the delete to commit (and a delete
    that fails part way leaves nothing deleted).
    """
    from django.contrib import admin
    from django.contrib.admin.actions import delete_selected
    from django.db import transaction

    action = admin.site.get_action("delete_selected")
    if getattr(action, "runs_atomically", False):
        return
    atomic_delete_selected = transaction.atomic(delete_selected)
    atomic_delete_selected.runs_atomically = True
    admin.site.add_action(atomic_delete_selected, "delete_selected")


class OfficeConfig(AppConfig):
    name = "office"

    def ready(self):
        from django.contrib.admin.models import LogEntry

        announce_bulk_admin_log_entries()
        run_delete_selected_atomically()

        post_save.connect(
            clear_office_cache_on_admin_change, sender=LogEntry, dispatch_uid="office_response_cache_admin_clear"
        )
        post_save.connect(
            record_offline_change_on_admin_change,
            sender=LogEntry,
            dispatch_uid="office_offline_content_admin_change",
        )

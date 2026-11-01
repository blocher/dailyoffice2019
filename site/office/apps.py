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


class OfficeConfig(AppConfig):
    name = "office"

    def ready(self):
        from django.contrib.admin.models import LogEntry

        post_save.connect(
            clear_office_cache_on_admin_change, sender=LogEntry, dispatch_uid="office_response_cache_admin_clear"
        )
        post_save.connect(
            record_offline_change_on_admin_change,
            sender=LogEntry,
            dispatch_uid="office_offline_content_admin_change",
        )

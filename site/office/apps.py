from django.apps import AppConfig
from django.db.models.signals import post_save


def clear_office_cache_on_admin_change(sender, **kwargs):
    """Every admin add/change/delete writes a LogEntry; show the edit at once.

    Cleared after commit, so a request racing the save cannot re-cache old data.
    """
    from django.db import transaction

    from office import response_cache

    transaction.on_commit(response_cache.clear)


class OfficeConfig(AppConfig):
    name = "office"

    def ready(self):
        from django.contrib.admin.models import LogEntry

        post_save.connect(
            clear_office_cache_on_admin_change, sender=LogEntry, dispatch_uid="office_response_cache_admin_clear"
        )

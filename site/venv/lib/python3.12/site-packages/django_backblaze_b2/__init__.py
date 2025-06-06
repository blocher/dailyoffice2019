import django_backblaze_b2.urls as urls

from .storage import BackblazeB2Storage
from .storages import LoggedInStorage, PublicStorage, StaffStorage

__version__ = "7.0.0"
__all__ = ["PublicStorage", "LoggedInStorage", "StaffStorage", "BackblazeB2Storage", "urls"]

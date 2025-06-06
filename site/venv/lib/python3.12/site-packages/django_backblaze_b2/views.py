import logging
import mimetypes
from typing import Union

from b2sdk.v1.exception import FileNotPresent
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin

from django_backblaze_b2 import storage, storages

from ._decorators import _requires_login

logger = logging.getLogger("django-backblaze-b2")


@xframe_options_sameorigin
def download_public_file(request: HttpRequest, filename: str) -> Union[HttpResponse, FileResponse]:
    """Serves the specified 'filename' without validating any authentication"""
    return _download_file_from_storage(storages.PublicStorage(), filename)


@_requires_login()
@xframe_options_sameorigin
def download_logged_in_file(request: HttpRequest, filename: str) -> Union[HttpResponse, FileResponse]:
    """Serves the specified 'filename' validating the user is logged in"""
    return _download_file_from_storage(storages.LoggedInStorage(), filename)


@_requires_login(requires_staff=True)
@xframe_options_sameorigin
def download_staff_file(request: HttpRequest, filename: str) -> Union[HttpResponse, FileResponse]:
    """Serves the specified 'filename' validating the user is logged in and a staff user"""
    return _download_file_from_storage(storages.StaffStorage(), filename)


def _download_file_from_storage(
    storage: storage.BackblazeB2Storage, filename: str
) -> Union[HttpResponse, FileResponse]:
    if logger.isEnabledFor(logging.DEBUG):
        try:
            logger.debug(f"Downloding file from {storage.get_backblaze_url(filename)}")
        except Exception:
            logger.exception(f"Debug log failed. Could not retrive b2 file url for {filename}")

    try:
        if storage.exists(filename):
            content_type, _encoding = mimetypes.guess_type(filename)
            return FileResponse(storage.open(filename, "r"), content_type=content_type)
    except (FileNotFoundError, FileNotPresent):
        logging.exception("Opening backblaze file failed")

    return HttpResponseNotFound(_("Could not find file") + f": {filename}")

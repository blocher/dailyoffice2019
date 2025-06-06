import re
from typing import Optional, Union, cast

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from typing_extensions import Literal, TypedDict, TypeVar, override

from django_backblaze_b2.options import (
    BackblazeB2StorageOptions,
    CDNConfig,
    PossibleB2StorageOptions,
    ProxiedBucketNames,
)
from django_backblaze_b2.storage import BackblazeB2Storage, logger


class _SdkBucketDict(TypedDict):
    """See https://github.com/Backblaze/b2-sdk-python/blob/2c85182c82ee09b7db7216d70567aafb87f31536/b2sdk/bucket.py#L1148"""  # noqa: E501

    bucketType: Literal["allPublic", "allPrivate"]  # noqa: N815


class PublicStorage(BackblazeB2Storage):
    """
    Storage that requires no authentication to view.
    If the bucket is public, returns the bucket's url, or CDN if configured
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._bucket_type: Optional[Literal["allPublic", "allPrivate"]] = None
        self._cdn_config: Optional[CDNConfig] = kwargs.get("opts", {}).get("cdn_config")

    @override
    def _get_file_url(self, name: str) -> str:
        if not self._is_public_bucket():
            return reverse("django_b2_storage:b2-public", args=[name])
        if self._cdn_config:
            file_url = self.get_backblaze_url(name)
            cdn_url_base = self._cdn_config["base_url"].replace("https://", "").replace("http://", "").strip("/")
            if self._cdn_config["include_bucket_url_segments"]:
                return re.sub(r"f\d+\.backblazeb2\.com", cdn_url_base, file_url)
            return re.sub(r"f\d+\.backblazeb2\.com/file/[^/]+/", cdn_url_base + "/", file_url)
        return self.get_backblaze_url(name)

    def _is_public_bucket(self) -> bool:
        if self._bucket_type is None:
            bucket_dict: _SdkBucketDict = self.bucket.as_dict()
            if bucket_dict.get("bucketType") is None:  # sometimes this happens due to cached values
                logger.debug(f"Re-retrieving bucket info for {bucket_dict}")
                self._refresh_bucket()
                bucket_dict = self.bucket.as_dict()
            self._bucket_type = bucket_dict.get("bucketType")
        return self._bucket_type == "allPublic"

    @override
    def _validate_options(self, options: PossibleB2StorageOptions, from_constructor: bool = False) -> None:
        super()._validate_options(options, from_constructor)
        if from_constructor:
            _validate_proxy_class_options(options)
        if options.get("cdn_config"):
            if not isinstance(options["cdn_config"], dict):
                raise ImproperlyConfigured("django-backblaze-b2 cdn_config must be a dict")
            if not isinstance(options["cdn_config"].get("base_url"), str):
                raise ImproperlyConfigured("cdn_config.base_url must be a string")
            if not isinstance(options["cdn_config"].get("include_bucket_url_segments"), bool):
                logger.debug("will treat cdn_config.include_bucket_url_segments to False")

    @override
    def _extract_constructor_options(
        self, constructor_kwargs: PossibleB2StorageOptions, opts_args: PossibleB2StorageOptions
    ) -> PossibleB2StorageOptions:
        extracted = super()._extract_constructor_options(constructor_kwargs, opts_args)
        return _with_bucket_name_extracted_from_settings(extracted, specific_bucket="public")

    @override
    def _get_options_from_django_settings(self) -> BackblazeB2StorageOptions:
        from_settings = super()._get_options_from_django_settings()
        return _with_bucket_name_extracted_from_settings(from_settings, specific_bucket="public")


class LoggedInStorage(BackblazeB2Storage):
    """Storage that requires authentication to view or download files"""

    @override
    def _get_file_url(self, name: str) -> str:
        return reverse("django_b2_storage:b2-logged-in", args=[name])

    @override
    def _validate_options(self, options: PossibleB2StorageOptions, from_constructor: bool = False) -> None:
        super()._validate_options(options, from_constructor)
        if from_constructor:
            _validate_proxy_class_options(options)

    @override
    def _extract_constructor_options(
        self, constructor_kwargs: PossibleB2StorageOptions, opts_args: PossibleB2StorageOptions
    ) -> PossibleB2StorageOptions:
        extracted = super()._extract_constructor_options(constructor_kwargs, opts_args)
        return _with_bucket_name_extracted_from_settings(extracted, specific_bucket="logged_in")

    @override
    def _get_options_from_django_settings(self) -> BackblazeB2StorageOptions:
        from_settings = super()._get_options_from_django_settings()
        return _with_bucket_name_extracted_from_settings(from_settings, specific_bucket="logged_in")


class StaffStorage(BackblazeB2Storage):
    """Storage that requires staff permission to view or download files"""

    @override
    def _get_file_url(self, name: str) -> str:
        return reverse("django_b2_storage:b2-staff", args=[name])

    @override
    def _validate_options(self, options: PossibleB2StorageOptions, from_constructor: bool = False) -> None:
        super()._validate_options(options, from_constructor)
        if from_constructor:
            _validate_proxy_class_options(options)

    @override
    def _extract_constructor_options(
        self, constructor_kwargs: PossibleB2StorageOptions, opts_args: PossibleB2StorageOptions
    ) -> PossibleB2StorageOptions:
        extracted = super()._extract_constructor_options(constructor_kwargs, opts_args)
        return _with_bucket_name_extracted_from_settings(extracted, specific_bucket="staff")

    @override
    def _get_options_from_django_settings(self) -> BackblazeB2StorageOptions:
        from_settings = super()._get_options_from_django_settings()
        return _with_bucket_name_extracted_from_settings(from_settings, specific_bucket="staff")


def _validate_proxy_class_options(options: PossibleB2StorageOptions) -> None:
    if "bucket" in options:
        raise ImproperlyConfigured("May not specify 'bucket' in proxied storage class")
    if "application_key_id" in options or "application_key" in options or "realm" in options:
        raise ImproperlyConfigured("May not specify auth credentials in proxied storage class")


B2Opts = TypeVar("B2Opts", bound=Union[BackblazeB2StorageOptions, PossibleB2StorageOptions])


def _with_bucket_name_extracted_from_settings(
    options: B2Opts, specific_bucket: Literal["public", "staff", "logged_in"]
) -> B2Opts:
    proxied_storage_bucket_name = (
        cast(PossibleB2StorageOptions, options).get("specific_bucket_names", ProxiedBucketNames()).get(specific_bucket)
    )
    if proxied_storage_bucket_name:
        return cast(B2Opts, {**options, "bucket": options["specific_bucket_names"][specific_bucket]})
    return cast(B2Opts, {**options})

from datetime import datetime
from hashlib import sha3_224 as hash
from logging import getLogger
from typing import IO, Any, Callable, Dict, List, Optional, Tuple, cast

from b2sdk.v2 import AbstractAccountInfo, AuthInfoCache, B2Api, Bucket, InMemoryAccountInfo, SqliteAccountInfo
from b2sdk.v2.exception import FileNotPresent, NonExistentBucket
from django.core.cache.backends.base import BaseCache
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from typing_extensions import NotRequired, TypedDict, TypeVar, Unpack

from django_backblaze_b2.b2_file import B2File
from django_backblaze_b2.cache_account_info import DjangoCacheAccountInfo
from django_backblaze_b2.options import (
    BackblazeB2StorageOptions,
    DjangoCacheAccountInfoConfig,
    PossibleB2StorageOptions,
    SqliteAccountInfoConfig,
    get_default_b2_storage_options,
)

logger = getLogger("django-backblaze-b2")


class _SdkBaseFileInfoDict(TypedDict):
    """See https://github.com/Backblaze/b2-sdk-python/blob/2c85182c82ee09b7db7216d70567aafb87f31536/b2sdk/file_version.py"""  # noqa: E501

    fileId: str  # noqa: N815
    fileName: str  # noqa: N815
    fileInfo: dict  # noqa: N815


class _SdkFileInfoDict(_SdkBaseFileInfoDict, total=False):
    """See https://github.com/Backblaze/b2-sdk-python/blob/2c85182c82ee09b7db7216d70567aafb87f31536/b2sdk/file_version.py#L143"""  # noqa: E501

    size: int
    uploadTimestamp: int  # noqa: N815
    contentType: str  # noqa: N815


class B2FileInformationNotAvailableException(Exception):  # noqa: N818
    ...


class BackblazeB2StorageConstructorArgs(PossibleB2StorageOptions):
    opts: NotRequired[PossibleB2StorageOptions]


@deconstructible
class BackblazeB2Storage(Storage):
    """Storage class which fulfills the Django Storage contract through b2 apis"""

    def __init__(self, **kwargs: Unpack[BackblazeB2StorageConstructorArgs]):
        constructor_options = self._extract_constructor_options(
            cast(PossibleB2StorageOptions, kwargs), kwargs.pop("opts", PossibleB2StorageOptions())
        )
        django_settings_options = self._get_options_from_django_settings()
        opts = _merge(source=constructor_options, into=django_settings_options)  # type: ignore[arg-type]
        logger.debug(
            f"Initializing {self.__class__.__name__} with options "
            + str({**opts, "application_key_id": "<redacted>", "application_key": "<redacted>"})
        )

        self._bucket_name = opts["bucket"]
        self._default_file_metadata = opts["default_file_info"]
        self._forbid_file_property_caching = opts["forbid_file_property_caching"]
        self._authInfo = dict(
            [(k, v) for k, v in opts.items() if k in ["realm", "application_key_id", "application_key"]]
        )
        self._allow_file_overwrites = opts["allow_file_overwrites"]

        self._get_account_info = self._create_account_info_callable(opts)

        logger.info(f"{self.__class__.__name__} instantiated to use bucket {self._bucket_name}")
        if opts["authorize_on_init"]:
            logger.debug(f"{self.__class__.__name__} authorizing")
            self.b2_api
            if opts["validate_on_init"]:
                self._get_or_create_bucket(opts["non_existent_bucket_details"])

    def _extract_constructor_options(
        self, constructor_kwargs: PossibleB2StorageOptions, opts_args: PossibleB2StorageOptions
    ) -> PossibleB2StorageOptions:
        if constructor_kwargs and opts_args:
            raise ImproperlyConfigured("Can only specify opts or keyword args, not both!")
        options = constructor_kwargs or opts_args
        self._validate_options(options, from_constructor=True)
        return options

    def _get_options_from_django_settings(self) -> BackblazeB2StorageOptions:
        """Setting terminology taken from:
        https://b2-sdk-python.readthedocs.io/en/master/glossary.html#term-application-key-ID
        kwargOpts available for subclasses
        """
        from django.conf import settings

        if not hasattr(settings, "BACKBLAZE_CONFIG"):
            raise ImproperlyConfigured("add BACKBLAZE_CONFIG dict to django settings")
        if "application_key_id" not in settings.BACKBLAZE_CONFIG or "application_key" not in settings.BACKBLAZE_CONFIG:
            raise ImproperlyConfigured(
                "At minimum BACKBLAZE_CONFIG must contain auth 'application_key' and 'application_key_id'"
                f"\nfound: {settings.BACKBLAZE_CONFIG}"
            )
        self._validate_options(cast(PossibleB2StorageOptions, settings.BACKBLAZE_CONFIG))
        opts = get_default_b2_storage_options()
        opts.update(settings.BACKBLAZE_CONFIG)  # type: ignore[typeddict-item]
        return opts

    def _validate_options(self, options: PossibleB2StorageOptions, from_constructor: bool = False) -> None:
        unrecognized_options = [k for k in options.keys() if k not in get_default_b2_storage_options().keys()]
        if unrecognized_options:
            raise ImproperlyConfigured(f"Unrecognized options: {unrecognized_options}")

    def _create_account_info_callable(self, opts: BackblazeB2StorageOptions) -> Callable[[], AbstractAccountInfo]:
        if (
            not isinstance(opts["account_info"], dict)
            or "type" not in opts["account_info"]
            or opts["account_info"]["type"] not in ["memory", "sqlite", "django-cache"]
        ):
            raise ImproperlyConfigured(
                (f"'account_info' property must be a dict with type found in options.py, was {opts['account_info']}")
            )
        if opts["account_info"]["type"] == "django-cache":
            logger.debug(f"{self.__class__.__name__} will use {DjangoCacheAccountInfo.__name__}")
            return lambda: DjangoCacheAccountInfo(
                cache_name=cast(DjangoCacheAccountInfoConfig, opts["account_info"]).get("cache", "django-backblaze-b2")
            )
        elif opts["account_info"]["type"] == "memory":
            logger.debug(f"{self.__class__.__name__} will use {InMemoryAccountInfo.__name__}")
            return lambda: InMemoryAccountInfo()
        elif opts["account_info"]["type"] == "sqlite":
            logger.debug(f"{self.__class__.__name__} will use {SqliteAccountInfo.__name__}")
            return lambda: SqliteAccountInfo(
                file_name=cast(SqliteAccountInfoConfig, opts["account_info"])["database_path"]
            )
        raise ImproperlyConfigured()

    @property
    def b2_api(self) -> B2Api:
        if not hasattr(self, "_b2_api"):
            self._account_info = self._get_account_info()
            self._b2_api = B2Api(account_info=self._account_info, cache=AuthInfoCache(self._account_info))
            self._b2_api.authorize_account(**self._authInfo)
        return self._b2_api

    @property
    def bucket(self) -> Bucket:
        if not hasattr(self, "_bucket"):
            self._get_or_create_bucket()
        return self._bucket

    def _get_or_create_bucket(self, new_bucket_details=None) -> None:
        try:
            self._bucket = self.b2_api.get_bucket_by_name(self._bucket_name)
        except NonExistentBucket as e:
            if new_bucket_details is not None:
                logger.debug(f"Bucket {self._bucket_name} not found. Creating with details: {new_bucket_details}")
                if "bucket_type" not in new_bucket_details:
                    new_bucket_details["bucket_type"] = "allPrivate"
                self._bucket = self.b2_api.create_bucket(name=self._bucket_name, **new_bucket_details)
            else:
                raise e
        logger.debug(f"Connected to bucket {self._bucket.as_dict()}")

    def _refresh_bucket(self) -> Bucket:
        if self._bucket:
            return self._bucket.get_fresh_state()
        return self.bucket

    def _open(self, name: str, mode: str) -> File:
        return B2File(
            name=name,
            bucket=self.bucket,
            file_metadata=self._default_file_metadata,
            mode=mode,
            size_provider=self.size,
        )

    def _save(self, name: str, content: IO[Any]) -> str:
        """
        Save and retrieve the filename.
        If the file exists it will make another version of that file.
        """
        return B2File(
            name=name,
            bucket=self.bucket,
            file_metadata=self._default_file_metadata,
            mode="w",
            size_provider=self.size,
        ).save_and_retrieve_file(content)

    def path(self, name: str) -> str:
        return name

    def delete(self, name: str) -> None:
        file_info = self._file_info(name)
        if file_info:
            logger.debug(f"Deleting file {name} id=({file_info['fileId']})")
            self.b2_api.delete_file_version(file_id=file_info["fileId"], file_name=name)
            if self._cache:
                self._cache.delete(self._file_cache_key(name))
        else:
            logger.debug("Not found")

    def _file_info(self, name: str) -> Optional[_SdkFileInfoDict]:
        try:
            if self._cache:
                cache_key = self._file_cache_key(name)
                timeout_in_seconds = 60

                def load_info():
                    logger.debug(f"file info cache miss for {name}")
                    return self.bucket.get_file_info_by_name(name).as_dict()

                return self._cache.get_or_set(key=cache_key, default=load_info, timeout=timeout_in_seconds)
            return self.bucket.get_file_info_by_name(name).as_dict()
        except FileNotPresent:
            return None

    def _file_cache_key(self, name: str) -> str:
        return hash(f"{self.bucket.name}__{name}".encode()).hexdigest()

    @property
    def _cache(self) -> Optional[BaseCache]:
        if (
            not self._forbid_file_property_caching
            and self.b2_api  # force init
            and self._account_info
            and isinstance(self._account_info, DjangoCacheAccountInfo)
        ):
            return self._account_info.cache
        return None

    def exists(self, name: str) -> bool:
        return bool(self._file_info(name))

    def size(self, name: str) -> int:
        file_info = self._file_info(name)
        return file_info.get("size", 0) if file_info else 0

    def url(self, name: Optional[str]) -> str:
        if not name:
            raise Exception("Name must be defined")
        return self._get_file_url(name)

    def _get_file_url(self, name: str) -> str:
        return self.get_backblaze_url(name)

    def get_backblaze_url(self, filename: str) -> str:
        return self.b2_api.get_download_url_for_file_name(bucket_name=self._bucket_name, file_name=filename)

    def get_available_name(self, name: str, max_length: Optional[int] = None) -> str:
        if self._allow_file_overwrites:
            return name
        return super().get_available_name(name, max_length)

    def listdir(self, path: str) -> Tuple[List[str], List[str]]:
        """
        List the contents of the specified path. Return a 2-tuple of lists:
        the first item being directories, the second item being files.
        """
        raise NotImplementedError("subclasses of Storage must provide a listdir() method")

    def get_accessed_time(self, name: str) -> datetime:
        """
        Return the last accessed time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        raise NotImplementedError("subclasses of Storage must provide a get_accessed_time() method")

    def get_created_time(self, name: str) -> datetime:
        """
        Return the creation time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        from datetime import timezone

        from django.conf import settings

        file_info = self._file_info(name)
        try:
            if file_info and float(file_info.get("uploadTimestamp", 0)) > 0:
                timestamp = float(file_info["uploadTimestamp"]) / 1000.0
                if settings.USE_TZ:
                    return datetime.fromtimestamp(timestamp, timezone.utc)
                return datetime.fromtimestamp(timestamp)
        except ValueError as e:
            raise B2FileInformationNotAvailableException(f"'uploadTimestamp' from API not valid for {name}: {e}")
        raise B2FileInformationNotAvailableException(f"'uploadTimestamp' not available for {name}")

    def get_modified_time(self, name: str) -> datetime:
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        return self.get_created_time(name)


T = TypeVar("T")


def _merge(source: Dict, into: T, path=None) -> T:
    """merges b into a
    https://stackoverflow.com/a/7205107/11076240
    """
    target = cast(dict, into)  # easier to read 'target' within function body
    merged = target.copy()
    if path is None:
        path = []
    for key in source:
        if key in target:
            printable_path = ".".join(path + [str(key)])
            if isinstance(target[key], dict) and isinstance(source[key], dict):
                merged[key] = _merge(source=source[key], into=target[key], path=path + [str(key)])
            elif target[key] != source[key]:
                logger.debug(f"Overriding setting {printable_path} '{target[key]}' with value '{source[key]}'")
                merged[key] = source[key]
        else:
            merged[key] = source[key]
    return cast(T, merged)

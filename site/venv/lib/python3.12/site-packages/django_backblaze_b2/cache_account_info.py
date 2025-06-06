import logging
import threading
from functools import wraps
from hashlib import sha3_224 as hash
from typing import Iterable, List, Optional, Tuple

from b2sdk.v2 import UrlPoolAccountInfo
from b2sdk.v2.exception import MissingAccountData
from django.core.cache import InvalidCacheBackendError, caches
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger("django-backblaze-b2")


class StoredBucketInfo:
    name: str
    id_: str


def _handle_result_is_none(item_name=None):
    """
    Raise MissingAccountData if function's result is None.
    adapted from https://github.com/Backblaze/b2-sdk-python/blob/v1.5.0/b2sdk/account_info/in_memory.py
    """

    def wrapper_factory(function):
        @wraps(function)
        def getter_function(self, *args, **kwargs):
            assert function.__name__.startswith("get_")
            result = function(self, *args, **kwargs)
            if result is None:
                self.cache.clear()
                raise MissingAccountData(
                    f"Token refresh required to determine value of '{item_name or function.__name__[len('get_') :]}'",
                )
            return result

        return getter_function

    return wrapper_factory


class DjangoCacheAccountInfo(UrlPoolAccountInfo):
    """
    Store account information in django's cache: https://docs.djangoproject.com/en/3.1/topics/cache

    Threadsafe only in the context of its own runtime,
    i.e. it's possible (unlikely though, only in a highly concurrent scenario) that a
    wrapper of Django could launch 2+ different processes, which would not share threads,
    and within the 'locked' blocks, mutation of values between cache accesses
    """

    def __init__(self, cache_name: str):
        logger.debug(f"Initializing {self.__class__.__name__} with cache '{cache_name}'")
        self._cache_name = cache_name
        self._cache_lock = threading.Lock()
        try:
            self.cache = caches[cache_name]
            self.cache.set("bucket_names", [])
        except InvalidCacheBackendError:
            logger.exception("Cache assignment failed")
            from django.conf import settings

            help_message = (
                (
                    ". "
                    "The default 'account_info' option of this library is with a django cache"
                    " by the name of 'django-backblaze-b2'"
                )
                if "account_info" not in settings.BACKBLAZE_CONFIG
                else ""
            )

            raise ImproperlyConfigured(
                f"Expected to find a cache with name '{cache_name}' as per options" + help_message
            )
        super(DjangoCacheAccountInfo, self).__init__()

    def clear(self):
        """
        Remove all info about accounts and buckets.
        """
        logger.debug("Clearing cache info")
        self.cache.clear()
        self.cache.set("bucket_names", [])

    def _set_auth_data(
        self,
        account_id,
        auth_token,
        api_url,
        download_url,
        recommended_part_size,
        absolute_minimum_part_size,
        application_key,
        realm,
        s3_api_url,
        allowed,
        application_key_id,
    ):
        logger.debug("New auth data set")
        old_value = self._cached_info()
        new_value = {
            "account_id": account_id,
            "auth_token": auth_token,
            "api_url": api_url,
            "download_url": download_url,
            "recommended_part_size": recommended_part_size,
            "absolute_minimum_part_size": absolute_minimum_part_size,
            "application_key": application_key,
            "realm": realm,
            "s3_api_url": s3_api_url,
            "allowed": allowed,
            "application_key_id": application_key_id,
        }
        if len(old_value.keys()) == 0:
            logger.debug("all auth values updated")
        else:
            logger.debug(
                "auth values updated: "
                + ", ".join(dict([(k, v) for (k, v) in new_value.items() if old_value.get(k) != new_value[k]]).keys())
            )
        self.cache.set(
            "cached_account_info",
            new_value,
            timeout=None,
        )

    def _cached_info(self):
        return self.cache.get("cached_account_info", default={})

    @_handle_result_is_none()
    def get_application_key(self):
        return self._cached_info().get("application_key")

    @_handle_result_is_none()
    def get_application_key_id(self):
        return self._cached_info().get("application_key_id")

    @_handle_result_is_none()
    def get_account_id(self):
        return self._cached_info().get("account_id")

    @_handle_result_is_none()
    def get_api_url(self):
        return self._cached_info().get("api_url")

    @_handle_result_is_none("auth_token")
    def get_account_auth_token(self):
        """Named different from cached value"""
        return self._cached_info().get("auth_token")

    @_handle_result_is_none()
    def get_download_url(self):
        return self._cached_info().get("download_url")

    @_handle_result_is_none()
    def get_realm(self):
        return self._cached_info().get("realm")

    @_handle_result_is_none()
    def get_absolute_minimum_part_size(self):
        return self._cached_info().get("absolute_minimum_part_size")

    @_handle_result_is_none()
    def get_recommended_part_size(self):
        return self._cached_info().get("recommended_part_size")

    @_handle_result_is_none()
    def get_allowed(self):
        return self._cached_info().get("allowed")

    def get_s3_api_url(self):
        return self._cached_info().get("s3_api_url") or ""

    def get_bucket_id_or_none_from_bucket_name(self, bucket_name: str) -> Optional[str]:
        try:
            return self.cache.get(_bucket_cachekey(bucket_name))
        except KeyError as e:
            logger.debug(f"cache miss {bucket_name}: {e}")
            return None

    def get_bucket_name_or_none_from_bucket_id(self, bucket_id: str) -> Optional[str]:
        try:
            self._cache_lock.acquire()
            for bucket_name in self.cache.get("bucket_names", []):
                cached_id = self.cache.get(_bucket_cachekey(bucket_name))
                if cached_id and cached_id == bucket_id:
                    return bucket_name
            logger.debug(f"cache miss {bucket_id}")
        except KeyError as e:
            logger.debug(f"cache miss {bucket_id}: {e}")
        finally:
            self._cache_lock.release()
        return None

    def refresh_entire_bucket_name_cache(self, name_id_iterable: Iterable[Tuple[str, str]]):
        with self._cache_lock:
            new_bucket_names = set()
            for bucket_name, bucket_id in name_id_iterable:
                self.cache.set(_bucket_cachekey(bucket_name), bucket_id)
                new_bucket_names.add(bucket_name)

            buckets_to_remove = [n for n in self.cache.get("bucket_names", []) if n not in new_bucket_names]
            for bucket_name in buckets_to_remove:
                self.cache.delete(_bucket_cachekey(bucket_name))

            self.cache.set("bucket_names", list(new_bucket_names))

    def save_bucket(self, bucket: StoredBucketInfo):
        with self._cache_lock:
            self.cache.set(_bucket_cachekey(bucket.name), bucket.id_)
            self.cache.set("bucket_names", self.cache.get("bucket_names", []) + [bucket.name])

    def remove_bucket_name(self, bucket_name):
        with self._cache_lock:
            self.cache.set("bucket_names", [n for n in self.cache.get("bucket_names", []) if n != bucket_name])
            self.cache.delete(_bucket_cachekey(bucket_name))

    def list_bucket_names_ids(self) -> List[Tuple[str, str]]:
        tuples = []
        with self._cache_lock:
            for bucket_name in self.cache.get("bucket_names", []):
                bucket_id = self.cache.get(_bucket_cachekey(bucket_name))
                tuples.append((bucket_name, bucket_id))
        return tuples

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{{cache_name={self._cache_name}, cache={self.cache}}}"


def _bucket_cachekey(bucket_name: str) -> str:
    return hash(f"bucket-name__{bucket_name}".encode()).hexdigest()

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from typing_extensions import Literal, TypedDict


class PossibleB2StorageOptions(TypedDict, total=False):
    realm: str  # default "production"
    application_key_id: str
    application_key: str
    bucket: str
    authorize_on_init: bool
    validate_on_init: bool
    allow_file_overwrites: bool
    account_info: Optional[Union[DjangoCacheAccountInfoConfig, InMemoryAccountInfoConfig, SqliteAccountInfoConfig]]
    forbid_file_property_caching: bool
    specific_bucket_names: ProxiedBucketNames
    cdn_config: Optional[CDNConfig]
    # see: https://b2-sdk-python.readthedocs.io/en/master/api/api.html#b2sdk.v1.B2Api.create_bucket
    non_existent_bucket_details: Optional[Dict[str, Union[str, Dict[str, Any]]]]
    default_file_info: Dict[str, Any]


class BackblazeB2StorageOptions(TypedDict):
    realm: str
    application_key_id: str
    application_key: str
    bucket: str
    authorize_on_init: bool
    validate_on_init: bool
    allow_file_overwrites: bool
    account_info: Optional[Union[DjangoCacheAccountInfoConfig, InMemoryAccountInfoConfig, SqliteAccountInfoConfig]]
    forbid_file_property_caching: bool
    specific_bucket_names: ProxiedBucketNames
    cdn_config: Optional[CDNConfig]
    non_existent_bucket_details: Optional[Dict[str, Union[str, Dict[str, Any]]]]
    default_file_info: Dict[str, Any]


def get_default_b2_storage_options() -> BackblazeB2StorageOptions:
    return {
        "realm": "production",
        "application_key_id": "you must set this value yourself",
        "application_key": "you must set this value yourself",
        "bucket": "django",
        "authorize_on_init": True,
        "validate_on_init": True,
        "allow_file_overwrites": False,
        "account_info": {"type": "django-cache", "cache": "django-backblaze-b2"},
        "forbid_file_property_caching": False,
        "specific_bucket_names": {"public": None, "logged_in": None, "staff": None},
        "cdn_config": None,
        "non_existent_bucket_details": None,
        "default_file_info": {},
    }


class ProxiedBucketNames(TypedDict, total=False):
    public: Optional[str]
    logged_in: Optional[str]
    staff: Optional[str]


class DjangoCacheAccountInfoConfig(TypedDict):
    type: Literal["django-cache"]
    cache: str


class InMemoryAccountInfoConfig(TypedDict):
    type: Literal["memory"]


class SqliteAccountInfoConfig(TypedDict):
    type: Literal["sqlite"]
    database_path: str


class CDNConfig(TypedDict):
    base_url: str
    include_bucket_url_segments: bool

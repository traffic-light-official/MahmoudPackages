"""Enterprise API version lifecycle management for Django REST Framework.

The public API is intentionally small. Most projects only need:

* One of the versioning schemes in :mod:`~drf_api_versioning.versioning`
  (a drop-in replacement for the matching DRF built-in class).
* :class:`~drf_api_versioning.mixins.DeprecationHeaderMixin` for the
  ``Deprecation``/``Sunset``/``Link`` response headers.
* :data:`~drf_api_versioning.signals.deprecated_version_used` to hook
  in your own usage analytics.

but the registry (:mod:`~drf_api_versioning.registry`) is importable
directly for anything else (a custom admin page, a health check).
"""

from __future__ import annotations

from drf_api_versioning.exceptions import APIVersionSunsetError, UnknownAPIVersionError
from drf_api_versioning.mixins import DeprecationHeaderMixin
from drf_api_versioning.registry import VersionInfo, all_versions, get_version_info
from drf_api_versioning.signals import deprecated_version_used
from drf_api_versioning.versioning import (
    AcceptHeaderVersioning,
    HostNameVersioning,
    NamespaceVersioning,
    QueryParameterVersioning,
    URLPathVersioning,
)

__version__ = "1.0.0"

__all__ = [
    "APIVersionSunsetError",
    "AcceptHeaderVersioning",
    "DeprecationHeaderMixin",
    "HostNameVersioning",
    "NamespaceVersioning",
    "QueryParameterVersioning",
    "URLPathVersioning",
    "UnknownAPIVersionError",
    "VersionInfo",
    "__version__",
    "all_versions",
    "deprecated_version_used",
    "get_version_info",
]

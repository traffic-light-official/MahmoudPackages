"""Read-only accessors over the ``API_VERSIONING`` setting's version metadata."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from django.utils import timezone

from drf_api_versioning.settings import get_setting


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Metadata for one declared API version."""

    name: str
    deprecated_on: datetime.date | None
    sunset_on: datetime.date | None
    deprecation_link: str | None

    def is_deprecated(self, *, as_of: datetime.date | None = None) -> bool:
        """Whether this version is deprecated as of ``as_of`` (default: today).

        "Today" is Django's own current date (``timezone.now().date()``,
        respecting ``USE_TZ``/``TIME_ZONE``), not the server process's
        local system date - the two can differ by a day around midnight
        depending on server and configured timezone.
        """
        if self.deprecated_on is None:
            return False
        return (as_of or timezone.now().date()) >= self.deprecated_on

    def is_sunset(self, *, as_of: datetime.date | None = None) -> bool:
        """Whether this version is past its sunset date as of ``as_of`` (default: today).

        See :meth:`is_deprecated` for what "today" means here.
        """
        if self.sunset_on is None:
            return False
        return (as_of or timezone.now().date()) >= self.sunset_on


def all_version_names() -> tuple[str, ...]:
    """Return every declared version name, in declaration order."""
    versions: dict[str, dict[str, object]] = get_setting("VERSIONS")
    return tuple(versions)


def all_versions() -> tuple[VersionInfo, ...]:
    """Return :class:`VersionInfo` for every declared version, in declaration order."""
    return tuple(get_version_info(name) for name in all_version_names())


def get_version_info(name: str) -> VersionInfo:
    """Return the :class:`VersionInfo` for a declared version.

    Args:
        name: A version name, e.g. ``"v1"``.

    Raises:
        KeyError: If ``name`` is not declared in the ``VERSIONS`` setting.
    """
    versions: dict[str, dict[str, datetime.date | str | None]] = get_setting("VERSIONS")
    entry = versions[name]
    deprecated = entry.get("deprecated")
    sunset = entry.get("sunset")
    link = entry.get("deprecation_link")
    return VersionInfo(
        name=name,
        deprecated_on=_as_date(deprecated),
        sunset_on=_as_date(sunset),
        deprecation_link=link if isinstance(link, str) else None,
    )


def default_version_name() -> str | None:
    """Return the configured ``DEFAULT_VERSION``, or ``None`` if unset."""
    value: str | None = get_setting("DEFAULT_VERSION")
    return value


def _as_date(value: object) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None

"""Registry-aware versioning schemes.

Each class here subclasses one of DRF's built-in versioning schemes,
so the request-side resolution mechanics (URL kwarg, ``Accept`` header
parameter, query parameter, URL namespace, or hostname) are entirely
DRF's own, unchanged. What's added is: ``allowed_versions``/
``default_version`` are computed from the ``API_VERSIONING`` registry
instead of DRF's own global ``ALLOWED_VERSIONS``/``DEFAULT_VERSION``
settings, unknown versions raise
:class:`~drf_api_versioning.exceptions.UnknownAPIVersionError` (naming
the specific value that was rejected, unlike DRF's generic
``NotFound``/``NotAcceptable``), a version past its sunset date raises
:class:`~drf_api_versioning.exceptions.APIVersionSunsetError` (HTTP
410) unless ``ALLOW_SUNSET`` is set, and a deprecated version fires
:data:`~drf_api_versioning.signals.deprecated_version_used`.
"""

from __future__ import annotations

from typing import Any

from rest_framework import versioning
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.utils.mediatypes import _MediaType

from drf_api_versioning import registry
from drf_api_versioning.exceptions import APIVersionSunsetError, UnknownAPIVersionError
from drf_api_versioning.settings import get_setting
from drf_api_versioning.signals import deprecated_version_used


class _RegistryVersioningMixin(versioning.BaseVersioning):
    """Shared registry-awareness for every concrete scheme below.

    Inherits from :class:`~rest_framework.versioning.BaseVersioning`
    itself (in addition to being mixed in alongside a concrete scheme
    that already does) purely so mypy understands that
    ``allowed_versions``/``default_version``/``determine_version``
    genuinely override the same base members on both sides of the
    diamond - this does not change the runtime MRO in any
    problematic way, since both branches already share
    ``BaseVersioning`` as their common ancestor.
    """

    @property
    def allowed_versions(self) -> tuple[str, ...]:
        """The declared version names - always in sync with the registry."""
        return registry.all_version_names()

    @allowed_versions.setter
    def allowed_versions(self, value: object) -> None:
        """No-op: DRF's ``BaseVersioning`` never assigns this at runtime."""

    @property
    def default_version(self) -> str | None:
        """The registry's configured ``DEFAULT_VERSION``."""
        return registry.default_version_name()

    @default_version.setter
    def default_version(self, value: object) -> None:
        """No-op: DRF's ``BaseVersioning`` never assigns this at runtime."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        """Best-effort extraction of the raw, rejected version string."""
        raise NotImplementedError

    def determine_version(  # type: ignore[override]
        self, request: Request, *args: Any, **kwargs: Any
    ) -> str | None:
        """Resolve the version via the wrapped scheme, then enforce registry rules.

        The ``# type: ignore[override]`` is for a stub imprecision, not a
        real Liskov violation: djangorestframework-stubs types
        ``BaseVersioning.determine_version`` as returning ``str``
        unconditionally, but DRF's actual ``NamespaceVersioning`` (at
        least) really can return ``None`` at runtime (when
        ``default_version`` is ``None`` and no namespace matches) - our
        signature reflects that real behavior.
        """
        try:
            version = super().determine_version(request, *args, **kwargs)
        except APIException as exc:
            raise UnknownAPIVersionError(
                self._raw_version(request, kwargs),
                registry.all_version_names(),
                status_code=exc.status_code,
            ) from exc

        if version is None:
            # Only reachable for NamespaceVersioning with no matching
            # namespace: it returns ``default_version`` directly without
            # calling ``is_allowed_version`` at all, so ``None`` can come
            # back unvalidated. Every other scheme calls
            # ``is_allowed_version`` unconditionally, which - since our
            # ``allowed_versions`` is always non-empty - already rejects
            # an unresolvable version before this method ever sees it.
            return None

        info = registry.get_version_info(version)
        if info.is_sunset() and not get_setting("ALLOW_SUNSET"):
            raise APIVersionSunsetError(version, info.sunset_on)
        if info.is_deprecated():
            deprecated_version_used.send(
                sender=type(self), request=request, version=version, version_info=info
            )
        return version


class URLPathVersioning(_RegistryVersioningMixin, versioning.URLPathVersioning):
    """:class:`rest_framework.versioning.URLPathVersioning`, registry-aware."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        return str(kwargs.get(self.version_param, "<missing>"))


class NamespaceVersioning(_RegistryVersioningMixin, versioning.NamespaceVersioning):
    """:class:`rest_framework.versioning.NamespaceVersioning`, registry-aware."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        resolver_match = getattr(request, "resolver_match", None)
        namespace = getattr(resolver_match, "namespace", None) if resolver_match else None
        return str(namespace or "<missing>")


class AcceptHeaderVersioning(_RegistryVersioningMixin, versioning.AcceptHeaderVersioning):
    """:class:`rest_framework.versioning.AcceptHeaderVersioning`, registry-aware."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        media_type = _MediaType(request.accepted_media_type)
        return str(media_type.params.get(self.version_param, "<missing>"))


class QueryParameterVersioning(_RegistryVersioningMixin, versioning.QueryParameterVersioning):
    """:class:`rest_framework.versioning.QueryParameterVersioning`, registry-aware."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        return str(request.query_params.get(self.version_param, "<missing>"))


class HostNameVersioning(_RegistryVersioningMixin, versioning.HostNameVersioning):
    """:class:`rest_framework.versioning.HostNameVersioning`, registry-aware."""

    def _raw_version(self, request: Request, kwargs: dict[str, Any]) -> str:
        hostname, _sep, _port = request.get_host().partition(":")
        match = self.hostname_regex.match(hostname)
        return match.group(1) if match else hostname

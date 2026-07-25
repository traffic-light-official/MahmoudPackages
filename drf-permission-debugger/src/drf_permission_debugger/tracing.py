"""The recorded outcome of one permission check, and a trace of all of them.

Recording is purely observational: :mod:`drf_permission_debugger.mixins`
calls DRF's own ``permission.has_permission()``/
``has_object_permission()`` exactly as ``APIView.check_permissions()``/
``check_object_permissions()`` already do, in the same order, stopping
at the same first denial - a :class:`PermissionTrace` never changes
what would have happened without it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PermissionCheckResult:
    """The outcome of checking one permission class against one request.

    Attributes:
        permission_class: The permission class's name, e.g. ``"IsAuthenticated"``.
        granted: Whether this permission granted the request.
        object_level: Whether this was an object-level check
            (``has_object_permission``) rather than a request-level one
            (``has_permission``).
        message: The permission's ``.message`` attribute, captured only
            when ``granted`` is ``False`` (DRF only consults it on
            denial, so it's ``None`` on a grant even if the attribute
            is set to something).
        code: The permission's ``.code`` attribute, captured the same
            way as ``message``.
    """

    permission_class: str
    granted: bool
    object_level: bool = False
    message: str | None = None
    code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Render as a plain, JSON-serializable dict."""
        return {
            "permission_class": self.permission_class,
            "granted": self.granted,
            "object_level": self.object_level,
            "message": self.message,
            "code": self.code,
        }


@dataclass
class PermissionTrace:
    """Every permission check result recorded for one request, in order checked."""

    results: list[PermissionCheckResult] = field(default_factory=list)

    @property
    def denied_by(self) -> PermissionCheckResult | None:
        """The first result that denied the request, or ``None`` if none did."""
        for result in self.results:
            if not result.granted:
                return result
        return None

    @property
    def all_granted(self) -> bool:
        """Whether every recorded check granted the request."""
        return all(result.granted for result in self.results)

    def as_dict(self) -> list[dict[str, Any]]:
        """Render every result as a plain, JSON-serializable list."""
        return [result.as_dict() for result in self.results]

    def as_header_value(self) -> str:
        """Render as a compact, single-line summary suitable for a response header.

        e.g. ``"IsAuthenticated=granted, IsAdminUser=denied"``.
        """
        return ", ".join(
            f"{result.permission_class}={'granted' if result.granted else 'denied'}"
            for result in self.results
        )

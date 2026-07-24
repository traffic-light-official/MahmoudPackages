"""The :class:`ProblemDetail` value object, modeling RFC 9457.

RFC 9457 ("Problem Details for HTTP APIs") defines four core members
(``type``, ``title``, ``status``, ``detail``, ``instance``) and explicitly
allows arbitrary "extension members" for additional, application-specific
information. :class:`ProblemDetail` models the core members as typed
fields and everything else as a free-form ``extensions`` mapping, so callers
get type safety for the RFC-defined fields without losing extensibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from drf_error_response_standardizer.constants import ABOUT_BLANK


@dataclass(frozen=True, slots=True)
class ProblemDetail:
    """An RFC 9457 Problem Details object.

    Attributes:
        status: The HTTP status code for this occurrence of the problem.
            Required to be included in the response body per RFC 9457 to
            preserve status information across proxies/logs, even though
            it also appears as the HTTP status line.
        title: A short, human-readable summary of the problem type that
            should not change between occurrences of the problem (e.g.
            "Validation Error" rather than "Field 'email' is invalid").
        type: A URI reference that identifies the problem type. Defaults
            to ``"about:blank"``, meaning "same as the HTTP status code".
        detail: A human-readable explanation specific to *this*
            occurrence of the problem.
        instance: A URI reference that identifies this specific
            occurrence of the problem, typically the request path.
        code: A machine-readable error code, stable across releases,
            intended for programmatic branching by API clients (RFC 9457
            deliberately leaves this to extension members; this package
            always includes one because "parse the English `title`" is
            not a viable integration strategy).
        extensions: Additional extension members, merged into the
            top-level JSON object alongside the fields above (e.g.
            ``errors``, ``correlation_id``, ``trace_id``, ``timestamp``).
    """

    status: int
    title: str
    type: str = ABOUT_BLANK
    detail: str | None = None
    instance: str | None = None
    code: str | None = None
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the JSON-compatible dict written to the response body.

        Core members with a value of ``None`` are omitted (RFC 9457 treats
        ``detail`` and ``instance`` as optional); ``type`` and ``title``
        and ``status`` are always present. Extension members are merged in
        last so a caller-supplied extension can never accidentally shadow
        a core member's key.

        Returns:
            A dictionary ready to be passed as the ``data`` argument of a
            DRF ``Response``.
        """
        payload: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if self.instance is not None:
            payload["instance"] = self.instance
        if self.code is not None:
            payload["code"] = self.code
        for key, value in self.extensions.items():
            if key not in payload:
                payload[key] = value
        return payload

    def with_extensions(self, **extra: Any) -> ProblemDetail:
        """Return a copy of this problem with additional extension members merged in.

        Args:
            **extra: Extension members to add. Existing extensions with
                the same key are overwritten; core RFC members
                (``type``/``title``/``status``/``detail``/``instance``/``code``)
                are not affected even if a matching keyword is passed.

        Returns:
            A new :class:`ProblemDetail` instance; the original is left
            unmodified since instances are immutable.
        """
        merged = {**self.extensions, **extra}
        return ProblemDetail(
            status=self.status,
            title=self.title,
            type=self.type,
            detail=self.detail,
            instance=self.instance,
            code=self.code,
            extensions=merged,
        )

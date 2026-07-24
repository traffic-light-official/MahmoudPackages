"""Normalization of (possibly deeply nested) DRF validation errors.

:class:`rest_framework.exceptions.ValidationError` carries its ``detail`` as
an arbitrarily nested combination of ``dict`` (serializer field errors),
``list`` (either plain leaf messages, or per-item errors for ``many=True``
serializers / :class:`~rest_framework.serializers.ListField`), and
``ErrorDetail`` leaf values. This module flattens that structure into a flat
list of :class:`NormalizedError` objects, each with a JSON-Pointer-like
``pointer`` locating exactly which field failed, matching the ``errors``
extension member example from RFC 9457 Appendix A.3.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from rest_framework.exceptions import ValidationError

from drf_error_response_standardizer.constants import POINTER_SEPARATOR


@dataclass(frozen=True, slots=True)
class NormalizedError:
    """A single flattened validation error.

    Attributes:
        pointer: Path to the offending field, e.g. ``"author/email"`` for
            ``{"author": {"email": [...]}}``, or ``"tags/0"`` for the
            first entry of a ``tags`` list field. An empty string denotes
            a non-field (serializer-level) error.
        detail: The human-readable error message.
        code: The machine-readable error code DRF attached to the
            message (e.g. ``"required"``, ``"invalid"``, ``"max_length"``),
            or ``"invalid"`` if none was attached.
    """

    pointer: str
    detail: str
    code: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to the ``{"pointer", "detail", "code"}`` dict used in responses."""
        return {"pointer": self.pointer, "detail": self.detail, "code": self.code}


def normalize_validation_error(exc: ValidationError) -> list[NormalizedError]:
    """Flatten a DRF :class:`~rest_framework.exceptions.ValidationError` into a flat list.

    Args:
        exc: The validation error raised by a serializer, field, or view.

    Returns:
        A list of :class:`NormalizedError`, one per leaf error message,
        in a stable, depth-first order matching the structure of
        ``exc.detail``.

    Example:
        .. code-block:: python

            >>> from rest_framework.exceptions import ValidationError, ErrorDetail
            >>> exc = ValidationError(
            ...     {
            ...         "title": [ErrorDetail("This field is required.", code="required")],
            ...         "author": {"email": [ErrorDetail("Enter a valid email.", code="invalid")]},
            ...     }
            ... )
            >>> [e.pointer for e in normalize_validation_error(exc)]
            ['title', 'author/email']
    """
    return list(_walk(exc.detail, ""))


def _walk(detail: Any, prefix: str) -> Iterator[NormalizedError]:
    if isinstance(detail, dict):
        for key, value in detail.items():
            yield from _walk(value, _extend_pointer(prefix, str(key)))
    elif isinstance(detail, list):
        if any(isinstance(item, dict) for item in detail):
            # Per-item errors, e.g. many=True serializer or ListField of
            # nested serializers: each entry is that item's own error dict
            # (or an empty dict for a valid item, which contributes nothing).
            for index, item in enumerate(detail):
                if item:
                    yield from _walk(item, _extend_pointer(prefix, str(index)))
        else:
            for item in detail:
                yield NormalizedError(
                    pointer=prefix,
                    detail=str(item),
                    code=getattr(item, "code", None) or "invalid",
                )
    else:
        yield NormalizedError(
            pointer=prefix,
            detail=str(detail),
            code=getattr(detail, "code", None) or "invalid",
        )


def _extend_pointer(prefix: str, segment: str) -> str:
    return f"{prefix}{POINTER_SEPARATOR}{segment}" if prefix else segment

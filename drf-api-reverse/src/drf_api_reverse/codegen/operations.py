"""Parses OpenAPI paths into resource groups shared by views.py and urls.py.

One :class:`ResourceGroup` per top-level path segment
(:func:`drf_api_reverse.naming.resource_group_key`) becomes one
``ViewSet``. Within a group, each operation is classified as one of:

- a standard ``list``/``create`` (a path with exactly one, non-param
  segment - the group's own collection path)
- a standard ``retrieve``/``update``/``partial_update``/``destroy`` (a
  path with exactly two segments, the second a ``{param}``)
- a ``@action``-decorated custom method (a path with exactly three
  segments: the group's collection segment, one ``{param}``, and one
  more literal segment - e.g. ``/articles/{id}/comments/``)
- unsupported (anything deeper or with more than one path parameter),
  which is still recorded so the caller can emit a clear, honest
  comment rather than silently dropping the operation or generating
  code that does not work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from drf_api_reverse.naming import (
    is_param_segment,
    path_segments,
    resource_group_key,
    to_snake_case,
)

_HTTP_METHODS: tuple[str, ...] = (
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
)

_STANDARD_COLLECTION_METHODS = {"get": "list", "post": "create"}
_STANDARD_DETAIL_METHODS = {
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
}


@dataclass(frozen=True, slots=True)
class Operation:
    """One ``(path, method)`` operation from the schema."""

    path: str
    method: str
    operation_id: str | None
    kind: str
    """One of ``"collection"``, ``"detail"``, ``"nested_action"``, ``"unsupported"``."""
    drf_method_name: str | None = None
    """The ``ViewSet`` method name, if ``kind`` maps to one directly."""
    action_url_path: str | None = None
    """The literal URL segment, for ``kind == "nested_action"``."""


@dataclass(frozen=True, slots=True)
class ResourceGroup:
    """All operations sharing one top-level path segment."""

    key: str
    base_path: str
    operations: list[Operation] = field(default_factory=list)


def parse_resource_groups(schema: dict[str, Any]) -> list[ResourceGroup]:
    """Group every path+method operation in ``schema`` by resource.

    Args:
        schema: The full parsed OpenAPI document.

    Returns:
        One :class:`ResourceGroup` per distinct top-level resource,
        in first-seen order, each with its operations in path-then-
        method order.
    """
    paths: dict[str, Any] = schema.get("paths") or {}
    groups: dict[str, ResourceGroup] = {}

    for path, path_item in paths.items():
        key = resource_group_key(path)
        if key not in groups:
            groups[key] = ResourceGroup(key=key, base_path=_collection_path(path))
        operations_by_method = path_item or {}
        for method in _HTTP_METHODS:
            if method not in operations_by_method:
                continue
            operation_id = (operations_by_method[method] or {}).get("operationId")
            groups[key].operations.append(_classify(path, method, operation_id))

    return list(groups.values())


def _collection_path(path: str) -> str:
    segments = path_segments(path)
    first_literal = next((s for s in segments if not is_param_segment(s)), None)
    return f"/{first_literal}/" if first_literal else path


def _classify(path: str, method: str, operation_id: str | None) -> Operation:
    segments = path_segments(path)

    if len(segments) == 1 and not is_param_segment(segments[0]):
        drf_method = _STANDARD_COLLECTION_METHODS.get(method)
        if drf_method:
            return Operation(path, method, operation_id, "collection", drf_method_name=drf_method)
        return Operation(path, method, operation_id, "unsupported")

    if len(segments) == 2 and not is_param_segment(segments[0]) and is_param_segment(segments[1]):
        drf_method = _STANDARD_DETAIL_METHODS.get(method)
        if drf_method:
            return Operation(path, method, operation_id, "detail", drf_method_name=drf_method)
        return Operation(path, method, operation_id, "unsupported")

    if (
        len(segments) == 3
        and not is_param_segment(segments[0])
        and is_param_segment(segments[1])
        and not is_param_segment(segments[2])
    ):
        name = operation_id or f"{method}_{segments[2]}"
        return Operation(
            path,
            method,
            operation_id,
            "nested_action",
            drf_method_name=to_snake_case(name),
            action_url_path=segments[2],
        )

    return Operation(path, method, operation_id, "unsupported")

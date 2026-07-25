"""Structurally diffs two OpenAPI schema documents.

The classification of each change as breaking or non-breaking follows one
consistent rule: a change is breaking if and only if an API client that
was correctly following the *old* contract could stop working (get a
validation error, KeyError, or wrong behavior) against the *new* one,
without any change on its part. See ``docs/architecture.md`` for the full,
enumerated rule set.
"""

from __future__ import annotations

from typing import Any

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity
from drf_changelog_generator.diffing.refs import deref

_HTTP_METHODS: tuple[str, ...] = (
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
)


def diff_schemas(old: dict[str, Any], new: dict[str, Any]) -> SchemaDiff:
    """Diff two OpenAPI schema documents.

    Args:
        old: The earlier OpenAPI document.
        new: The later OpenAPI document.

    Returns:
        Every detected change, in a stable (path, then method) order.
    """
    changes: list[Change] = []
    old_paths: dict[str, Any] = old.get("paths") or {}
    new_paths: dict[str, Any] = new.get("paths") or {}

    for path in sorted(set(old_paths) | set(new_paths)):
        old_ops = dict(_operations(old_paths.get(path) or {}))
        new_ops = dict(_operations(new_paths.get(path) or {}))

        for method in sorted(set(old_ops) | set(new_ops)):
            old_op = old_ops.get(method)
            new_op = new_ops.get(method)
            if old_op is None:
                changes.append(
                    Change(
                        kind=ChangeKind.ENDPOINT_ADDED,
                        severity=Severity.NON_BREAKING,
                        path=path,
                        method=method,
                        location="",
                        message=f"Added {method.upper()} {path}",
                    )
                )
                continue
            if new_op is None:
                changes.append(
                    Change(
                        kind=ChangeKind.ENDPOINT_REMOVED,
                        severity=Severity.BREAKING,
                        path=path,
                        method=method,
                        location="",
                        message=f"Removed {method.upper()} {path}",
                    )
                )
                continue
            changes.extend(_diff_operation(old, new, path, method, old_op, new_op))

    return SchemaDiff(changes=changes)


def _operations(path_item: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [(method, path_item[method]) for method in _HTTP_METHODS if method in path_item]


def _diff_operation(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    path: str,
    method: str,
    old_op: dict[str, Any],
    new_op: dict[str, Any],
) -> list[Change]:
    changes: list[Change] = []
    old_deprecated = bool(old_op.get("deprecated"))
    new_deprecated = bool(new_op.get("deprecated"))
    if new_deprecated and not old_deprecated:
        changes.append(
            Change(
                kind=ChangeKind.ENDPOINT_DEPRECATED,
                severity=Severity.NON_BREAKING,
                path=path,
                method=method,
                location="",
                message=f"{method.upper()} {path} is now deprecated",
            )
        )
    elif old_deprecated and not new_deprecated:
        changes.append(
            Change(
                kind=ChangeKind.ENDPOINT_UNDEPRECATED,
                severity=Severity.NON_BREAKING,
                path=path,
                method=method,
                location="",
                message=f"{method.upper()} {path} is no longer deprecated",
            )
        )

    changes.extend(
        _diff_parameters(
            path, method, old_op.get("parameters") or [], new_op.get("parameters") or []
        )
    )
    changes.extend(
        _diff_body(
            old_doc,
            new_doc,
            path,
            method,
            old_op.get("requestBody") or {},
            new_op.get("requestBody") or {},
            prefix="body",
            is_request=True,
        )
    )
    changes.extend(
        _diff_responses(
            old_doc,
            new_doc,
            path,
            method,
            old_op.get("responses") or {},
            new_op.get("responses") or {},
        )
    )
    return changes


def _param_key(parameter: dict[str, Any]) -> tuple[str, str]:
    return (parameter.get("name", ""), parameter.get("in", ""))


def _diff_parameters(
    path: str, method: str, old_params: list[dict[str, Any]], new_params: list[dict[str, Any]]
) -> list[Change]:
    changes: list[Change] = []
    old_by_key = {_param_key(p): p for p in old_params}
    new_by_key = {_param_key(p): p for p in new_params}

    for key in sorted(set(old_by_key) | set(new_by_key)):
        name, param_in = key
        old_param = old_by_key.get(key)
        new_param = new_by_key.get(key)
        location = f"parameters.{name}"

        if old_param is None:
            assert new_param is not None
            required = bool(new_param.get("required"))
            changes.append(
                Change(
                    kind=ChangeKind.PARAMETER_ADDED,
                    severity=Severity.BREAKING if required else Severity.NON_BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=(
                        f"Added {'required' if required else 'optional'} "
                        f"{param_in} parameter '{name}'"
                    ),
                )
            )
            continue
        if new_param is None:
            changes.append(
                Change(
                    kind=ChangeKind.PARAMETER_REMOVED,
                    severity=Severity.BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Removed {param_in} parameter '{name}'",
                )
            )
            continue

        old_required = bool(old_param.get("required"))
        new_required = bool(new_param.get("required"))
        if old_required != new_required:
            became_required = new_required and not old_required
            changes.append(
                Change(
                    kind=ChangeKind.PARAMETER_REQUIRED_CHANGED,
                    severity=Severity.BREAKING if became_required else Severity.NON_BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=(
                        f"Parameter '{name}' required changed: {old_required} -> {new_required}"
                    ),
                )
            )
    return changes


def _pick_schema(content: dict[str, Any], document: dict[str, Any]) -> dict[str, Any] | None:
    if not content:
        return None
    media_type = "application/json" if "application/json" in content else next(iter(content))
    schema = content[media_type].get("schema")
    return deref(document, schema) if schema is not None else None


def _diff_body(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    path: str,
    method: str,
    old_body: dict[str, Any],
    new_body: dict[str, Any],
    *,
    prefix: str,
    is_request: bool,
) -> list[Change]:
    old_schema = _pick_schema(old_body.get("content") or {}, old_doc)
    new_schema = _pick_schema(new_body.get("content") or {}, new_doc)
    return _diff_json_schema(
        old_doc,
        new_doc,
        old_schema,
        new_schema,
        path=path,
        method=method,
        prefix=prefix,
        is_request=is_request,
    )


def _diff_responses(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    path: str,
    method: str,
    old_responses: dict[str, Any],
    new_responses: dict[str, Any],
) -> list[Change]:
    changes: list[Change] = []
    for status in sorted(set(old_responses) | set(new_responses)):
        old_response = old_responses.get(status)
        new_response = new_responses.get(status)
        location = f"responses.{status}"

        if old_response is None:
            changes.append(
                Change(
                    kind=ChangeKind.RESPONSE_ADDED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Added {status} response",
                )
            )
            continue
        if new_response is None:
            changes.append(
                Change(
                    kind=ChangeKind.RESPONSE_REMOVED,
                    severity=Severity.BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Removed {status} response",
                )
            )
            continue

        changes.extend(
            _diff_body(
                old_doc,
                new_doc,
                path,
                method,
                old_response,
                new_response,
                prefix=location,
                is_request=False,
            )
        )
    return changes


def _diff_json_schema(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    old_schema: dict[str, Any] | None,
    new_schema: dict[str, Any] | None,
    *,
    path: str,
    method: str,
    prefix: str,
    is_request: bool,
) -> list[Change]:
    if old_schema is None or new_schema is None:
        return []

    changes: list[Change] = []
    old_properties: dict[str, Any] = old_schema.get("properties") or {}
    new_properties: dict[str, Any] = new_schema.get("properties") or {}
    old_required: set[str] = set(old_schema.get("required") or [])
    new_required: set[str] = set(new_schema.get("required") or [])

    field_added_kind = (
        ChangeKind.REQUEST_FIELD_ADDED if is_request else ChangeKind.RESPONSE_FIELD_ADDED
    )
    field_removed_kind = (
        ChangeKind.REQUEST_FIELD_REMOVED if is_request else ChangeKind.RESPONSE_FIELD_REMOVED
    )
    field_type_kind = (
        ChangeKind.REQUEST_FIELD_TYPE_CHANGED
        if is_request
        else ChangeKind.RESPONSE_FIELD_TYPE_CHANGED
    )

    for name in sorted(set(old_properties) | set(new_properties)):
        location = f"{prefix}.{name}"
        old_field = old_properties.get(name)
        new_field = new_properties.get(name)

        if old_field is None:
            required = name in new_required
            severity = Severity.BREAKING if is_request and required else Severity.NON_BREAKING
            changes.append(
                Change(
                    kind=field_added_kind,
                    severity=severity,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Added {'required ' if required else ''}field '{name}'",
                )
            )
            continue
        if new_field is None:
            changes.append(
                Change(
                    kind=field_removed_kind,
                    severity=Severity.BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Removed field '{name}'",
                )
            )
            continue

        old_field_schema = deref(old_doc, old_field)
        new_field_schema = deref(new_doc, new_field)
        old_type = old_field_schema.get("type")
        new_type = new_field_schema.get("type")

        if old_type is not None and new_type is not None and old_type != new_type:
            changes.append(
                Change(
                    kind=field_type_kind,
                    severity=Severity.BREAKING,
                    path=path,
                    method=method,
                    location=location,
                    message=f"Field '{name}' type changed: {old_type} -> {new_type}",
                )
            )

        if is_request:
            was_required = name in old_required
            now_required = name in new_required
            if was_required != now_required:
                became_required = now_required and not was_required
                changes.append(
                    Change(
                        kind=ChangeKind.REQUEST_FIELD_REQUIRED_CHANGED,
                        severity=Severity.BREAKING if became_required else Severity.NON_BREAKING,
                        path=path,
                        method=method,
                        location=location,
                        message=(
                            f"Field '{name}' required changed: {was_required} -> {now_required}"
                        ),
                    )
                )

        if (
            old_type == "array"
            and new_type == "array"
            and "items" in old_field_schema
            and "items" in new_field_schema
        ):
            old_items = deref(old_doc, old_field_schema["items"])
            new_items = deref(new_doc, new_field_schema["items"])
            changes.extend(
                _diff_json_schema(
                    old_doc,
                    new_doc,
                    old_items,
                    new_items,
                    path=path,
                    method=method,
                    prefix=f"{location}[]",
                    is_request=is_request,
                )
            )
        elif "properties" in old_field_schema or "properties" in new_field_schema:
            changes.extend(
                _diff_json_schema(
                    old_doc,
                    new_doc,
                    old_field_schema,
                    new_field_schema,
                    path=path,
                    method=method,
                    prefix=location,
                    is_request=is_request,
                )
            )

    return changes

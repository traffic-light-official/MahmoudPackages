"""Comparing two full OpenAPI schemas, operation by operation.

:func:`compare_schemas` is the top-level entry point: it walks every
operation (method + path) present in either schema, flags added/removed
endpoints, and for operations present in both, delegates to
:mod:`drf_contract_test.rules` to compare the request body and each
documented response, in the correct direction for each.
"""

from __future__ import annotations

from typing import Any

from drf_contract_test.changes import Change, DiffResult, Severity
from drf_contract_test.rules import Direction, compare_schema_objects
from drf_contract_test.schema import Schema


def compare_schemas(baseline: Schema, current: Schema) -> DiffResult:
    """Compare a baseline schema against a current one.

    Args:
        baseline: The previous/reference schema (e.g. your last release).
        current: The new schema to check for compatibility against
            ``baseline``.

    Returns:
        A :class:`~drf_contract_test.changes.DiffResult` listing every
        detected change and its severity.

    Example:
        >>> baseline = Schema({"paths": {"/x/": {"get": {"responses": {"200": {}}}}}})
        >>> current = Schema({"paths": {}})
        >>> result = compare_schemas(baseline, current)
        >>> result.has_breaking_changes
        True
    """
    changes: list[Change] = []
    baseline_ops = {(method, path): op for method, path, op in baseline.operations()}
    current_ops = {(method, path): op for method, path, op in current.operations()}

    for method, path in sorted(set(baseline_ops) - set(current_ops)):
        label = f"{method} {path}"
        changes.append(
            Change(Severity.BREAKING, label, "", "endpoint_removed", f"{label}: endpoint removed")
        )

    for method, path in sorted(set(current_ops) - set(baseline_ops)):
        label = f"{method} {path}"
        changes.append(
            Change(Severity.SAFE, label, "", "endpoint_added", f"{label}: endpoint added")
        )

    for method, path in sorted(set(baseline_ops) & set(current_ops)):
        label = f"{method} {path}"
        changes.extend(
            _compare_operation(
                baseline_ops[(method, path)],
                current_ops[(method, path)],
                operation=label,
                baseline=baseline,
                current=current,
            )
        )

    return DiffResult(changes=tuple(changes))


def _compare_operation(
    old_op: dict[str, Any],
    new_op: dict[str, Any],
    *,
    operation: str,
    baseline: Schema,
    current: Schema,
) -> list[Change]:
    changes: list[Change] = []
    changes.extend(
        _compare_request(old_op, new_op, operation=operation, baseline=baseline, current=current)
    )
    changes.extend(
        _compare_responses(old_op, new_op, operation=operation, baseline=baseline, current=current)
    )
    return changes


def _compare_request(
    old_op: dict[str, Any],
    new_op: dict[str, Any],
    *,
    operation: str,
    baseline: Schema,
    current: Schema,
) -> list[Change]:
    old_request = _request_schema(old_op)
    new_request = _request_schema(new_op)
    if old_request is None and new_request is None:
        return []
    if old_request is None:
        return [
            Change(
                Severity.SAFE,
                operation,
                "request",
                "request_body_added",
                f"{operation}: request body added",
            )
        ]
    if new_request is None:
        return [
            Change(
                Severity.BREAKING,
                operation,
                "request",
                "request_body_removed",
                f"{operation}: request body removed",
            )
        ]
    return compare_schema_objects(
        old_request,
        new_request,
        direction=Direction.REQUEST,
        location="request",
        operation=operation,
        old_root=baseline.raw,
        new_root=current.raw,
    )


def _compare_responses(
    old_op: dict[str, Any],
    new_op: dict[str, Any],
    *,
    operation: str,
    baseline: Schema,
    current: Schema,
) -> list[Change]:
    changes: list[Change] = []
    old_responses = _response_schemas(old_op)
    new_responses = _response_schemas(new_op)

    for status in sorted(set(old_responses) - set(new_responses)):
        changes.append(
            Change(
                Severity.BREAKING,
                operation,
                f"responses.{status}",
                "response_removed",
                f"{operation}: documented response {status} removed",
            )
        )
    for status in sorted(set(new_responses) - set(old_responses)):
        changes.append(
            Change(
                Severity.SAFE,
                operation,
                f"responses.{status}",
                "response_added",
                f"{operation}: new documented response {status}",
            )
        )
    for status in sorted(set(old_responses) & set(new_responses)):
        changes.extend(
            compare_schema_objects(
                old_responses[status],
                new_responses[status],
                direction=Direction.RESPONSE,
                location=f"responses.{status}",
                operation=operation,
                old_root=baseline.raw,
                new_root=current.raw,
            )
        )
    return changes


def _request_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content") or {}
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return None
    schema = json_content.get("schema")
    return schema if isinstance(schema, dict) else None


def _response_schemas(operation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    responses = operation.get("responses") or {}
    result: dict[str, dict[str, Any]] = {}
    for status_code, response_obj in responses.items():
        if not isinstance(response_obj, dict):
            continue
        content = response_obj.get("content") or {}
        json_content = content.get("application/json")
        if isinstance(json_content, dict) and isinstance(json_content.get("schema"), dict):
            result[str(status_code)] = json_content["schema"]
    return result

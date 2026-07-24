"""Generating contract tests from an OpenAPI schema, and validating live
responses against them.

:func:`generate_contract_cases` turns every documented ``(operation,
response status)`` pair into a :class:`ContractCase`. Hand these to your
own pytest parametrization (see ``docs/testing.md``) to call the real
endpoint and check the real response against what's documented —
catching drift between your code and your published contract, in either
direction.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

import jsonschema

from drf_contract_test.schema import Schema

_MAX_INLINE_DEPTH = 40


@dataclass(frozen=True, slots=True)
class ContractCase:
    """One documented ``(operation, response status)`` pair to test.

    Attributes:
        operation: ``"<METHOD> <path>"``, e.g. ``"GET /articles/{id}/"``.
        method: The HTTP method, uppercase.
        path: The path template, e.g. ``"/articles/{id}/"``.
        expected_status: The documented status code, as a string
            (e.g. ``"200"``).
        response_schema: The (still possibly ``$ref``-containing) schema
            for this response's ``application/json`` body, or ``None`` if
            none is documented.
    """

    operation: str
    method: str
    path: str
    expected_status: str
    response_schema: dict[str, Any] | None


def generate_contract_cases(
    schema: Schema, *, statuses: Collection[str] | None = None
) -> list[ContractCase]:
    """Build one :class:`ContractCase` per documented response.

    Args:
        schema: The OpenAPI schema to generate cases from.
        statuses: If given, only status codes in this collection are
            included (e.g. ``{"200", "201"}`` to test only success
            cases). Defaults to every numeric status code documented.

    Returns:
        A list of :class:`ContractCase`, one per ``(operation, status)``
        pair, in schema iteration order.
    """
    cases: list[ContractCase] = []
    for method, path, operation in schema.operations():
        responses = operation.get("responses") or {}
        for status_code, response_obj in responses.items():
            status_str = str(status_code)
            if not status_str.isdigit():
                continue  # skip "default" and similar non-numeric entries
            if statuses is not None and status_str not in statuses:
                continue
            content = (response_obj or {}).get("content") or {}
            json_content = content.get("application/json")
            response_schema = json_content.get("schema") if isinstance(json_content, dict) else None
            cases.append(
                ContractCase(
                    operation=f"{method} {path}",
                    method=method,
                    path=path,
                    expected_status=status_str,
                    response_schema=response_schema if isinstance(response_schema, dict) else None,
                )
            )
    return cases


def validate_response_against_schema(
    case: ContractCase, *, status_code: int, data: Any, root: dict[str, Any]
) -> list[str]:
    """Validate a live response against a :class:`ContractCase`'s documented contract.

    Args:
        case: The contract case being tested.
        status_code: The actual HTTP status code received.
        data: The actual, parsed JSON response body.
        root: The full OpenAPI document ``case.response_schema`` (if any)
            was drawn from, used to resolve any ``$ref`` it contains.

    Returns:
        A list of human-readable violation messages. Empty means the
        response fully complies with the documented contract.
    """
    violations: list[str] = []
    if str(status_code) != case.expected_status:
        violations.append(
            f"{case.operation}: expected status {case.expected_status}, got {status_code}"
        )
        return violations

    if case.response_schema is None:
        return violations

    resolved_schema = _inline_refs(case.response_schema, root)
    validator_cls = jsonschema.validators.validator_for(resolved_schema)
    validator = validator_cls(resolved_schema)
    for error in validator.iter_errors(data):
        location = "/".join(str(p) for p in error.absolute_path) or "<root>"
        violations.append(f"{case.operation}: {location}: {error.message}")
    return violations


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    node: Any = root
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None


def _inline_refs(
    schema: dict[str, Any],
    root: dict[str, Any],
    *,
    seen: frozenset[str] = frozenset(),
    depth: int = 0,
) -> dict[str, Any]:
    """Recursively replace every ``$ref`` with its resolved content.

    Produces a fully self-contained schema with no remaining ``$ref``
    entries, so it can be validated directly with a plain
    :class:`jsonschema.validators.Validator` without needing a resolver
    registry. Reference cycles (a schema that (indirectly) references
    itself) are broken by substituting a permissive ``{"type": "object"}``
    once a cycle is detected, rather than recursing forever.

    Args:
        schema: The schema fragment to inline.
        root: The full document to resolve ``$ref`` pointers against.
        seen: Ref pointers already expanded on the current path, for
            cycle detection. Callers should not set this.
        depth: Current recursion depth, as a secondary safety bound.

    Returns:
        A new schema dict with every ``$ref`` resolved inline.
    """
    if depth > _MAX_INLINE_DEPTH:
        return {"type": "object"}

    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in seen:
            return {"type": "object"}
        resolved = _resolve_ref(ref, root)
        if resolved is None:
            return schema
        return _inline_refs(resolved, root, seen=seen | {ref}, depth=depth + 1)

    result: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                name: (
                    _inline_refs(prop, root, seen=seen, depth=depth + 1)
                    if isinstance(prop, dict)
                    else prop
                )
                for name, prop in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            result[key] = _inline_refs(value, root, seen=seen, depth=depth + 1)
        elif key in ("allOf", "oneOf", "anyOf") and isinstance(value, list):
            result[key] = [
                (
                    _inline_refs(item, root, seen=seen, depth=depth + 1)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            result[key] = value
    return result

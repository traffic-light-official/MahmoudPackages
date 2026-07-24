"""Directional schema-comparison rules.

The central insight this module encodes: the same structural difference
is safe in one direction and breaking in the other, depending on whether
it occurred in a **request** schema or a **response** schema:

- A **request** schema describes what a client may send. Making it more
  permissive (a new optional field, relaxing a required field to
  optional, accepting an additional enum value, accepting ``null``) is
  ``SAFE`` — every existing client's requests still work. Making it more
  restrictive (a new required field, an enum value no longer accepted,
  ``null`` no longer accepted) is ``BREAKING`` — some existing client's
  request that used to succeed may now be rejected.
- A **response** schema describes what the server promises to send back.
  Promising *more* (a field is now always present instead of sometimes,
  a value is guaranteed non-null) is ``SAFE``. Promising *less* (a field
  that used to always be present might now be missing, a field that was
  never null might now be, a field is removed entirely) is ``BREAKING`` —
  some existing client relying on that guarantee may now break.

This is the opposite of a naive "any difference is worth flagging"
diff — and it's what makes this package's breaking-change detection
actually useful instead of just noisy.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from drf_contract_test.changes import Change, Severity

_MAX_RESOLUTION_DEPTH = 40


class Direction(str, Enum):
    """Which side of an operation a schema fragment belongs to."""

    REQUEST = "request"
    RESPONSE = "response"


def compare_schema_objects(  # noqa: PLR0913
    old: dict[str, Any] | None,
    new: dict[str, Any] | None,
    *,
    direction: Direction,
    location: str,
    operation: str,
    old_root: dict[str, Any],
    new_root: dict[str, Any],
    depth: int = 0,
) -> list[Change]:
    """Recursively compare two JSON Schema fragments.

    Args:
        old: The baseline schema fragment (may contain ``$ref``).
        new: The current schema fragment (may contain ``$ref``).
        direction: Whether ``old``/``new`` describe a request or a
            response — determines which changes are breaking.
        location: A human-readable path identifying this fragment within
            its operation, e.g. ``"request.properties.title"``.
        operation: The operation these fragments belong to, formatted as
            ``"<METHOD> <path>"``.
        old_root: The full baseline OpenAPI document, used to resolve
            ``$ref`` pointers within ``old``.
        new_root: The full current OpenAPI document, used to resolve
            ``$ref`` pointers within ``new``.
        depth: Current recursion depth, used to guard against
            self-referential schemas. Callers should not set this.

    Returns:
        Every :class:`~drf_contract_test.changes.Change` detected in this
        fragment or any of its nested properties/items.
    """
    if old is None or new is None or depth > _MAX_RESOLUTION_DEPTH:
        return []

    old = _resolve(old, old_root)
    new = _resolve(new, new_root)

    changes: list[Change] = []
    _compare_type(old, new, operation=operation, location=location, changes=changes)
    _compare_nullable(old, new, direction=direction, operation=operation, location=location, changes=changes)
    _compare_enum(old, new, direction=direction, operation=operation, location=location, changes=changes)
    _compare_properties(
        old,
        new,
        direction=direction,
        location=location,
        operation=operation,
        old_root=old_root,
        new_root=new_root,
        depth=depth,
        changes=changes,
    )
    _compare_items(
        old,
        new,
        direction=direction,
        location=location,
        operation=operation,
        old_root=old_root,
        new_root=new_root,
        depth=depth,
        changes=changes,
    )
    return changes


def _resolve(schema: dict[str, Any], root: dict[str, Any], *, depth: int = 0) -> dict[str, Any]:
    """Follow a ``$ref`` pointer to its target, if present.

    Args:
        schema: A schema fragment, possibly ``{"$ref": "#/..."}`` alone
            or alongside sibling keys (OpenAPI 3.1 allows siblings; only
            the ``$ref`` is followed, matching common generator output).
        root: The full document to resolve the pointer against.
        depth: Current resolution depth, to guard against a reference
            cycle.

    Returns:
        The resolved schema object, or ``schema`` unchanged if it has no
        ``$ref``, the ref is external/unsupported, or resolution failed.
    """
    ref = schema.get("$ref")
    if not isinstance(ref, str) or depth > _MAX_RESOLUTION_DEPTH:
        return schema
    if not ref.startswith("#/"):
        return schema  # external references are not supported
    node: Any = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return schema  # broken reference: treat as opaque rather than fail
        node = node[part]
    if not isinstance(node, dict):
        return schema
    return _resolve(node, root, depth=depth + 1) if "$ref" in node else node


def _base_type(schema: dict[str, Any]) -> Any:
    """Normalize a schema's ``type``, stripping an OpenAPI 3.1 ``"null"`` entry."""
    declared = schema.get("type")
    if isinstance(declared, list):
        non_null = [t for t in declared if t != "null"]
        return non_null[0] if len(non_null) == 1 else (non_null or None)
    return declared


def _is_nullable(schema: dict[str, Any]) -> bool:
    """Whether a schema accepts/produces ``null``, in either OpenAPI 3.0 or 3.1 style."""
    if schema.get("nullable") is True:
        return True
    declared = schema.get("type")
    return isinstance(declared, list) and "null" in declared


def _compare_type(
    old: dict[str, Any], new: dict[str, Any], *, operation: str, location: str, changes: list[Change]
) -> None:
    old_type = _base_type(old)
    new_type = _base_type(new)
    if old_type and new_type and old_type != new_type:
        changes.append(
            Change(
                severity=Severity.BREAKING,
                operation=operation,
                location=location,
                kind="type_changed",
                message=f"{location}: type changed from {old_type!r} to {new_type!r}",
            )
        )


def _compare_nullable(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    direction: Direction,
    operation: str,
    location: str,
    changes: list[Change],
) -> None:
    old_nullable = _is_nullable(old)
    new_nullable = _is_nullable(new)
    if old_nullable == new_nullable:
        return

    became_nullable = new_nullable and not old_nullable
    if direction is Direction.REQUEST:
        severity = Severity.SAFE if became_nullable else Severity.BREAKING
        verb = "now accepts" if became_nullable else "no longer accepts"
    else:
        severity = Severity.BREAKING if became_nullable else Severity.SAFE
        verb = "may now be" if became_nullable else "is now guaranteed never"
    changes.append(
        Change(
            severity=severity,
            operation=operation,
            location=location,
            kind="nullable_added" if became_nullable else "nullable_removed",
            message=f"{location}: {verb} null",
        )
    )


def _compare_enum(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    direction: Direction,
    operation: str,
    location: str,
    changes: list[Change],
) -> None:
    old_enum = old.get("enum")
    new_enum = new.get("enum")
    if old_enum is None and new_enum is None:
        return
    old_set = set(old_enum or [])
    new_set = set(new_enum or [])
    removed = sorted(old_set - new_set, key=str)
    added = sorted(new_set - old_set, key=str)

    if direction is Direction.REQUEST:
        if removed:
            changes.append(
                Change(
                    Severity.BREAKING,
                    operation,
                    location,
                    "enum_value_removed",
                    f"{location}: no longer accepts previously-valid value(s) {removed}",
                )
            )
        if added:
            changes.append(
                Change(
                    Severity.SAFE,
                    operation,
                    location,
                    "enum_value_added",
                    f"{location}: now additionally accepts value(s) {added}",
                )
            )
    else:
        if added:
            changes.append(
                Change(
                    Severity.BREAKING,
                    operation,
                    location,
                    "enum_value_added",
                    f"{location}: response may now include previously-undocumented value(s) {added}",
                )
            )
        if removed:
            changes.append(
                Change(
                    Severity.SAFE,
                    operation,
                    location,
                    "enum_value_removed",
                    f"{location}: response no longer includes value(s) {removed}",
                )
            )


def _compare_properties(  # noqa: PLR0913
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    direction: Direction,
    location: str,
    operation: str,
    old_root: dict[str, Any],
    new_root: dict[str, Any],
    depth: int,
    changes: list[Change],
) -> None:
    old_props: dict[str, Any] = old.get("properties") or {}
    new_props: dict[str, Any] = new.get("properties") or {}
    if not old_props and not new_props:
        return
    old_required = set(old.get("required") or [])
    new_required = set(new.get("required") or [])

    for name in sorted(set(old_props) - set(new_props)):
        field_loc = f"{location}.properties.{name}"
        if direction is Direction.REQUEST:
            changes.append(Change(Severity.SAFE, operation, field_loc, "field_removed", f"{field_loc}: request field removed"))
        else:
            changes.append(
                Change(Severity.BREAKING, operation, field_loc, "field_removed", f"{field_loc}: response field removed")
            )

    for name in sorted(set(new_props) - set(old_props)):
        field_loc = f"{location}.properties.{name}"
        if direction is Direction.REQUEST:
            if name in new_required:
                changes.append(
                    Change(
                        Severity.BREAKING,
                        operation,
                        field_loc,
                        "field_added_required",
                        f"{field_loc}: new required request field",
                    )
                )
            else:
                changes.append(
                    Change(
                        Severity.SAFE, operation, field_loc, "field_added_optional", f"{field_loc}: new optional request field"
                    )
                )
        else:
            changes.append(Change(Severity.SAFE, operation, field_loc, "field_added", f"{field_loc}: new response field"))

    for name in sorted(set(old_props) & set(new_props)):
        field_loc = f"{location}.properties.{name}"
        _compare_required(
            name in old_required,
            name in new_required,
            direction=direction,
            operation=operation,
            location=field_loc,
            changes=changes,
        )
        changes.extend(
            compare_schema_objects(
                old_props[name],
                new_props[name],
                direction=direction,
                location=field_loc,
                operation=operation,
                old_root=old_root,
                new_root=new_root,
                depth=depth + 1,
            )
        )


def _compare_required(
    was_required: bool,
    is_required: bool,
    *,
    direction: Direction,
    operation: str,
    location: str,
    changes: list[Change],
) -> None:
    if was_required == is_required:
        return
    became_required = is_required and not was_required
    if direction is Direction.REQUEST:
        severity = Severity.BREAKING if became_required else Severity.SAFE
        verb = "is now required" if became_required else "is now optional"
        suffix = "was optional" if became_required else "was required"
    else:
        severity = Severity.SAFE if became_required else Severity.BREAKING
        verb = "is now always present" if became_required else "is no longer guaranteed present"
        suffix = "was sometimes absent" if became_required else "was always present"
    changes.append(
        Change(
            severity=severity,
            operation=operation,
            location=location,
            kind="required_added" if became_required else "required_removed",
            message=f"{location}: {verb} ({suffix})",
        )
    )


def _compare_items(  # noqa: PLR0913
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    direction: Direction,
    location: str,
    operation: str,
    old_root: dict[str, Any],
    new_root: dict[str, Any],
    depth: int,
    changes: list[Change],
) -> None:
    old_items = old.get("items")
    new_items = new.get("items")
    if isinstance(old_items, dict) and isinstance(new_items, dict):
        changes.extend(
            compare_schema_objects(
                old_items,
                new_items,
                direction=direction,
                location=f"{location}.items",
                operation=operation,
                old_root=old_root,
                new_root=new_root,
                depth=depth + 1,
            )
        )

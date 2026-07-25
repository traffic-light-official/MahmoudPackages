"""Resolves local (``#/...``) JSON Reference pointers within an OpenAPI document."""

from __future__ import annotations

from typing import Any


def resolve_ref(document: dict[str, Any], ref: str) -> Any:
    """Resolve a local JSON Reference pointer against ``document``.

    Args:
        document: The full OpenAPI document the pointer is relative to.
        ref: A local reference, e.g. ``"#/components/schemas/Article"``.

    Returns:
        The referenced node.

    Raises:
        ValueError: If ``ref`` is not a local (``"#/..."``) reference, or
            does not resolve to an existing node.
    """
    if not ref.startswith("#/"):
        raise ValueError(f"Only local ('#/...') references are supported, got {ref!r}.")

    node: Any = document
    for raw_segment in ref[2:].split("/"):
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        try:
            node = node[segment]
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError(f"Reference {ref!r} does not resolve in the document.") from exc
    return node


def deref(document: dict[str, Any], node: Any) -> dict[str, Any]:
    """Follow ``$ref`` pointers on ``node`` until a concrete schema object is reached.

    Args:
        document: The full OpenAPI document, used to resolve any ``$ref``.
        node: A schema object, which may itself be ``{"$ref": "..."}``.

    Returns:
        The fully dereferenced schema object.

    Raises:
        ValueError: If a ``$ref`` chain is circular, or a reference does
            not resolve.
    """
    seen: set[str] = set()
    current = node
    while isinstance(current, dict) and "$ref" in current:
        ref = current["$ref"]
        if ref in seen:
            raise ValueError(f"Circular $ref detected while resolving {ref!r}.")
        seen.add(ref)
        current = resolve_ref(document, ref)
    return current if isinstance(current, dict) else {}

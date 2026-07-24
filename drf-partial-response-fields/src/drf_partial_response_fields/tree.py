"""Data structures representing a parsed ``fields`` expression.

A :class:`FieldTree` is the result of parsing a ``fields`` query parameter
such as ``id,name,author(name,email),tags(-internal_notes)``. It is a plain,
immutable, framework-agnostic tree: nothing in this module imports Django or
Django REST Framework, which keeps it trivially unit-testable and reusable
outside of a request/response cycle (e.g. from a management command or a
GraphQL-style resolver).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from typing import Literal

from drf_partial_response_fields.exceptions import UnknownFieldError

TreeMode = Literal["all", "include", "exclude"]


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """A single requested field within a :class:`FieldTree`.

    Attributes:
        name: The concrete field name as it appears on the serializer.
        alias: The key the field should be renamed to in the response, or
            ``None`` if the field should keep its original name.
        children: A nested :class:`FieldTree` restricting which sub-fields
            of this field are included (only meaningful when the field is
            itself a nested serializer), or ``None`` if no nested
            restriction was specified (meaning: include the field's own
            default representation, unrestricted).
    """

    name: str
    alias: str | None = None
    children: FieldTree | None = None


@dataclass(frozen=True, slots=True)
class FieldTree:
    """An immutable tree describing which fields to include at one level.

    Attributes:
        mode: ``"all"`` means no restriction applies (every field available
            on the serializer is included); ``"include"`` means only the
            names in ``includes`` are kept; ``"exclude"`` means every field
            is kept *except* the names in ``excludes``.
        includes: Mapping of field name to :class:`FieldSpec`, populated
            only when ``mode == "include"``.
        excludes: The set of excluded field names, populated only when
            ``mode == "exclude"``.
    """

    mode: TreeMode
    includes: Mapping[str, FieldSpec] = field(default_factory=dict)
    excludes: frozenset[str] = frozenset()


#: Shared sentinel representing "no restriction whatsoever". Returned
#: whenever a level of the tree has no further nested restriction, and used
#: as the default when no ``fields`` parameter was supplied at all.
ALL_TREE: FieldTree = FieldTree(mode="all")


def resolve_allowed_names(
    tree: FieldTree,
    available: Collection[str],
    *,
    strict: bool,
) -> set[str]:
    """Compute the set of field names allowed by ``tree``.

    Args:
        tree: The parsed field restriction for this level.
        available: The full set of field names that exist at this level
            (e.g. every key in a serializer's ``get_fields()`` result).
        strict: If ``True``, raise
            :class:`~drf_partial_response_fields.exceptions.UnknownFieldError`
            when ``tree`` references a name that is not in ``available``.
            If ``False``, unknown names are silently ignored.

    Returns:
        The subset of ``available`` that should be kept.

    Raises:
        drf_partial_response_fields.exceptions.UnknownFieldError: If
            ``strict`` is ``True`` and an unknown field name was requested.
    """
    available_set = set(available)
    if tree.mode == "all":
        return available_set
    if tree.mode == "exclude":
        unknown_excluded: AbstractSet[str] = tree.excludes - available_set
        if strict and unknown_excluded:
            _raise_unknown(unknown_excluded)
        return available_set - tree.excludes
    # mode == "include"
    requested = set(tree.includes)
    unknown_requested: AbstractSet[str] = requested - available_set
    if unknown_requested:
        if strict:
            _raise_unknown(unknown_requested)
        requested -= unknown_requested
    return requested


def child_tree(tree: FieldTree, name: str) -> FieldTree:
    """Descend one level into ``tree`` following field ``name``.

    Args:
        tree: The tree at the current level.
        name: The field name to descend into.

    Returns:
        The nested :class:`FieldTree` requested for ``name``, or
        :data:`ALL_TREE` if ``tree`` does not restrict ``name`` (either
        because ``tree`` itself is unrestricted, ``name`` was requested
        without an explicit nested group, or ``tree`` is in ``exclude``
        mode, which never restricts what happens *within* a kept field).
    """
    if tree.mode != "include":
        return ALL_TREE
    spec = tree.includes.get(name)
    if spec is None or spec.children is None:
        return ALL_TREE
    return spec.children


def _raise_unknown(unknown: AbstractSet[str]) -> None:
    names = ", ".join(sorted(unknown))
    raise UnknownFieldError(f"Unknown field(s) requested: {names}")

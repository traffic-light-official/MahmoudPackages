"""Automatic queryset optimization driven by a parsed ``fields`` request.

:func:`optimize_queryset` inspects a serializer class together with a
:class:`~drf_partial_response_fields.tree.FieldTree` and applies
``select_related``, ``prefetch_related``, and ``only`` to a queryset so
that exactly (and only) the data needed to render the requested fields is
fetched from the database. This is what turns sparse fieldsets into an
actual performance win rather than just a smaller JSON payload: requesting
fewer fields also means fewer joins, fewer prefetch queries, and fewer
columns read off the wire.

The optimization is deliberately conservative: whenever a field cannot be
mapped to a concrete model column or relation with certainty (a plain
``@property``, an un-annotated computed value, a
:class:`~django.contrib.contenttypes.fields.GenericForeignKey`, ...), it is
simply left alone. Correctness always wins over optimization — see
``docs/troubleshooting.md`` for the full list of cases that fall back to
unoptimized attribute access.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING, Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Prefetch
from rest_framework.relations import ManyRelatedField, RelatedField
from rest_framework.serializers import (
    BaseSerializer,
    ListSerializer,
    Serializer,
    SerializerMethodField,
)

from drf_partial_response_fields.decorators import get_hints
from drf_partial_response_fields.settings import get_setting
from drf_partial_response_fields.tree import FieldTree, child_tree, resolve_allowed_names

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet


@dataclass
class _Accumulator:
    """Mutable state threaded through the recursive optimization walk."""

    select_related: set[str] = dataclass_field(default_factory=set)
    prefetch_related: list[Any] = dataclass_field(default_factory=list)
    only_fields: set[str] = dataclass_field(default_factory=set)
    strict: bool = False


def optimize_queryset(
    queryset: QuerySet[Any],
    serializer_class: type[Serializer[Any]],
    tree: FieldTree,
    *,
    strict: bool | None = None,
    required_only_fields: frozenset[str] = frozenset(),
) -> QuerySet[Any]:
    """Apply ``select_related`` / ``prefetch_related`` / ``only`` to a queryset.

    Args:
        queryset: The base queryset to optimize. It is not mutated;
            a new queryset is returned.
        serializer_class: The (potentially nested) serializer class that
            will render the queryset's results. Must ultimately be a
            :class:`~rest_framework.serializers.ModelSerializer` subclass
            for optimization to have any effect; other serializers are
            returned unmodified.
        tree: The parsed field restriction for the top level of the
            response (as produced by
            :func:`drf_partial_response_fields.parser.parse_fields`).
        strict: Whether unknown field names should raise. Defaults to the
            :ref:`STRICT <settings-strict>` setting when ``None``.
        required_only_fields: Field names that must be included in
            ``only()`` regardless of what was requested. Used internally
            when building the queryset for a reverse-FK ``Prefetch``: the
            FK column back to the parent must never be deferred, or
            Django's own prefetch bucketing silently re-fetches it one row
            at a time.

    Returns:
        A new queryset with the relevant ``select_related``,
        ``prefetch_related``, and ``only`` calls applied. If the requested
        fields include nothing optimizable, the original queryset is
        returned unchanged.

    Raises:
        drf_partial_response_fields.exceptions.UnknownFieldError: If
            ``strict`` (or the ``STRICT`` setting) is enabled and an
            unknown field name is present in ``tree``.
    """
    if not get_setting("ENABLE_QUERY_OPTIMIZATION"):
        return queryset
    model = getattr(queryset, "model", None)
    if model is None:
        return queryset

    acc = _Accumulator(
        only_fields=set(required_only_fields),
        strict=get_setting("STRICT") if strict is None else strict,
    )
    annotations = (
        frozenset(queryset.query.annotations) if hasattr(queryset, "query") else frozenset()
    )

    _collect_optimizations(
        serializer_class=serializer_class,
        tree=tree,
        model=model,
        prefix="",
        annotations=annotations,
        acc=acc,
    )

    optimized = queryset
    if acc.select_related:
        optimized = optimized.select_related(*sorted(acc.select_related))
    if acc.prefetch_related:
        optimized = optimized.prefetch_related(*acc.prefetch_related)
    if acc.only_fields:
        optimized = optimized.only(*sorted(acc.only_fields))
    return optimized


def _join(prefix: str, name: str) -> str:
    return name if not prefix else f"{prefix}__{name}"


def _is_pk_only_related_field(field: Any) -> bool:
    if isinstance(field, ManyRelatedField):
        return bool(field.child_relation.use_pk_only_optimization())
    if isinstance(field, RelatedField):
        return bool(field.use_pk_only_optimization())
    return False


def _nested_serializer_class(field: Any) -> type[Serializer[Any]] | None:
    if isinstance(field, BaseSerializer) and not isinstance(field, ListSerializer):
        return cast("type[Serializer[Any]]", type(field))
    return None


def _apply_method_field_hints(
    *, name: str, instance: Serializer[Any], prefix: str, acc: _Accumulator
) -> None:
    getter = getattr(instance, f"get_{name}", None)
    hints = get_hints(getter) if getter is not None else None
    if hints is None:
        return
    for related_path in hints.select_related:
        acc.select_related.add(_join(prefix, related_path))
    for related_path in hints.prefetch_related:
        acc.prefetch_related.append(_join(prefix, related_path))


def _collect_optimizations(
    *,
    serializer_class: type[Serializer[Any]],
    tree: FieldTree,
    model: type[Model],
    prefix: str,
    annotations: frozenset[str],
    acc: _Accumulator,
) -> None:
    instance = serializer_class()
    fields = instance.fields
    allowed = resolve_allowed_names(tree, fields.keys(), strict=acc.strict)
    meta = model._meta

    for name in allowed:
        field = fields[name]
        if getattr(field, "write_only", False):
            # Write-only fields (e.g. a `PrimaryKeyRelatedField` mirror used
            # for input alongside a read-only nested field of the same
            # relation) never appear in the rendered response, so they must
            # not contribute to select_related/prefetch_related/only -
            # doing so risks adding a conflicting duplicate Prefetch for a
            # relation already handled by its read-only counterpart.
            continue
        _apply_method_field_hints(name=name, instance=instance, prefix=prefix, acc=acc)
        if isinstance(field, SerializerMethodField):
            continue
        _process_model_backed_field(
            name=name,
            field=field,
            tree=tree,
            meta=meta,
            prefix=prefix,
            annotations=annotations,
            acc=acc,
        )


def _process_model_backed_field(
    *,
    name: str,
    field: Any,
    tree: FieldTree,
    meta: Any,
    prefix: str,
    annotations: frozenset[str],
    acc: _Accumulator,
) -> None:
    source = field.source or name
    if not source or source == "*":
        return
    local_name = source.split(".")[0]

    if not prefix and local_name in annotations:
        acc.only_fields.add(local_name)
        return

    try:
        model_field = meta.get_field(local_name)
    except FieldDoesNotExist:
        return

    if not model_field.is_relation:
        acc.only_fields.add(_join(prefix, local_name))
        return
    if model_field.related_model is None:
        return  # e.g. GenericForeignKey: cannot be optimized generically

    full_path = _join(prefix, local_name)

    if model_field.many_to_many or model_field.one_to_many:
        _collect_to_many(
            field=field,
            model_field=model_field,
            related_model=model_field.related_model,
            full_path=full_path,
            nested_tree=child_tree(tree, name),
            acc=acc,
        )
    else:
        _process_single_relation(
            name=name, field=field, tree=tree, model_field=model_field, full_path=full_path, acc=acc
        )


def _process_single_relation(
    *,
    name: str,
    field: Any,
    tree: FieldTree,
    model_field: Any,
    full_path: str,
    acc: _Accumulator,
) -> None:
    """Handle a forward or reverse single-valued relation (FK / O2O)."""
    if _is_pk_only_related_field(field):
        return  # DRF already avoids the join via serializable_value().
    acc.select_related.add(full_path)
    nested_serializer_class = _nested_serializer_class(field)
    if nested_serializer_class is not None:
        _collect_optimizations(
            serializer_class=nested_serializer_class,
            tree=child_tree(tree, name),
            model=model_field.related_model,
            prefix=full_path,
            annotations=frozenset(),
            acc=acc,
        )


def _collect_to_many(
    *,
    field: Any,
    model_field: Any,
    related_model: type[Model],
    full_path: str,
    nested_tree: FieldTree,
    acc: _Accumulator,
) -> None:
    # For a reverse-FK relation, Django's prefetch machinery buckets each
    # fetched row by reading the FK attribute in Python (there is no
    # through-table annotation to fall back on, unlike M2M). If that column
    # is deferred by our own only() call, Django silently re-fetches it one
    # row at a time - the exact N+1 this package exists to prevent. Force it
    # to always be loaded.
    required_only_fields: frozenset[str] = (
        frozenset({model_field.field.name}) if model_field.one_to_many else frozenset()
    )

    if isinstance(field, ListSerializer):
        nested_serializer_class = cast("type[Serializer[Any]]", type(field.child))
        nested_queryset = optimize_queryset(
            related_model._default_manager.all(),
            nested_serializer_class,
            nested_tree,
            strict=acc.strict,
            required_only_fields=required_only_fields,
        )
        acc.prefetch_related.append(Prefetch(full_path, queryset=nested_queryset))
    elif isinstance(field, ManyRelatedField) and field.child_relation.use_pk_only_optimization():
        nested_queryset = related_model._default_manager.only("pk", *required_only_fields)
        acc.prefetch_related.append(Prefetch(full_path, queryset=nested_queryset))
    else:
        acc.prefetch_related.append(full_path)

"""Optimizer hints for computed (non-model) serializer fields.

:class:`~rest_framework.serializers.SerializerMethodField` values and other
computed fields have no direct mapping to a model column, so the automatic
query optimizer in :mod:`drf_partial_response_fields.optimizer` cannot infer
what a method needs to run efficiently. :func:`requires_related` lets you
declare that explicitly, so the optimizer can still add the right
``select_related`` / ``prefetch_related`` calls when (and only when) the
field is actually requested.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar

_F = TypeVar("_F", bound=Callable[..., object])

#: Attribute name under which optimizer hints are stashed on a decorated
#: method. Exposed for introspection by advanced integrations; most users
#: never need to reference this directly.
HINTS_ATTR = "partial_response_hints"


@dataclass(frozen=True, slots=True)
class OptimizationHints:
    """Extra ``select_related`` / ``prefetch_related`` paths for one field.

    Attributes:
        select_related: Relation paths (Django ``__`` notation) that must
            be joined via ``select_related`` for this field's method to
            avoid extra queries.
        prefetch_related: Relation paths that must be fetched via
            ``prefetch_related`` for this field's method to avoid extra
            queries.
    """

    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()


def requires_related(
    *,
    select_related: Sequence[str] = (),
    prefetch_related: Sequence[str] = (),
) -> Callable[[_F], _F]:
    """Declare the relations a ``get_<field>`` method depends on.

    Attach this to a :class:`~rest_framework.serializers.SerializerMethodField`
    method so that :func:`drf_partial_response_fields.optimizer.optimize_queryset`
    includes the declared relations in the generated queryset — but only
    when a client actually requests the field, avoiding the cost when it is
    not needed.

    Args:
        select_related: Dotted relation paths to add to ``select_related``
            when this field is included in the response.
        prefetch_related: Dotted relation paths to add to
            ``prefetch_related`` when this field is included in the
            response.

    Returns:
        A decorator that attaches the hints to the wrapped method and
        returns it unchanged.

    Example:
        .. code-block:: python

            class ArticleSerializer(PartialFieldsSerializerMixin, serializers.ModelSerializer):
                editor_name = serializers.SerializerMethodField()

                @requires_related(select_related=["editor__profile"])
                def get_editor_name(self, obj):
                    return obj.editor.profile.display_name
    """

    def decorator(func: _F) -> _F:
        func.__dict__[HINTS_ATTR] = OptimizationHints(
            select_related=tuple(select_related),
            prefetch_related=tuple(prefetch_related),
        )
        return func

    return decorator


def get_hints(func: object) -> OptimizationHints | None:
    """Return the :class:`OptimizationHints` attached to ``func``, if any.

    Args:
        func: A bound or unbound method, typically a serializer's
            ``get_<field_name>`` method.

    Returns:
        The attached :class:`OptimizationHints`, or ``None`` if ``func``
        was never decorated with :func:`requires_related`.
    """
    return getattr(func, HINTS_ATTR, None)

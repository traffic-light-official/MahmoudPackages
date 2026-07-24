"""Serializer mixins implementing GraphQL-like sparse fieldsets.

The central class here is :class:`PartialFieldsSerializerMixin`. Mix it into
any :class:`~rest_framework.serializers.Serializer` or
:class:`~rest_framework.serializers.ModelSerializer` (including serializers
nested inside other serializers) to make that serializer honor the parsed
``fields`` request stored in the DRF serializer context by
:class:`~drf_partial_response_fields.mixins.PartialResponseMixin`.

Unrequested :class:`~rest_framework.serializers.SerializerMethodField`
fields are removed from ``self.fields`` entirely (not merely hidden after
computation), so their ``get_<field>`` methods are never called for a field
the client did not ask for — this is what makes the mixin safe to use for
expensive computed fields.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.serializers import ListSerializer

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.settings import get_setting
from drf_partial_response_fields.tree import ALL_TREE, FieldTree, child_tree, resolve_allowed_names


class PartialFieldsSerializerMixin:
    """Mixin adding sparse-fieldset support to a DRF serializer.

    Combine with :class:`rest_framework.serializers.Serializer` or
    :class:`rest_framework.serializers.ModelSerializer` (this mixin must
    come first in the MRO). Works correctly at arbitrary nesting depth: a
    serializer used as a nested field only needs this mixin itself for its
    own sub-selection (``author(name,email)``) to be honored — no manual
    context propagation is required.

    Example:
        .. code-block:: python

            class AuthorSerializer(PartialFieldsSerializerMixin, serializers.ModelSerializer):
                class Meta:
                    model = Author
                    fields = ["id", "name", "email", "bio"]


            class ArticleSerializer(PartialFieldsSerializerMixin, serializers.ModelSerializer):
                author = AuthorSerializer()

                class Meta:
                    model = Article
                    fields = ["id", "title", "body", "author"]

        A request to ``/articles/1/?fields=title,author(name)`` returns
        only ``title`` and ``author.name``.
    """

    def get_fields(self) -> dict[str, Field[Any, Any, Any, Any]]:
        """Return the field set narrowed to what the client requested.

        Returns:
            An ordered mapping of field name to bound
            :class:`~rest_framework.fields.Field` instance, restricted
            according to the :class:`~drf_partial_response_fields.tree.FieldTree`
            resolved for this serializer's position in the response tree.
        """
        fields: dict[str, Field[Any, Any, Any, Any]] = super().get_fields()  # type: ignore[misc]
        tree = self._resolve_local_tree()
        self._partial_response_alias_map = _build_alias_map(tree)

        if tree.mode == "all":
            return fields

        strict = get_setting("STRICT")
        always_include = set(get_setting("ALWAYS_INCLUDE"))
        allowed = resolve_allowed_names(tree, fields.keys(), strict=strict)
        allowed |= always_include & fields.keys()
        return OrderedDict((name, f) for name, f in fields.items() if name in allowed)

    def to_representation(self, instance: Any) -> Any:
        """Serialize ``instance``, applying any requested field aliases.

        Args:
            instance: The object being serialized.

        Returns:
            The representation produced by the parent class, with any
            ``alias:field`` renames from the request applied to its keys.
        """
        ret = super().to_representation(instance)  # type: ignore[misc]
        alias_map = getattr(self, "_partial_response_alias_map", None)
        if alias_map:
            renamed = OrderedDict()
            for key, value in ret.items():
                renamed[alias_map.get(key, key)] = value
            return renamed
        return ret

    def _resolve_local_tree(self) -> FieldTree:
        """Resolve the :class:`FieldTree` that applies to this serializer.

        Walks from this serializer instance up to the root of the
        serializer tree to determine this instance's dotted path (e.g.
        ``["author"]`` for a serializer nested under an ``author`` field),
        then descends into the request-wide tree stored in the root's
        context following that path.

        Returns:
            The resolved :class:`~drf_partial_response_fields.tree.FieldTree`
            for this exact position in the response, or
            :data:`~drf_partial_response_fields.tree.ALL_TREE` if no
            restriction applies (no ``fields`` parameter was supplied, or
            this position was not restricted by a parent group).
        """
        context = self.context  # type: ignore[attr-defined]
        top_tree: FieldTree | None = context.get(CONTEXT_KEY) if context else None
        if top_tree is None:
            return ALL_TREE

        node: FieldTree = top_tree
        for name in self._path_from_root():
            node = child_tree(node, name)
            if node is ALL_TREE:
                return ALL_TREE
        return node

    def _path_from_root(self) -> list[str]:
        """Compute the field-name path from the root serializer to here."""
        segments: list[str] = []
        node: Any = self
        while node.parent is not None:
            name = node.field_name
            if name:
                segments.append(name)
            node = node.parent
        segments.reverse()
        return segments


def _build_alias_map(tree: FieldTree) -> dict[str, str]:
    if tree.mode != "include":
        return {}
    return {name: spec.alias for name, spec in tree.includes.items() if spec.alias}


class PartialFieldsSerializer(PartialFieldsSerializerMixin, serializers.Serializer[Any]):
    """Convenience base combining :class:`PartialFieldsSerializerMixin` with
    :class:`rest_framework.serializers.Serializer`, for non-model serializers.
    """


class PartialFieldsModelSerializer(PartialFieldsSerializerMixin, serializers.ModelSerializer[Any]):
    """Convenience base combining :class:`PartialFieldsSerializerMixin` with
    :class:`rest_framework.serializers.ModelSerializer`.
    """


class PartialFieldsListSerializer(ListSerializer[Any]):
    """A :class:`~rest_framework.serializers.ListSerializer` variant that is
    a no-op subclass kept for symmetry and forward compatibility.

    Field filtering for ``many=True`` serializers is handled entirely by
    :class:`PartialFieldsSerializerMixin` on the child serializer (its
    ``_path_from_root`` correctly skips the list wrapper), so this class
    does not need to override any behavior today. It exists so that users
    who explicitly set ``Meta.list_serializer_class`` have a documented,
    stable name to point to.
    """

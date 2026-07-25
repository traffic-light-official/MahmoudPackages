"""Maps a single JSON Schema field definition to a DRF field expression.

This module only handles one field at a time and does not itself
resolve ``$ref`` - callers pass in the schema's ``components.schemas``
so a ``$ref`` can be recognized as "this is field is another generated
serializer," without this module needing to know about serializer
class naming (that's :mod:`drf_api_reverse.naming`'s job) or generation
order (that's :mod:`drf_api_reverse.codegen.serializers`'s job).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from drf_api_reverse.naming import serializer_class_name

_REF_PREFIX = "#/components/schemas/"

_STRING_FORMAT_FIELDS: dict[str, str] = {
    "date": "DateField",
    "date-time": "DateTimeField",
    "email": "EmailField",
    "uri": "URLField",
    "url": "URLField",
    "uuid": "UUIDField",
    "ipv4": "IPAddressField",
    "ipv6": "IPAddressField",
}

_SIMPLE_TYPE_FIELDS: dict[str, str] = {
    "integer": "IntegerField",
    "number": "FloatField",
    "boolean": "BooleanField",
}


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """The generated source for one serializer field."""

    expression: str
    """The right-hand side, e.g. ``serializers.CharField(required=False)``."""

    ref: str | None = None
    """The referenced component schema name, if this field is a ``$ref``
    (directly, or as an array's ``items``) - used by the serializer
    generator to order classes and detect circular references."""


def ref_target(schema: dict[str, Any]) -> str | None:
    """Return the component name a ``$ref`` points at, or ``None``."""
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
        return ref[len(_REF_PREFIX) :]
    return None


def field_spec(field_schema: dict[str, Any], *, required: bool) -> FieldSpec:
    """Return the DRF field expression for one property's schema.

    Args:
        field_schema: The property's own JSON Schema fragment (already
            dereferenced one level, i.e. ``$ref`` is resolved by the
            caller only far enough to detect it - the fragment itself
            may still be a ``{"$ref": ...}`` dict).
        required: Whether this field is in the parent schema's
            ``required`` list.

    Returns:
        A :class:`FieldSpec` with a ready-to-emit field expression.
    """
    target = ref_target(field_schema)
    if target is not None:
        kwargs = _kwargs_str(required=required, extra={})
        return FieldSpec(f"{serializer_class_name(target)}({kwargs})", ref=target)

    field_type = field_schema.get("type")

    if field_type == "array":
        return _array_field_spec(field_schema, required=required)

    if field_type == "object" and "properties" in field_schema:
        return FieldSpec(_dict_field_expression(required=required, reason="inline object"))

    if field_type == "string":
        enum = field_schema.get("enum")
        if enum:
            choices = ", ".join(repr(value) for value in enum)
            extra = {"choices": f"[{choices}]"}
            return FieldSpec(
                f"serializers.ChoiceField({_kwargs_str(required=required, extra=extra)})"
            )

        field_format = field_schema.get("format")
        class_name = _STRING_FORMAT_FIELDS.get(field_format or "", "CharField")
        extra = {}
        if class_name == "CharField":
            max_length = field_schema.get("maxLength")
            if max_length is not None:
                extra["max_length"] = str(max_length)
        return FieldSpec(f"serializers.{class_name}({_kwargs_str(required=required, extra=extra)})")

    simple_class_name = _SIMPLE_TYPE_FIELDS.get(field_type or "")
    if simple_class_name is not None:
        kwargs = _kwargs_str(required=required, extra={})
        return FieldSpec(f"serializers.{simple_class_name}({kwargs})")

    return FieldSpec(
        _dict_field_expression(required=required, reason=f"unrecognized type {field_type!r}")
    )


def _array_field_spec(field_schema: dict[str, Any], *, required: bool) -> FieldSpec:
    items = field_schema.get("items") or {}
    target = ref_target(items)
    if target is not None:
        extra = {"many": "True"}
        kwargs = _kwargs_str(required=required, extra=extra)
        return FieldSpec(f"{serializer_class_name(target)}({kwargs})", ref=target)

    child_spec = field_spec(items, required=True) if items else FieldSpec("serializers.CharField()")
    extra = {"child": child_spec.expression}
    return FieldSpec(
        f"serializers.ListField({_kwargs_str(required=required, extra=extra)})", ref=child_spec.ref
    )


def _dict_field_expression(*, required: bool, reason: str) -> str:
    kwargs = _kwargs_str(required=required, extra={})
    comment = f"  # {reason}: generated as an opaque mapping, refine by hand"
    return f"serializers.DictField({kwargs}){comment}"


def _kwargs_str(*, required: bool, extra: dict[str, str]) -> str:
    kwargs = dict(extra)
    if not required:
        kwargs["required"] = "False"
    return ", ".join(f"{key}={value}" for key, value in kwargs.items())

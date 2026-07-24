"""JSON Schema generation from Django REST Framework serializers.

:func:`serializer_to_json_schema` is the single entry point: give it a
serializer class (or instance) and get back a plain JSON-Schema-compatible
``dict`` — the same shape OpenAI function calling and MCP tool
definitions both wrap (see :mod:`drf_llm_gateway.openai_tools` and
:mod:`drf_llm_gateway.mcp`).

The conversion is deliberately explicit about what it does *not* support:
:class:`~rest_framework.fields.FileField` and
:class:`~rest_framework.fields.ImageField` have no meaningful
representation as a JSON-serializable function-call argument (an LLM
cannot attach binary file content to a tool call), so they are omitted
from the generated schema by default — see ``docs/troubleshooting.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from rest_framework import fields as drf_fields
from rest_framework import relations as drf_relations
from rest_framework.serializers import BaseSerializer, ListSerializer, Serializer

from drf_llm_gateway.exceptions import SchemaGenerationError
from drf_llm_gateway.settings import get_setting

JSONSchema = dict[str, Any]

#: Fields with no reasonable JSON Schema representation as a tool-call
#: argument. Skipped entirely rather than guessed at.
_UNSUPPORTED_FIELD_TYPES: tuple[type[drf_fields.Field[Any, Any, Any, Any]], ...] = (
    drf_fields.FileField,
    drf_fields.ImageField,
)

#: Direct type mappings requiring no further inspection of the field
#: instance beyond its class. Order matters: this is scanned top-to-bottom
#: and the first matching ``isinstance()`` wins, so subclasses (e.g.
#: ``EmailField``, a ``CharField`` subclass) must be listed *before* the
#: more general class they inherit from.
_SIMPLE_TYPE_MAP: dict[type[drf_fields.Field[Any, Any, Any, Any]], JSONSchema] = {
    drf_fields.BooleanField: {"type": "boolean"},
    drf_fields.IntegerField: {"type": "integer"},
    drf_fields.FloatField: {"type": "number"},
    drf_fields.DecimalField: {"type": "string", "format": "decimal"},
    drf_fields.SlugField: {"type": "string", "format": "slug"},
    drf_fields.EmailField: {"type": "string", "format": "email"},
    drf_fields.URLField: {"type": "string", "format": "uri"},
    drf_fields.UUIDField: {"type": "string", "format": "uuid"},
    drf_fields.IPAddressField: {"type": "string", "format": "ipv4"},
    drf_fields.DateTimeField: {"type": "string", "format": "date-time"},
    drf_fields.DateField: {"type": "string", "format": "date"},
    drf_fields.TimeField: {"type": "string", "format": "time"},
    drf_fields.DurationField: {"type": "string", "format": "duration"},
    drf_fields.JSONField: {},
    drf_fields.DictField: {"type": "object"},
    drf_fields.HStoreField: {"type": "object"},
    drf_fields.ReadOnlyField: {},
    drf_fields.SerializerMethodField: {},
    drf_fields.CharField: {"type": "string"},
}


def serializer_to_json_schema(
    serializer: type[BaseSerializer[Any]] | BaseSerializer[Any],
    *,
    mode: str = "input",
) -> JSONSchema:
    """Convert a DRF serializer to a JSON Schema ``object`` schema.

    Args:
        serializer: A serializer class or instance. Classes are
            instantiated internally (with no arguments) purely for field
            introspection; no validation or I/O occurs.
        mode: ``"input"`` (default) includes only writable fields — the
            arguments a caller may supply — and is what
            :mod:`drf_llm_gateway.openai_tools` and :mod:`drf_llm_gateway.mcp`
            use for tool parameter schemas. ``"output"`` includes every
            field (read-only fields are marked ``"readOnly": true``),
            useful for describing what a tool *returns*.

    Returns:
        A JSON-Schema-compatible object schema: a top-level type of
        object, a mapping of field name to field schema, and (in
        ``"input"`` mode) a list of the required field names.

    Raises:
        drf_llm_gateway.exceptions.SchemaGenerationError: If ``mode`` is
            invalid, or if nested serializers exceed the
            ``MAX_SCHEMA_DEPTH`` setting.

    Example:
        A serializer with a required ``name`` field and an optional
        ``email`` field produces a schema whose ``required`` list contains
        only ``"name"``.
    """
    if mode not in ("input", "output"):
        raise SchemaGenerationError(f"mode must be 'input' or 'output', got {mode!r}.")
    instance = serializer() if isinstance(serializer, type) else serializer
    return _serializer_to_schema(instance, mode=mode, depth=1)


def _serializer_to_schema(instance: BaseSerializer[Any], *, mode: str, depth: int) -> JSONSchema:
    max_depth = get_setting("MAX_SCHEMA_DEPTH")
    if depth > max_depth:
        raise SchemaGenerationError(
            f"Serializer nesting exceeds MAX_SCHEMA_DEPTH ({max_depth}); "
            f"this usually indicates a self-referential serializer."
        )
    if not isinstance(instance, Serializer):
        raise SchemaGenerationError(
            f"Expected a Serializer instance, got {type(instance).__name__}."
        )

    properties: dict[str, JSONSchema] = {}
    required: list[str] = []
    for name, field in instance.fields.items():
        if isinstance(field, _UNSUPPORTED_FIELD_TYPES):
            continue
        if mode == "input" and field.read_only:
            continue
        properties[name] = _field_to_schema(field, mode=mode, depth=depth)
        if mode == "output" and field.read_only:
            properties[name]["readOnly"] = True
        if mode == "input" and field.required:
            required.append(name)

    schema: JSONSchema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = sorted(required)
    return schema


def _field_to_schema(
    field: drf_fields.Field[Any, Any, Any, Any], *, mode: str, depth: int
) -> JSONSchema:
    schema = _base_field_schema(field, mode=mode, depth=depth)
    if field.help_text:
        schema.setdefault("description", str(field.help_text))
    if field.default is not drf_fields.empty and not callable(field.default):
        schema.setdefault("default", field.default)
    if getattr(field, "allow_null", False):
        schema = _make_nullable(schema)
    return schema


def _base_field_schema(
    field: drf_fields.Field[Any, Any, Any, Any], *, mode: str, depth: int
) -> JSONSchema:
    relation_schema = _relation_or_nested_schema(field, mode=mode, depth=depth)
    if relation_schema is not None:
        return relation_schema
    if isinstance(field, drf_fields.MultipleChoiceField):
        return {"type": "array", "items": _choice_schema(field)}
    if isinstance(field, drf_fields.ChoiceField):
        return _choice_schema(field)
    return _simple_type_schema(field)


def _relation_or_nested_schema(
    field: drf_fields.Field[Any, Any, Any, Any], *, mode: str, depth: int
) -> JSONSchema | None:
    if isinstance(field, drf_relations.ManyRelatedField):
        return {"type": "array", "items": _related_field_schema(field.child_relation)}
    if isinstance(field, drf_relations.RelatedField):
        return _related_field_schema(field)
    if isinstance(field, ListSerializer):
        child = cast(BaseSerializer[Any], field.child)
        return {
            "type": "array",
            "items": _serializer_to_schema(child, mode=mode, depth=depth + 1),
        }
    if isinstance(field, Serializer):
        return _serializer_to_schema(field, mode=mode, depth=depth + 1)
    if isinstance(field, drf_fields.ListField):
        list_child = field.child
        item_schema = _field_to_schema(list_child, mode=mode, depth=depth) if list_child else {}
        return {"type": "array", "items": item_schema}
    return None


def _simple_type_schema(field: drf_fields.Field[Any, Any, Any, Any]) -> JSONSchema:
    for field_type, mapped in _SIMPLE_TYPE_MAP.items():
        if isinstance(field, field_type):
            return dict(mapped)
    return {}


def _related_field_schema(field: drf_fields.Field[Any, Any, Any, Any]) -> JSONSchema:
    if isinstance(field, (drf_relations.SlugRelatedField, drf_relations.StringRelatedField)):
        return {"type": "string"}
    if isinstance(field, drf_relations.HyperlinkedRelatedField):
        return {"type": "string", "format": "uri"}
    if isinstance(field, drf_relations.PrimaryKeyRelatedField):
        pk_field = _pk_field_type(field)
        if pk_field is not None:
            return dict(pk_field)
        return {"type": "integer"}
    return {"type": "string"}


def _pk_field_type(field: drf_relations.PrimaryKeyRelatedField[Any]) -> JSONSchema | None:
    queryset = getattr(field, "queryset", None)
    model = getattr(queryset, "model", None)
    if model is None:
        return None
    pk_field = model._meta.pk
    if pk_field.get_internal_type() in {
        "AutoField",
        "BigAutoField",
        "SmallAutoField",
        "IntegerField",
    }:
        return {"type": "integer"}
    if pk_field.get_internal_type() == "UUIDField":
        return {"type": "string", "format": "uuid"}
    return {"type": "string"}


def _choice_schema(field: drf_fields.ChoiceField) -> JSONSchema:
    max_values = get_setting("MAX_ENUM_VALUES")
    choices = (
        list(field.choices.keys()) if isinstance(field.choices, Mapping) else list(field.choices)
    )
    if len(choices) > max_values:
        return {
            "type": "string",
            "description": f"One of {len(choices)} choices (too many to enumerate).",
        }
    if choices and all(isinstance(c, bool) for c in choices):
        return {"type": "boolean", "enum": choices}
    if choices and all(isinstance(c, int) and not isinstance(c, bool) for c in choices):
        return {"type": "integer", "enum": choices}
    return {"type": "string", "enum": [str(c) for c in choices]}


def _make_nullable(schema: JSONSchema) -> JSONSchema:
    schema = dict(schema)
    current_type = schema.get("type")
    if isinstance(current_type, str):
        schema["type"] = [current_type, "null"]
    elif isinstance(current_type, list) and "null" not in current_type:
        schema["type"] = [*current_type, "null"]
    return schema

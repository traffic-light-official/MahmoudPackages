# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) — the same text you'll see
in your editor's tooltips.

## Serializers

### PartialFieldsSerializerMixin

::: drf_partial_response_fields.serializers.PartialFieldsSerializerMixin

### PartialFieldsSerializer

::: drf_partial_response_fields.serializers.PartialFieldsSerializer

### PartialFieldsModelSerializer

::: drf_partial_response_fields.serializers.PartialFieldsModelSerializer

### PartialFieldsListSerializer

::: drf_partial_response_fields.serializers.PartialFieldsListSerializer

## Views

### PartialResponseMixin

::: drf_partial_response_fields.mixins.PartialResponseMixin

### parse_request_fields

::: drf_partial_response_fields.mixins.parse_request_fields

### PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY

A module-level constant: the serializer-context key under which
`PartialResponseMixin` stores the parsed `FieldTree` for the current
request. Public alias of `drf_partial_response_fields.constants.CONTEXT_KEY`,
for use by manual (non-mixin) integrations such as plain `APIView`
subclasses — see [Advanced Usage](advanced-usage.md#plain-apiview-integration).

## Query optimization

### optimize_queryset

::: drf_partial_response_fields.optimizer.optimize_queryset

## Decorators

### requires_related

::: drf_partial_response_fields.decorators.requires_related

### OptimizationHints

::: drf_partial_response_fields.decorators.OptimizationHints

### get_hints

::: drf_partial_response_fields.decorators.get_hints

## Parsing

### parse_fields

::: drf_partial_response_fields.parser.parse_fields

## Data model

### FieldTree

::: drf_partial_response_fields.tree.FieldTree

### FieldSpec

::: drf_partial_response_fields.tree.FieldSpec

### ALL_TREE

::: drf_partial_response_fields.tree.ALL_TREE

### resolve_allowed_names

::: drf_partial_response_fields.tree.resolve_allowed_names

### child_tree

::: drf_partial_response_fields.tree.child_tree

## Exceptions

### PartialResponseFieldsError

::: drf_partial_response_fields.exceptions.PartialResponseFieldsError

### InvalidFieldsParameterError

::: drf_partial_response_fields.exceptions.InvalidFieldsParameterError

### UnknownFieldError

::: drf_partial_response_fields.exceptions.UnknownFieldError

## Settings

### get_setting

::: drf_partial_response_fields.settings.get_setting

See [Settings](settings.md) for the full list of recognized keys and their
defaults.

## OpenAPI (drf-spectacular)

Requires the `openapi` extra: `pip install drf-partial-response-fields[openapi]`.

### fields_query_parameter

::: drf_partial_response_fields.openapi.fields_query_parameter

### PartialResponseAutoSchema

::: drf_partial_response_fields.openapi.PartialResponseAutoSchema

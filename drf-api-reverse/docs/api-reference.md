# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Scaffolding

### scaffold

::: drf_api_reverse.scaffolder.scaffold

### FileResult

::: drf_api_reverse.scaffolder.FileResult

## Drift detection

### check_drift

::: drf_api_reverse.checker.check_drift

### raise_if_drifted

::: drf_api_reverse.checker.raise_if_drifted

### FileDrift

::: drf_api_reverse.checker.FileDrift

## Loading schemas

### load_schema_file

::: drf_api_reverse.schema_loader.load_schema_file

### parse_schema

::: drf_api_reverse.schema_loader.parse_schema

## Code generators

### generate_serializer_regions

::: drf_api_reverse.codegen.serializers.generate_serializer_regions

### serializers.render_file

::: drf_api_reverse.codegen.serializers.render_file

### generate_viewset_regions

::: drf_api_reverse.codegen.views.generate_viewset_regions

### views.render_file

::: drf_api_reverse.codegen.views.render_file

### generate_url_regions

::: drf_api_reverse.codegen.urls.generate_url_regions

### urls.render_file

::: drf_api_reverse.codegen.urls.render_file

### parse_resource_groups

::: drf_api_reverse.codegen.operations.parse_resource_groups

### ResourceGroup

::: drf_api_reverse.codegen.operations.ResourceGroup

### Operation

::: drf_api_reverse.codegen.operations.Operation

## Idempotent region merging

### merge

::: drf_api_reverse.regions.merge

### existing_region_keys

::: drf_api_reverse.regions.existing_region_keys

### parse_regions

::: drf_api_reverse.regions.parse_regions

## Naming and type mapping

### to_class_name

::: drf_api_reverse.naming.to_class_name

### to_snake_case

::: drf_api_reverse.naming.to_snake_case

### resource_group_key

::: drf_api_reverse.naming.resource_group_key

### field_spec

::: drf_api_reverse.type_mapping.field_spec

### FieldSpec

::: drf_api_reverse.type_mapping.FieldSpec

## Exceptions

### ApiReverseError

::: drf_api_reverse.exceptions.ApiReverseError

### SchemaParseError

::: drf_api_reverse.exceptions.SchemaParseError

### RegionMergeError

::: drf_api_reverse.exceptions.RegionMergeError

### DriftDetectedError

::: drf_api_reverse.exceptions.DriftDetectedError

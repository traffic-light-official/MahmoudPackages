# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Exception handler

### problem_details_exception_handler

::: drf_error_response_standardizer.handler.problem_details_exception_handler

## Problem model

### ProblemDetail

::: drf_error_response_standardizer.problem.ProblemDetail

### ErrorType

::: drf_error_response_standardizer.codes.ErrorType

### BUILTIN_ERROR_TYPES

A `dict[str, ErrorType]` of every problem type this package produces out
of the box, keyed by `ErrorType.code`. See [Settings](settings.md) and
[Common Patterns](common-patterns.md) for how these are used.

## Registry

### ProblemRegistry

::: drf_error_response_standardizer.registry.ProblemRegistry

### register

::: drf_error_response_standardizer.registry.register

### register_builder

::: drf_error_response_standardizer.registry.register_builder

### default_registry

The `ProblemRegistry` instance used throughout the package unless a
different registry is passed explicitly to
`problem_details_exception_handler(..., registry=...)`.

## Exceptions

### ProblemAPIException

::: drf_error_response_standardizer.exceptions.ProblemAPIException

### ConflictError

::: drf_error_response_standardizer.exceptions.ConflictError

### UnprocessableEntityError

::: drf_error_response_standardizer.exceptions.UnprocessableEntityError

## Validation normalization

### normalize_validation_error

::: drf_error_response_standardizer.normalize.normalize_validation_error

### NormalizedError

::: drf_error_response_standardizer.normalize.NormalizedError

## Middleware

### CorrelationIdMiddleware

::: drf_error_response_standardizer.middleware.CorrelationIdMiddleware

### get_correlation_id

::: drf_error_response_standardizer.middleware.get_correlation_id

### get_request_id

::: drf_error_response_standardizer.middleware.get_request_id

### get_trace_id

::: drf_error_response_standardizer.middleware.get_trace_id

## Localization

### translate

::: drf_error_response_standardizer.localization.translate

### activate_for_request

::: drf_error_response_standardizer.localization.activate_for_request

### resolve_language

::: drf_error_response_standardizer.localization.resolve_language

## Error catalog

### build_catalog

::: drf_error_response_standardizer.catalog.build_catalog

### render_markdown

::: drf_error_response_standardizer.catalog.render_markdown

### render_json

::: drf_error_response_standardizer.catalog.render_json

## OpenAPI integration

### problem_details_postprocessing_hook

::: drf_error_response_standardizer.openapi.problem_details_postprocessing_hook

### registered_status_codes

::: drf_error_response_standardizer.openapi.registered_status_codes

### PROBLEM_DETAIL_SCHEMA

The raw OpenAPI schema dict registered as the `ProblemDetail` component.

## drf-standardized-errors compatibility

### to_standardized_errors_format

::: drf_error_response_standardizer.compat.to_standardized_errors_format

## Settings

### get_setting

::: drf_error_response_standardizer.settings.get_setting

### app_settings

The module-level `_ErrorResponseStandardizerSettings` instance backing
`get_setting()`. See [Settings](settings.md) for the full list of keys.

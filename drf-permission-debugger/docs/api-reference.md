# API Reference

This page documents every public class and function. It is generated
in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll
see in your editor's tooltips.

## Mixin

### PermissionDebugMixin

::: drf_permission_debugger.mixins.PermissionDebugMixin

### get_permission_trace

::: drf_permission_debugger.mixins.get_permission_trace

## Tracing

### PermissionCheckResult

::: drf_permission_debugger.tracing.PermissionCheckResult

### PermissionTrace

::: drf_permission_debugger.tracing.PermissionTrace

## Introspection

### PermissionDescription

::: drf_permission_debugger.introspection.PermissionDescription

### describe_permissions

::: drf_permission_debugger.introspection.describe_permissions

### describe_view

::: drf_permission_debugger.introspection.describe_view

## Settings

### get_setting

::: drf_permission_debugger.settings.get_setting

## Management command

### show_view_permissions

```bash
python manage.py show_view_permissions <path>
```

Resolves `<path>` via Django's URL resolver and prints the matched
view's `permission_classes` (via [`describe_view`](#describe_view)),
`authentication_classes`, and `throttle_classes`. Raises a
`CommandError` if the path doesn't resolve to any URL, or resolves to a
plain function-based view with no `.cls`/`.view_class` to introspect.
See [Quick Start](quickstart.md#from-the-command-line) for example
output.

# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Versioning schemes

### URLPathVersioning

::: drf_api_versioning.versioning.URLPathVersioning

### NamespaceVersioning

::: drf_api_versioning.versioning.NamespaceVersioning

### AcceptHeaderVersioning

::: drf_api_versioning.versioning.AcceptHeaderVersioning

### QueryParameterVersioning

::: drf_api_versioning.versioning.QueryParameterVersioning

### HostNameVersioning

::: drf_api_versioning.versioning.HostNameVersioning

## Response headers

### DeprecationHeaderMixin

::: drf_api_versioning.mixins.DeprecationHeaderMixin

## Registry

### VersionInfo

::: drf_api_versioning.registry.VersionInfo

### all_versions

::: drf_api_versioning.registry.all_versions

### all_version_names

::: drf_api_versioning.registry.all_version_names

### get_version_info

::: drf_api_versioning.registry.get_version_info

### default_version_name

::: drf_api_versioning.registry.default_version_name

## Signals

### deprecated_version_used

`drf_api_versioning.signals.deprecated_version_used` - a
`django.dispatch.Signal`, sent once per request that resolves to a
deprecated (but not sunset/rejected) API version.

Providing arguments:

| Argument | Type | Description |
| --- | --- | --- |
| `request` | `rest_framework.request.Request` | The request being processed. |
| `version` | `str` | The resolved version name. |
| `version_info` | [`VersionInfo`](#versioninfo) | That version's metadata. |

See [Quick Start](quickstart.md#tracking-whos-still-using-a-deprecated-version)
for a usage example.

## Settings

### get_setting

::: drf_api_versioning.settings.get_setting

## Exceptions

### UnknownAPIVersionError

::: drf_api_versioning.exceptions.UnknownAPIVersionError

### APIVersionSunsetError

::: drf_api_versioning.exceptions.APIVersionSunsetError

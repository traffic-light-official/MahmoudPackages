# drf-api-versioning

Enterprise API version lifecycle management for Django REST Framework:
a central version registry with deprecation/sunset dates, automatic
`Deprecation`/`Sunset`/`Link` response headers (RFC 8594-style), and
registry-aware versioning schemes that are drop-in replacements for
DRF's own.

```python
class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
    versioning_class = URLPathVersioning
```

## Why this exists

DRF ships versioning *schemes* (how a version is resolved from a
request) but no version *lifecycle*: there's no built-in concept of "v1
is deprecated as of X and sunset as of Y," no automatic client-facing
signal that a version is going away, and no single source of truth a
health check or CI job can query. This package adds exactly that layer
on top of DRF's existing schemes, without replacing how you version
your API today - switching is a one-line import change.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Want the exact enforcement rules (deprecated vs. sunset, header
  format)? Read [Architecture](architecture.md).
- Looking for a specific function? Jump to [API Reference](api-reference.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Declare version metadata | [Settings](settings.md) (`API_VERSIONING`) |
| Drop-in versioning scheme | [`URLPathVersioning`](api-reference.md#urlpathversioning) and 4 others |
| Automatic Deprecation/Sunset/Link headers | [`DeprecationHeaderMixin`](api-reference.md#deprecationheadermixin) |
| Reject unknown/sunset versions | Automatic - [`UnknownAPIVersionError`](api-reference.md#unknownapiversionerror) / [`APIVersionSunsetError`](api-reference.md#apiversionsunseterror) |
| Track who's still using a deprecated version | [`deprecated_version_used`](api-reference.md#deprecated_version_used) signal |
| List every version's status | `python manage.py list_api_versions` |

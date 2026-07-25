# Advanced Usage

## Switching an existing view from a DRF built-in scheme

```python
# before
from rest_framework.versioning import URLPathVersioning

class ArticleViewSet(viewsets.ModelViewSet):
    versioning_class = URLPathVersioning

# after
from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning

class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
    versioning_class = URLPathVersioning
```

Only the import changes. Remove any per-view `allowed_versions`/
`default_version` override on the view itself - the registry-aware
class always computes both from `API_VERSIONING`, so a leftover
per-view override has no effect either way, but leaving it in place is
misleading to a future reader.

## Writing your own response header logic

`DeprecationHeaderMixin` is a small, single-purpose `finalize_response`
override - write your own instead if you need different headers or
extra logic per view:

```python
from drf_api_versioning import registry


class CustomDeprecationMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        version = getattr(request, "version", None)
        if version is None:
            return response

        info = registry.get_version_info(version)
        if info.is_deprecated():
            response["X-API-Deprecated"] = "true"
            response["X-API-Migrate-By"] = str(info.sunset_on) if info.sunset_on else "unscheduled"
        return response
```

## Custom usage analytics via the signal

```python
from drf_api_versioning.signals import deprecated_version_used


def record_deprecated_usage(sender, *, request, version, version_info, **kwargs):
    DeprecatedVersionUsage.objects.create(
        version=version,
        path=request.path,
        user=request.user if request.user.is_authenticated else None,
    )


deprecated_version_used.connect(record_deprecated_usage)
```

This package deliberately ships no `DeprecatedVersionUsage` model or
similar - what "usage" means (per-request, per-user, aggregated daily)
is a project-specific decision; connect the signal to whatever your
project already uses for analytics/metrics.

## Combining with a custom `allowed_versions`-dependent third-party package

Some third-party DRF packages introspect `view.versioning_class(
).allowed_versions` directly (rather than going through
`determine_version`). Since `allowed_versions` is a property computed
from the registry, this still works transparently - the third-party
package sees the same tuple `all_version_names()` would return, with no
extra wiring needed.

## Testing views without going through URL resolution

`determine_version()` needs the resolved kwargs a real URL dispatch
would provide - for `URLPathVersioning`, pass `version` as a kwarg
directly to the view call, matching what a real URL conf's `(?P<version>...)`
group would supply:

```python
from rest_framework.test import APIRequestFactory

request = APIRequestFactory().get("/v2/articles/")
response = ArticleViewSet.as_view({"get": "list"})(request, version="v2")
```

See [Testing](testing.md) for the equivalent for each of the other four
schemes (query parameter, `Accept` header, namespace, hostname).

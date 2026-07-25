# Examples

A complete, runnable example - no separate Django project needed - lives
in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-api-versioning/examples/blog):
a three-version registry (`v1` sunset, `v2` deprecated but active, `v3`
fully supported) and an `ArticleListView` using `URLPathVersioning` and
`DeprecationHeaderMixin`.

## Running it

```bash
python -m examples.blog.example
```

```
Registry:
  VersionInfo(name='v1', deprecated_on=datetime.date(2020, 1, 1), sunset_on=datetime.date(2020, 6, 1), deprecation_link='https://example.com/docs/migrating-to-v3')
  VersionInfo(name='v2', deprecated_on=datetime.date(2020, 1, 1), sunset_on=None, deprecation_link='https://example.com/docs/migrating-to-v3')
  VersionInfo(name='v3', deprecated_on=None, sunset_on=None, deprecation_link=None)

Requests:
v1: 410 {'detail': ErrorDetail(string="API version 'v1' has been sunset as of 2020-06-01 and is no longer available.", code='api_version_sunset')} headers={}
v2: 200 {'version': 'v2', 'articles': ['Hello, world!']} headers={'Deprecation': 'Wed, 01 Jan 2020 00:00:00 GMT', 'Link': '<https://example.com/docs/migrating-to-v3>; rel="deprecation"'}
v3: 200 {'version': 'v3', 'articles': ['Hello, world!']} headers={}
v9: 404 {'detail': ErrorDetail(string="Unknown API version 'v9'. Supported versions: v1, v2, v3.", code='unknown_api_version')} headers={}
```

Note `v1` gets no headers at all - once a version is rejected outright
(410), there's nothing left to warn about; `Sunset`/`Deprecation` are
advance-warning headers for a version that still works, not a
description of why a request just failed (see
[Architecture](architecture.md)). `v2` gets both `Deprecation` and
`Link` but no `Sunset`, matching its registry entry, which declares no
`sunset` date at all.

## The code

```python
# examples/blog/example.py (abbreviated)
from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning


class ArticleListView(DeprecationHeaderMixin, APIView):
    versioning_class = URLPathVersioning

    def get(self, request, *args, **kwargs):
        return Response({"version": request.version, "articles": ["Hello, world!"]})
```

```python
from rest_framework.test import APIRequestFactory

request = APIRequestFactory().get("/v2/articles/")
response = ArticleListView.as_view()(request, version="v2")
```

## In a real DRF project instead

Wire the same view through a real URL conf's version kwarg rather than
passing it directly:

```python
# urls.py
urlpatterns = [
    re_path(r"^(?P<version>v1|v2|v3)/articles/$", ArticleListView.as_view()),
]
```

See [Getting Started](getting-started.md) for the full request/response
cycle through a normal HTTP client.

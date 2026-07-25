# Getting Started

## Install

```bash
pip install drf-api-versioning
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_api_versioning",
]
```

## Declare your versions

```python
# settings.py
import datetime

API_VERSIONING = {
    "VERSIONS": {
        "v1": {
            "deprecated": datetime.date(2020, 1, 1),
            "sunset": datetime.date(2020, 6, 1),
            "deprecation_link": "https://example.com/docs/migrating-to-v3",
        },
        "v2": {
            "deprecated": datetime.date(2020, 1, 1),
            "deprecation_link": "https://example.com/docs/migrating-to-v3",
        },
        "v3": {},
    },
    "DEFAULT_VERSION": "v3",
}
```

Every key except a version's own name is optional - a version with an
empty dict (or omitted keys, like `v3` here) is fully supported, not
deprecated. `v1` is both deprecated and past its sunset date; `v2` is
deprecated but still active (no `sunset` key at all).

## Use a registry-aware versioning scheme

```python
# views.py
from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning


class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
    versioning_class = URLPathVersioning
```

This is a drop-in replacement for DRF's own `URLPathVersioning` -
`AcceptHeaderVersioning`, `QueryParameterVersioning`,
`NamespaceVersioning`, and `HostNameVersioning` are all available the
same way, matching whichever scheme you already use.

## What happens now

A request to `v2` (deprecated, still active) succeeds normally, with
extra response headers:

```
Deprecation: Wed, 01 Jan 2020 00:00:00 GMT
Link: <https://example.com/docs/migrating-to-v3>; rel="deprecation"
```

A request to `v1` (past its sunset date) gets:

```http
HTTP/1.1 410 Gone

{"detail": "API version 'v1' has been sunset as of 2020-06-01 and is no longer available."}
```

A request to a version that was never declared gets a 404 (or 406 for
`AcceptHeaderVersioning` - see [Architecture](architecture.md)) naming
what's actually supported:

```http
HTTP/1.1 404 Not Found

{"detail": "Unknown API version 'v9'. Supported versions: v1, v2, v3."}
```

## Check what's currently live

```bash
python manage.py list_api_versions
```

```
v1: sunset, deprecated 2020-01-01, sunset 2020-06-01 (https://example.com/docs/migrating-to-v3)
v2: deprecated, deprecated 2020-01-01 (https://example.com/docs/migrating-to-v3)
v3 (default): supported
```

See [Quick Start](quickstart.md) for the usage-tracking signal and
per-view header customization.

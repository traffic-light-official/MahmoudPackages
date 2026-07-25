# Quick Start

## Declare versions and use a scheme

```python
# settings.py
import datetime

API_VERSIONING = {
    "VERSIONS": {
        "v1": {"deprecated": datetime.date(2026, 1, 1)},
        "v2": {},
    },
    "DEFAULT_VERSION": "v2",
}
```

```python
# views.py
from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning


class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
    versioning_class = URLPathVersioning
```

## Tracking who's still using a deprecated version

```python
# apps.py or signals.py
from drf_api_versioning.signals import deprecated_version_used


def log_deprecated_usage(sender, *, request, version, version_info, **kwargs):
    logger.warning(
        "Deprecated API version used", extra={"version": version, "path": request.path}
    )


deprecated_version_used.connect(log_deprecated_usage)
```

Fires once per request resolving to a deprecated (but not rejected)
version - see [Architecture](architecture.md) for exactly when.

## Checking version status from the CLI

```bash
python manage.py list_api_versions
python manage.py list_api_versions --status sunset
```

## From Python

```python
from drf_api_versioning import all_versions, get_version_info

for info in all_versions():
    print(info.name, info.is_deprecated(), info.is_sunset())

v1 = get_version_info("v1")
if v1.is_sunset():
    ...
```

## Per-view header customization

`DeprecationHeaderMixin` reads header names from the `API_VERSIONING`
setting at response time - there's no per-view override, since the
header *names* are meant to be one project-wide convention. If one
specific view genuinely needs different behavior (a different header
format, an extra header), write your own `finalize_response` override
calling `registry.get_version_info(request.version)` directly - see
[Advanced Usage](advanced-usage.md#writing-your-own-response-header-logic).

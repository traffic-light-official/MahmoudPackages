# drf-api-versioning

[![PyPI version](https://img.shields.io/pypi/v/drf-api-versioning.svg)](https://pypi.org/project/drf-api-versioning/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-api-versioning.svg)](https://pypi.org/project/drf-api-versioning/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Enterprise API version lifecycle management for Django REST Framework:
a central version registry with deprecation/sunset dates, automatic
`Deprecation`/`Sunset`/`Link` response headers (RFC 8594-style), and
registry-aware versioning schemes that are drop-in replacements for
DRF's own.

```python
# settings.py
import datetime

API_VERSIONING = {
    "VERSIONS": {
        "v1": {
            "deprecated": datetime.date(2026, 1, 1),
            "sunset": datetime.date(2026, 7, 1),
            "deprecation_link": "https://example.com/docs/migrating-to-v2",
        },
        "v2": {},
    },
    "DEFAULT_VERSION": "v2",
}
```

## Why

DRF ships versioning *schemes* (how a version is resolved from a
request) but no version *lifecycle* - there's no built-in concept of "v1
is deprecated as of X and sunset as of Y," no automatic client-facing
signal that a version is going away, and no single source of truth a
health check or CI job can query. This package adds exactly that layer
on top of DRF's existing schemes, without replacing how you version
your API today.

## Features

- **A central version registry**: one Django setting declares every
  version's deprecation/sunset dates and migration link - the single
  source of truth for "what's supported right now."
- **Drop-in versioning schemes**: `URLPathVersioning`,
  `NamespaceVersioning`, `AcceptHeaderVersioning`,
  `QueryParameterVersioning`, `HostNameVersioning` - each a thin,
  registry-aware subclass of DRF's own, so switching is a one-line
  import change.
- **Automatic enforcement**: an unregistered version raises a clear 404
  (`UnknownAPIVersionError`, naming the supported versions); a version
  past its sunset date raises a 410 (`APIVersionSunsetError`) unless
  explicitly allowed.
- **RFC 8594-style response headers**: `DeprecationHeaderMixin` adds
  `Deprecation`/`Sunset`/`Link` headers automatically for a deprecated
  or sunset version - no per-view boilerplate.
- **A `deprecated_version_used` signal** for your own usage analytics
  (which clients still call v1?), with no bundled model or dependency.
- **`list_api_versions` management command** for a quick, scriptable
  inventory in CI or before writing release notes.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-api-versioning
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_api_versioning",
]
```

## Quick Start

```python
# views.py
from drf_api_versioning import DeprecationHeaderMixin, URLPathVersioning


class ArticleViewSet(DeprecationHeaderMixin, viewsets.ModelViewSet):
    versioning_class = URLPathVersioning
```

A request to a deprecated version now gets:

```
Deprecation: Thu, 01 Jan 2026 00:00:00 GMT
Sunset: Wed, 01 Jul 2026 00:00:00 GMT
Link: <https://example.com/docs/migrating-to-v2>; rel="deprecation"
```

A request to an unregistered version gets a 404 with a message listing
what's actually supported; a request past the sunset date gets a 410.

See [`docs/quickstart.md`](docs/quickstart.md) for the signal, the
management command, and per-version serializer selection patterns.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-api-versioning/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-versioning/LICENSE).

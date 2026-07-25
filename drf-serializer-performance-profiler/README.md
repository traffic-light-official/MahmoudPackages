# drf-serializer-performance-profiler

[![PyPI version](https://img.shields.io/pypi/v/drf-serializer-performance-profiler.svg)](https://pypi.org/project/drf-serializer-performance-profiler/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-serializer-performance-profiler.svg)](https://pypi.org/project/drf-serializer-performance-profiler/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Find slow fields in Django REST Framework serializers - per-field
timing and per-field query counts, with zero change to what's actually
serialized.

```python
from drf_serializer_performance_profiler import ProfileSerializerMixin


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
```

```
X-Serializer-Profile: comment_count=42.10ms (12q), author=3.20ms (1q), title=0.05ms (0q) (total=45.35ms, queries=13)
```

## Why

A slow API endpoint is often a slow *serializer*, not a slow query or a
slow view - a single `SerializerMethodField` computing an aggregate, or
a related field silently triggering a query per row, can dominate
response time while every other field is instant. DRF gives you no
built-in way to see *which* field is responsible; this package
instruments each field's `to_representation()` individually - timing
it and counting the database queries it triggers - without changing a
single byte of the actual serialized output.

## Features

- **`ProfileSerializerMixin`**: per-field timing + per-field query
  count, aggregated across every row in a list response.
- **`X-Serializer-Profile` response header**: opt-in and
  staff-restricted by default, showing the slowest fields first.
- **Passive slow-field logging**: log a warning whenever a field
  exceeds a configurable threshold, independent of the header feature -
  safe to leave on in production for ongoing monitoring.
- **Zero behavior change** - the exact same serialized output, byte for
  byte, as the same serializer without the mixin.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-serializer-performance-profiler
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Quick Start

```python
# settings.py
INSTALLED_APPS = [..., "drf_serializer_performance_profiler"]
SERIALIZER_PROFILER = {"ENABLED": True}  # off by default
```

```python
from drf_serializer_performance_profiler import ProfileSerializerMixin
from rest_framework import serializers


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
```

A staff user's request now carries an `X-Serializer-Profile` header
showing exactly which field is slow. See
[`docs/quickstart.md`](docs/quickstart.md) for the view-level mixin
that attaches the header, and the passive slow-field logger.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-serializer-performance-profiler/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-serializer-performance-profiler/LICENSE).

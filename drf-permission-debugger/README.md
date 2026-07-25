# drf-permission-debugger

[![PyPI version](https://img.shields.io/pypi/v/drf-permission-debugger.svg)](https://pypi.org/project/drf-permission-debugger/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-permission-debugger.svg)](https://pypi.org/project/drf-permission-debugger/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Understand exactly why a Django REST Framework permission check
granted or denied a request - without changing its behavior.

```python
from drf_permission_debugger import PermissionDebugMixin


class ArticleViewSet(PermissionDebugMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

```
X-Permission-Trace: IsAuthenticated=granted, IsOwnerOrReadOnly=denied
```

## Why

A `403 Forbidden` from DRF tells you a request was denied - not
*which* of your (possibly several) configured permission classes
denied it, or why, once `permission_classes` has more than one entry.
This package records every configured permission class's outcome for
each request, in the exact order and with the exact early-exit-on-
first-denial behavior DRF's own `check_permissions()`/
`check_object_permissions()` already have - mixing it in never changes
who is authorized to do what, only what you can *see* about that
decision.

## Features

- **`PermissionDebugMixin`**: records a full trace (granted/denied,
  message, code, request-level vs. object-level) for every permission
  check, exposed as a response header - opt-in and staff-restricted by
  default, never leaked to a real user by accident.
- **`describe_permissions()`/`describe_view()`**: static introspection
  of a view's permission/authentication/throttle stack with no live
  request at all - useful in a shell or a test.
- **`show_view_permissions` management command**: resolve a URL path
  and print its full permission stack from the command line.
- **Zero behavior change** - the exact same grant/deny outcome, in the
  exact same order, as an undecorated view.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-permission-debugger
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Quick Start

```python
# settings.py
INSTALLED_APPS = [..., "drf_permission_debugger"]
PERMISSION_DEBUGGER = {"ENABLED": True}  # off by default
```

```python
from drf_permission_debugger import PermissionDebugMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
```

Requests from a staff user now carry an `X-Permission-Trace` header
showing exactly what was checked. See
[`docs/quickstart.md`](docs/quickstart.md) for the response-body trace
option and the `show_view_permissions` command.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-permission-debugger/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-permission-debugger/LICENSE).

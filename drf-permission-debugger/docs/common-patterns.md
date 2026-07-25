# Common Patterns

## Debugging a "why is this endpoint returning 403" support ticket

The fastest path: temporarily enable the trace for the affected user
(or ask them to check as staff), reproduce the request, and read the
header - no code changes, no debugger attached, no reproducing locally
against production data:

```python
# settings.py (temporarily, or gated by an env var in staging)
PERMISSION_DEBUGGER = {"ENABLED": True}
```

```
X-Permission-Trace: IsAuthenticated=granted, HasActiveSubscription=denied
```

Immediately answers "which permission, and in what order" without
adding a single `print()` or breakpoint.

## Enabling only in staging, never in production

```python
# settings.py
import os

PERMISSION_DEBUGGER = {
    "ENABLED": os.environ.get("ENVIRONMENT") != "production",
}
```

Combine with the default `RESTRICT_TO_STAFF: True` for defense in depth
- even if `ENABLED` is accidentally left on in production, only staff
users ever see anything.

## Asserting a viewset requires the permission you expect, in CI

```python
from drf_permission_debugger import describe_permissions


def test_article_viewset_requires_authentication():
    names = [p.name for p in describe_permissions(ArticleViewSet)]
    assert "IsAuthenticated" in names


def test_article_update_checks_ownership():
    descriptions = describe_permissions(ArticleViewSet)
    owner_check = next(d for d in descriptions if d.name == "IsOwner")
    assert owner_check.checks_object_permission is True
```

Catches a permission class being accidentally removed or reordered
during a refactor, without needing a full request/response test for
every possible permission combination.

## Recording denial metrics without exposing anything over HTTP

```python
from drf_permission_debugger import PermissionDebugMixin, get_permission_trace


class MetricsPermissionMixin(PermissionDebugMixin):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        trace = get_permission_trace(self)
        if trace and (denied := trace.denied_by):
            metrics.increment("permission_denied", tags={"permission": denied.permission_class})
        return response
```

Leave `PERMISSION_DEBUGGER = {"ENABLED": False}` (the default) - this
pattern reads the trace directly via `get_permission_trace()`, which
always works regardless of the HTTP-exposure setting.

## Documenting a view's permission stack automatically

```bash
python manage.py show_view_permissions /api/articles/1/ >> docs/permissions.txt
```

Useful as a pre-release check alongside API documentation generation -
diff the output against a previous release to catch an unintentional
permission change.

## Combining with `drf-api-versioning`'s deprecation headers

Both packages override `finalize_response` additively - list them in
whatever MRO order makes sense for your other mixins, since neither
overwrites the other's header:

```python
class ArticleViewSet(PermissionDebugMixin, DeprecationHeaderMixin, ModelViewSet):
    ...
```

```
X-Permission-Trace: IsAuthenticated=granted
Deprecation: Wed, 01 Jan 2026 00:00:00 GMT
```

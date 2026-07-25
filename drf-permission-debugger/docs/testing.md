# Testing

## Running this package's own test suite

```bash
pip install -e ".[test]"
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

Across the full Python/Django support matrix via [tox](https://tox.wiki):

```bash
tox
```

## Proving the mixin never changes behavior

This is the single most important property to test if you extend or
modify this package (see
[Architecture](architecture.md#the-core-guarantee-identical-behavior-to-a-plain-apiview)).
This package's own `tests/test_integration.py::TestBehaviorIsUnchanged`
demonstrates the pattern: assert the exact same status code and
`detail` message a plain, undecorated view would produce, both for a
granted and a denied request.

```python
def test_denied_request_still_returns_403(api_client, make_user):
    user = make_user()
    api_client.force_authenticate(user=user)
    response = api_client.get("/multi-denied/")
    assert response.status_code == 403
    assert response.json()["detail"] == "Denied by DenyAll."
```

## Testing the trace header requires enabling the setting and authenticating as staff

```python
from django.test import override_settings


def test_staff_user_sees_the_trace_header(api_client, make_user):
    staff = make_user(is_staff=True)
    api_client.force_authenticate(user=staff)
    with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
        response = api_client.get("/multi-denied/")
    assert response.headers["X-Permission-Trace"] == "IsAuthenticated=granted, DenyAll=denied"
```

Forgetting either `ENABLED: True` or a staff user is the most common
reason a trace-header test fails unexpectedly with a `KeyError` on the
header lookup - see [Troubleshooting](troubleshooting.md).

## Testing an object-level trace

Remember the combined trace includes *both* the request-level and
object-level pass over the same permission classes (see
[Architecture](architecture.md#why-the-trace-accumulates-across-both-request-level-and-object-level-checks)) -
assert against the full sequence, not just the object-level half:

```python
def test_object_level_check_is_recorded(api_client, make_article, make_user):
    owner = make_user()
    other_staff = make_user(is_staff=True)
    article = make_article(owner=owner)
    api_client.force_authenticate(user=other_staff)

    with override_settings(PERMISSION_DEBUGGER={"ENABLED": True}):
        response = api_client.get(f"/articles/{article.pk}/")

    assert response.status_code == 403
    assert response.headers["X-Permission-Trace"] == (
        "IsAuthenticated=granted, IsOwner=granted, IsAuthenticated=granted, IsOwner=denied"
    )
```

## Testing the trace directly, without going through a full request

```python
from drf_permission_debugger import get_permission_trace
from rest_framework.test import APIRequestFactory


def test_trace_records_both_permissions(db):
    request = APIRequestFactory().get("/articles/1/")
    view = ArticleViewSet()
    view.request = view.initialize_request(request)
    view.check_permissions(view.request)

    trace = get_permission_trace(view)
    assert [r.permission_class for r in trace.results] == ["IsAuthenticated", "IsOwner"]
```

## Testing `describe_permissions()`/`describe_view()`

No database, no client, no `@pytest.mark.django_db` needed - these are
pure functions over a class object:

```python
def test_describes_object_level_permission():
    descriptions = describe_permissions(ArticleViewSet)
    by_name = {d.name: d for d in descriptions}
    assert by_name["IsOwner"].checks_object_permission is True
```

## Testing the management command

```python
import io
from django.core.management import call_command


def test_show_view_permissions_prints_the_stack(db):
    out = io.StringIO()
    call_command("show_view_permissions", "/articles/1/", stdout=out)
    assert "IsOwner [object-level]" in out.getvalue()
```

## Fixtures used by this package's own suite

`tests/test_app` declares an `Article` model with an `owner` FK, custom
`DenyAll`/`IsOwner` permission classes (request-level and object-level
respectively, to exercise both code paths), and one view per feature
this package adds, including a plain Django function-based view (to
test the management command's "not a class-based view" error) and a
permission class with no docstring of its own (to test
`describe_permissions()`'s non-inheriting docstring behavior) - reuse
this shape in your own project's test suite.

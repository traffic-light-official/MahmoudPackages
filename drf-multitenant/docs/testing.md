# Testing

This page covers testing tenant isolation *in your own project*. For
running this package's own test suite, see [Contributing](contributing.md).

## Fixtures for two tenants

```python
# conftest.py
import pytest
from accounts.models import Tenant

@pytest.fixture
def tenant_a(db):
    return Tenant.objects.create(name="Acme", slug="acme")

@pytest.fixture
def tenant_b(db):
    return Tenant.objects.create(name="Globex", slug="globex")
```

## Binding a tenant in a test

```python
from drf_multitenant.testing import as_tenant

def test_creating_an_article(tenant_a):
    with as_tenant(tenant_a):
        article = Article.objects.create(title="Hello")
    assert article.tenant_id == tenant_a.pk
```

`as_tenant` is a plain alias for
`drf_multitenant.context.tenant_context` — use whichever name reads
better in context; they're the same function.

## Explicitly testing the "no tenant" case

```python
from drf_multitenant.testing import as_no_tenant

def test_no_articles_visible_with_no_tenant_bound(tenant_a):
    with as_tenant(tenant_a):
        Article.objects.create(title="Hello")

    with as_no_tenant():
        assert list(Article.objects.all()) == []
```

## Asserting isolation directly

```python
from drf_multitenant.testing import assert_no_cross_tenant_leak

def test_query_never_returns_another_tenants_rows(tenant_a, tenant_b):
    with as_tenant(tenant_a):
        Article.objects.create(title="A's article")
    with as_tenant(tenant_b):
        Article.objects.create(title="B's article")

    with as_tenant(tenant_a):
        rows = list(Article.objects.all())
    assert_no_cross_tenant_leak(rows, tenant_a)  # raises TenantLeakError if not
```

## Testing through real HTTP requests

Set the resolver's header directly rather than binding the context
manually — this exercises `TenantMiddleware` end-to-end, the same path
production traffic takes:

```python
def test_list_endpoint_is_isolated(client, tenant_a, tenant_b):
    with as_tenant(tenant_a):
        Article.objects.create(title="A's article")
    with as_tenant(tenant_b):
        Article.objects.create(title="B's article")

    response = client.get("/articles/", HTTP_X_TENANT_ID=str(tenant_a.pk))
    titles = {row["title"] for row in response.json()}
    assert titles == {"A's article"}
```

## Testing a request with no tenant

```python
def test_rejected_with_no_tenant_header(client):
    response = client.get("/articles/")
    assert response.status_code == 400  # STRICT default
```

## Testing your own resolver

Resolvers are plain `(request) -> tenant | None` functions — test them
directly with `django.test.RequestFactory`, no middleware or client
needed:

```python
from django.test import RequestFactory
from myproject.resolvers import api_key_resolver

def test_api_key_resolver_finds_the_right_tenant(tenant_a):
    ApiKey.objects.create(tenant=tenant_a, key="secret")
    request = RequestFactory().get("/", HTTP_AUTHORIZATION="Bearer secret")
    assert api_key_resolver(request) == tenant_a
```

## Running this package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-multitenant.git
cd drf-multitenant
pip install -e ".[dev]"
pytest --cov
```

Tests span context propagation, queryset scoping (including the
import-time-safety regression covered in [FAQ](faq.md)), model
save-time enforcement, resolvers, middleware (including strict/non-strict
modes), permissions, serializers (including the defense-in-depth path
when field-level scoping is bypassed), caching, admin integration, and
full end-to-end HTTP request flows — comfortably above the 90% coverage
floor enforced by `pytest-cov`'s `fail_under` in `pyproject.toml`.

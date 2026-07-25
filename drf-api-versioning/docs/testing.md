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

## Testing each versioning scheme without a full URL conf

Every scheme needs the kwargs a real URL dispatch would have supplied.
This package's own `tests/test_app` demonstrates all five against real
views - the pattern for each:

### URLPathVersioning

```python
response = api_client.get("/v2/articles/")  # version baked into the URL
```

or, calling the view directly:

```python
response = ArticleViewSet.as_view({"get": "list"})(request, version="v2")
```

### QueryParameterVersioning

```python
response = api_client.get("/articles/?version=v2")
```

### AcceptHeaderVersioning

```python
response = api_client.get("/articles/", HTTP_ACCEPT="application/json; version=v2")
```

### NamespaceVersioning

Requires a real URL conf with the version as a namespace
(`path("v2/", include(("app.urls", "app"), namespace="v2"))`) - there is
no equivalent of passing a kwarg directly, since the namespace comes
from URL resolution itself, not a view kwarg.

### HostNameVersioning

```python
response = api_client.get("/articles/", HTTP_HOST="v2.example.com")
```

Requires `"v2.example.com"` (or a wildcard) in `ALLOWED_HOSTS`, and a
three-part hostname matching `HostNameVersioning.hostname_regex`
(`subdomain.domain.tld` - a bare `"testserver"` never matches, and
falls back to `default_version`).

## Testing deprecation headers

Assuming a registry with `v_deprecated_only` (a `deprecated` date, no
`sunset`) and `v_scheduled` (both `deprecated` and a future `sunset`
date):

```python
def test_deprecated_but_active_version_gets_deprecation_header_only(api_client):
    response = api_client.get("/v_deprecated_only/articles/")
    assert response["Deprecation"]  # RFC 7231 HTTP-date string
    assert "Sunset" not in response


def test_deprecated_version_with_a_scheduled_sunset_gets_both_headers(api_client):
    response = api_client.get("/v_scheduled/articles/")
    assert response["Deprecation"]
    assert response["Sunset"]
```

## Testing sunset rejection

```python
def test_sunset_version_returns_410(api_client):
    response = api_client.get("/v0/articles/")  # past its sunset date
    assert response.status_code == 410
```

## Testing the `deprecated_version_used` signal fires

```python
def test_signal_fires_for_deprecated_version(api_client):
    received = []
    handler = lambda sender, **kwargs: received.append(kwargs)  # noqa: E731
    deprecated_version_used.connect(handler)
    try:
        api_client.get("/v1/articles/")
    finally:
        deprecated_version_used.disconnect(handler)

    assert len(received) == 1
    assert received[0]["version"] == "v1"
```

Always `disconnect` in a `finally` block (or use a fixture with
teardown) - a receiver left connected leaks into unrelated later tests.

## Testing with `override_settings`

```python
from django.test import override_settings


@override_settings(API_VERSIONING={"VERSIONS": {"v1": {}}, "ALLOW_SUNSET": True})
def test_allow_sunset_override(api_client):
    ...
```

Works correctly because the settings cache is invalidated via Django's
own `setting_changed` signal - no manual cache-clearing needed (see
[Architecture](architecture.md)).

## Fixtures used by this package's own suite

`tests/test_app` declares a three-version registry (`v1`: deprecated
and sunset, both in the past; `v2`: deprecated only; `v3`: fully
supported, the default) and one view per versioning scheme - reuse this
shape (permanently-past dates for "already deprecated/sunset" scenarios,
so tests never depend on when they happen to run) in your own project's
test fixtures.

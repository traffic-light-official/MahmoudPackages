# Installation

```bash
pip install drf-async
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Why the Django floor is 4.2

This package relies on the async ORM (`QuerySet.aget`/`.acreate`,
`Model.asave`/`.adelete`, `.aiterator()`) and the async cache API
(`cache.aget`/`.aset`), both stable since Django 4.2 - there is no
lower-version fallback, since bridging every ORM call through a thread
would defeat the entire point of this package.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_async",
]
```

Registering the app is for consistency with this workspace's other
packages only - `drf_async` defines no models and needs no
app-loading side effects of its own, so there is nothing to migrate and
nothing that breaks if you forget this step (though `manage.py check`
conventions in most projects expect every first-party dependency to be
listed).

## Serve over ASGI to get real concurrency

Async views work under Django's WSGI handler too, but Django wraps
each async view in its own event loop per request in that case, one
thread per request - you get correctness, not extra throughput.
To actually benefit from this package, run your project behind an ASGI
server:

```bash
pip install uvicorn
uvicorn myproject.asgi:application
```

See [Deployment](deployment.md) for a complete ASGI production setup.

## Verifying the install

```python
>>> import drf_async
>>> drf_async.__version__
'1.0.0'
```

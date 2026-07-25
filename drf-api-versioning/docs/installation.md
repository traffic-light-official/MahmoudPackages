# Installation

```bash
pip install drf-api-versioning
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_api_versioning",
]
```

Required for `API_VERSIONING` setting validation on app load and for
the `list_api_versions` management command. No migrations to run -
this package defines no models.

## Declaring at least one version is required

Unlike most settings-driven packages in this workspace, `API_VERSIONING`
has no usable "all defaults" state: `VERSIONS` must declare at least one
version, or `ImproperlyConfigured` is raised the first time any setting
is accessed (see [Settings](settings.md)). There is no sensible default
version registry to fall back to.

## Verifying the install

```python
>>> import drf_api_versioning
>>> drf_api_versioning.__version__
'1.0.0'
```

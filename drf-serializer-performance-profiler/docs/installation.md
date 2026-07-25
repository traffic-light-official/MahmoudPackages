# Installation

```bash
pip install drf-serializer-performance-profiler
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Django project setup

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_serializer_performance_profiler",
]
```

This package defines no models, so there's nothing to migrate -
registering the app is for consistency with this workspace's other
packages only.

## No extra dependencies

This package's only runtime dependencies are Django and Django REST
Framework themselves - query counting uses Django's own public
`connection.execute_wrapper()` hook, not a third-party profiling
library.

## Verifying the install

```python
>>> import drf_serializer_performance_profiler
>>> drf_serializer_performance_profiler.__version__
'1.0.0'
```

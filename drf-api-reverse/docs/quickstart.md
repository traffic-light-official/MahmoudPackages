# Quick Start

## The CLI

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
drf-api-reverse check --schema api/contract.yml --output myapp/
```

## The Django management command

```bash
python manage.py scaffold_api --schema api/contract.yml --output myapp/
```

Requires `drf_api_reverse` in `INSTALLED_APPS` (see
[Installation](installation.md)).

## From Python

```python
from drf_api_reverse import load_schema_file, scaffold

schema = load_schema_file("api/contract.yml")
for result in scaffold(schema, "myapp/"):
    verb = "Created" if result.created else "Updated"
    print(f"{verb} {result.filename}")
    for key in result.orphaned_keys:
        print(f"  note: {key} has no corresponding schema entry anymore")
```

```python
from drf_api_reverse import check_drift, load_schema_file

schema = load_schema_file("api/contract.yml")
for report in check_drift(schema, "myapp/"):
    print(f"{report.filename}: {'DRIFTED' if report.has_drift else 'in sync'}")
```

## What gets generated

For each `components.schemas` entry, one `serializers.Serializer`
subclass. For each top-level path segment (e.g. everything under
`/articles/...`), one `viewsets.ViewSet` subclass with
`list`/`create`/`retrieve`/`update`/`partial_update`/`destroy` methods
mapped from standard collection/detail paths, plus `@action`-decorated
methods for one level of nested sub-resource path (e.g.
`/articles/{id}/comments/`). See [Architecture](architecture.md) for
the exact classification rules and what falls outside them.

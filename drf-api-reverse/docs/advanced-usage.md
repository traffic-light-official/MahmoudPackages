# Advanced Usage

## Using the library programmatically

Every CLI capability is a plain function:

```python
from drf_api_reverse import load_schema_file, raise_if_drifted, scaffold
from drf_api_reverse.exceptions import DriftDetectedError

schema = load_schema_file("api/contract.yml")
scaffold(schema, "myapp/")

try:
    raise_if_drifted(schema, "myapp/")
except DriftDetectedError as exc:
    print(f"Drift found: {exc}")
```

## Scaffolding from any schema source, not just a file

`scaffold()`/`check_drift()` take plain dicts - load them however you
like:

```python
import requests

from drf_api_reverse import scaffold

schema = requests.get("https://contracts.example.com/api/v2/openapi.json", timeout=10).json()
scaffold(schema, "myapp/")
```

## Django management command

```bash
python manage.py scaffold_api --schema api/contract.yml --output myapp/
python manage.py scaffold_api --schema api/contract.yml --output myapp/ --check
```

Requires `drf_api_reverse` in `INSTALLED_APPS`. Unlike the standalone
CLI, it does not require the package to be run as a console script -
useful if your team already standardizes on `manage.py` for all
project tooling. See
[Common Patterns](common-patterns.md#running-scaffold-in-a-pre-commit-hook).

## Generating only one of the three files

The three generators are independently callable if you only need one
file's worth of output (e.g. you maintain `urls.py` by hand but want
generated serializers):

```python
from drf_api_reverse.codegen.serializers import generate_serializer_regions, render_file
from drf_api_reverse import load_schema_file

schema = load_schema_file("api/contract.yml")
print(render_file(schema))  # a complete, brand-new serializers.py

# Or just the region bodies, to merge into an existing file yourself:
regions = generate_serializer_regions(schema)
```

The same pattern applies to `drf_api_reverse.codegen.views` and
`drf_api_reverse.codegen.urls`.

## Writing your own generator against the same region-merge engine

If you need a fourth generated file (e.g. a `filters.py` following the
same naming conventions), reuse `drf_api_reverse.regions.merge()`
directly rather than re-implementing marker parsing:

```python
from pathlib import Path

from drf_api_reverse.regions import merge

def scaffold_filters(schema: dict, output_path: Path) -> None:
    regions = {
        f"filterset:{name}": f"class {name}FilterSet(filters.FilterSet):\n    pass"
        for name in (schema.get("components") or {}).get("schemas", {})
    }
    if output_path.exists():
        new_text, orphaned = merge(output_path.read_text(encoding="utf-8"), regions)
    else:
        new_text = "\n\n".join(regions.values()) + "\n"
    output_path.write_text(new_text, encoding="utf-8")
```

## Inspecting resource grouping and operation classification directly

Useful when writing your own generator, or when debugging why an
operation ended up `"unsupported"`:

```python
from drf_api_reverse.codegen.operations import parse_resource_groups

for group in parse_resource_groups(schema):
    print(group.key, group.base_path)
    for op in group.operations:
        print(" ", op.method.upper(), op.path, "->", op.kind, op.drf_method_name)
```

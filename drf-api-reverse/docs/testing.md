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

## Asserting that regeneration is a no-op

The core guarantee of this package is that re-scaffolding with an
unchanged schema produces no meaningful diff - assert exactly that in
your own project's tests:

```python
from pathlib import Path

from drf_api_reverse import load_schema_file, scaffold


def test_rescaffolding_is_idempotent(tmp_path: Path) -> None:
    schema = load_schema_file("api/contract.yml")
    scaffold(schema, tmp_path)
    before = (tmp_path / "views.py").read_text(encoding="utf-8")

    scaffold(schema, tmp_path)
    after = (tmp_path / "views.py").read_text(encoding="utf-8")

    assert before == after
```

## Asserting hand-written code survives regeneration

```python
def test_custom_helper_survives_regeneration(tmp_path: Path) -> None:
    schema = load_schema_file("api/contract.yml")
    scaffold(schema, tmp_path)

    views_path = tmp_path / "views.py"
    views_path.write_text(
        views_path.read_text(encoding="utf-8") + "\n\ndef my_helper():\n    return 42\n",
        encoding="utf-8",
    )

    scaffold(schema, tmp_path)

    assert "def my_helper():" in views_path.read_text(encoding="utf-8")
```

## Testing that generated code is valid Python

Useful as a smoke test whenever you change the contract in a
non-trivial way:

```python
def test_generated_files_compile(tmp_path: Path) -> None:
    schema = load_schema_file("api/contract.yml")
    scaffold(schema, tmp_path)

    for filename in ("serializers.py", "views.py", "urls.py"):
        source = (tmp_path / filename).read_text(encoding="utf-8")
        compile(source, filename, "exec")
```

## Testing drift detection in CI

```python
import pytest

from drf_api_reverse import load_schema_file, raise_if_drifted, scaffold
from drf_api_reverse.exceptions import DriftDetectedError


def test_committed_scaffolding_matches_the_contract() -> None:
    schema = load_schema_file("api/contract.yml")
    raise_if_drifted(schema, "myapp/")  # raises DriftDetectedError if out of sync
```

Run this as a real test in CI (not just the standalone
`drf-api-reverse check` step) if you want a normal `pytest` failure
report rather than a separate CI step's exit code to interpret.

## Testing your own generated `ViewSet` before implementing it

Every generated method starts as `raise NotImplementedError(...)` -
assert that explicitly for methods you haven't implemented yet, so a
test suite documents scaffolding-stage endpoints rather than silently
skipping them:

```python
def test_unimplemented_endpoint_raises_not_implemented(api_client) -> None:
    with pytest.raises(NotImplementedError):
        api_client.get("/articles/")
```

Remove each such test as you replace the corresponding method body with
a real implementation.

## Fixtures used by this package's own suite

`tests/conftest.py` provides a `sample_schema` fixture (a small but
representative OpenAPI document covering a referenced nested schema, an
enum, both array-of-primitive and array-of-`$ref` fields, and a nested
sub-resource path) - reuse this shape when writing your own contract
fixtures rather than re-deriving one from scratch.

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

## Testing your own schema diffs without touching Git

`diff_schemas()` takes plain dicts - build the two schemas in-line
rather than committing fixture files:

```python
from drf_changelog_generator import diff_schemas


def test_removing_a_required_field_is_breaking():
    old = {
        "paths": {
            "/widgets/": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                    "required": ["name"],
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new = {
        "paths": {
            "/widgets/": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {}, "required": []}
                            }
                        }
                    }
                }
            }
        }
    }

    diff = diff_schemas(old, new)

    assert diff.has_breaking_changes
    assert any("name" in c.message for c in diff.breaking_changes)
```

## Testing against a real Git repository

Use a real, disposable repository in a `tmp_path` rather than mocking
`subprocess` - `git show` is fast and this exercises the actual
subprocess boundary, matching this package's own
`tests/conftest.py::git_repo` fixture:

```python
import subprocess
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    run("init", "-b", "main")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")

    (repo / "schema.yml").write_text(yaml.safe_dump({"openapi": "3.0.3", "paths": {}}), encoding="utf-8")
    run("add", "schema.yml")
    run("commit", "-m", "v1")
    run("tag", "v1.0.0")

    return repo


def test_load_schema_at_ref(git_repo: Path) -> None:
    from drf_changelog_generator.git_utils import load_schema_at_ref

    schema = load_schema_at_ref(repo=git_repo, ref="v1.0.0", file_path="schema.yml")
    assert schema["openapi"] == "3.0.3"
```

## Testing the CLI end-to-end

Call `main()` directly with an argument list rather than invoking a
subprocess - it returns the process exit code and is fully testable
in-process:

```python
from pathlib import Path

from drf_changelog_generator.cli import main


def test_fail_on_breaking_exits_1(tmp_path: Path) -> None:
    old = tmp_path / "old.yml"
    new = tmp_path / "new.yml"
    old.write_text("openapi: 3.0.3\npaths: {}\n", encoding="utf-8")
    new.write_text("openapi: 3.0.3\npaths: {}\n", encoding="utf-8")

    exit_code = main(
        ["diff", "--old-file", str(old), "--new-file", str(new), "--fail-on-breaking"]
    )

    assert exit_code == 0  # identical schemas: nothing breaking
```

## Testing the `generate_changelog` management command

Requires `drf-spectacular` installed and a real Django app with URLs to
generate a schema from - this package's own
`tests/test_app/` is a minimal working example to copy the pattern from:

```python
from django.core.management import call_command


def test_generate_changelog_command(git_repo, capsys):
    call_command(
        "generate_changelog",
        "--old-ref", "v1.0.0",
        "--schema-path", "schema.yml",
        "--repo", str(git_repo),
    )
    assert "API Changelog" in capsys.readouterr().out
```

## Fixtures used by this package's own suite

`tests/conftest.py` provides `old_schema`/`new_schema` (a rich pair of
OpenAPI documents covering every `ChangeKind`) and `git_repo` (a real,
temporary Git repository with two tagged commits) - reuse this pattern
in your own project's `conftest.py` rather than re-deriving fixture
schemas from scratch.

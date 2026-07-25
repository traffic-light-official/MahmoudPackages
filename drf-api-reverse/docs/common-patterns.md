# Common Patterns

## Delegating generated method bodies to real logic immediately

Don't write substantial logic directly inside a generated `ViewSet`
method - it lives inside a marked region and will be silently
regenerated back to `raise NotImplementedError(...)` the next time the
underlying schema operation changes shape (see
[Architecture](architecture.md#idempotent-regeneration-how-it-actually-works)).
Instead, delegate immediately to a real implementation defined outside
any region:

```python
# myapp/views.py (generated, then hand-edited)
from .logic import list_articles  # your own, non-generated module


class ArticlesViewSet(viewsets.ViewSet):
    serializer_class = ArticleSerializer

    def list(self, request, *args, **kwargs):
        return list_articles(self, request)

    # ... the rest, generated, unchanged
```

Re-running `scaffold` regenerates the `def list(...)` line and its
one-line body exactly as before (since the underlying schema didn't
change) - a no-op diff - while `myapp/logic.py` is never touched at
all, since it isn't a generated file.

## Gating a PR on contract drift

```yaml
- uses: actions/checkout@v4
- run: pip install drf-api-reverse
- run: drf-api-reverse check --schema api/contract.yml --output myapp/
```

Fails the job if the committed `myapp/serializers.py`/`views.py`/`urls.py`
no longer match what `api/contract.yml` would currently produce - i.e.
someone changed the contract (or hand-edited a generated region) and
forgot to run `scaffold` and commit the result.

## Running `scaffold` in a pre-commit hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: api-scaffold
      name: Regenerate DRF scaffolding from the API contract
      entry: python manage.py scaffold_api --schema api/contract.yml --output myapp/
      language: system
      pass_filenames: false
```

Regenerating is idempotent and safe to run on every commit - if nothing
in the contract changed, no file changes at all (see
[Testing](testing.md#asserting-that-regeneration-is-a-no-op)).

## Splitting a large contract across multiple Django apps

`scaffold()` always writes one `serializers.py`/`views.py`/`urls.py`
triplet per call - for a contract spanning several apps, split the
OpenAPI document into one file per app (a `paths`/`components.schemas`
subset each) rather than trying to scaffold one document into multiple
output directories:

```bash
drf-api-reverse scaffold --schema api/articles.yml --output articles_app/
drf-api-reverse scaffold --schema api/accounts.yml --output accounts_app/
```

## Reviewing exactly what changed after regenerating

Since generated regions are marker-delimited, a plain `git diff` after
re-running `scaffold` already isolates the change to the specific
region(s) whose schema entry changed - there's no need for a
specialized diff tool. If a change touches more regions than expected,
that's itself a signal worth double-checking (e.g. a schema you thought
was unrelated actually shares a `$ref` with the one you changed).

## Detecting a schema entry that was removed but not cleaned up

```python
from drf_api_reverse import check_drift, load_schema_file

schema = load_schema_file("api/contract.yml")
for report in check_drift(schema, "myapp/"):
    if report.orphaned_keys:
        print(f"{report.filename} has stale regions: {report.orphaned_keys}")
```

`orphaned_keys` lists generated regions still on disk that no longer
correspond to anything in the current contract - useful for a periodic
cleanup pass distinct from the CI drift gate (which typically treats
*any* drift, orphaned or not, as failing).

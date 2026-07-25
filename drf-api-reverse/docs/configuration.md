# Configuration

This package has no Django settings and no configuration file - every
option is a CLI flag (or the equivalent management command option). See
[Settings](settings.md) for the complete flag reference.

## Choosing where to write generated code

`--output` is any directory - it will be created if it does not already
exist. A common layout is one directory per Django app:

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

The generated `urls.py` imports from `.views`, and the generated
`views.py` imports from `.serializers` (both relative imports) - so the
three files must stay together in the same package/directory. If you
need to split them up further, do that by hand-editing after scaffold
runs; the region markers don't care where the file physically lives, so
re-running `scaffold` against the original combined directory still
works even if you've since moved a copy elsewhere.

## Choosing which schema to scaffold from

`--schema` accepts a local JSON or YAML file (auto-detected from
content, not just extension - see [`schema_loader.parse_schema`](api-reference.md#parse_schema)).
There is no `--repo`/`--ref` mode (unlike the CLI of the sibling
`drf-changelog-generator` package) - this package always scaffolds from
a schema file already on disk, since scaffolding from a historical Git
ref rarely makes sense (you want to scaffold from where the contract is
*going*, not where it *was*).

## One contract, multiple apps

If different parts of one large OpenAPI contract correspond to
different Django apps, split the contract into multiple files (one per
app) rather than trying to scaffold a single combined document into
multiple output directories - `scaffold()` always writes exactly one
`serializers.py`/`views.py`/`urls.py` triplet per invocation.

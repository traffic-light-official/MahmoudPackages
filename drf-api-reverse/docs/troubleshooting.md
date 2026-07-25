# Troubleshooting

## `RegionMergeError: BEGIN marker for '...' has no matching END marker`

Someone hand-edited a generated file and deleted (or broke) an `# ===
END DRF-API-REVERSE GENERATED: ... ===` line, or a merge conflict
resolution left a `BEGIN` marker orphaned. Fix the markers by hand (or
delete the file and let `scaffold` recreate it from scratch - any
custom code outside the broken region is lost only if you delete the
whole file, not if you just repair the marker pair).

## `RegionMergeError: Duplicate generated region key '...' in existing file`

Two copy-pasted regions share the same key - most commonly from
manually copying a generated block instead of letting `scaffold`
produce a second one. Region keys must be unique within a file; rename
one of the `BEGIN`/`END` marker pairs, or better, let `scaffold`
regenerate the file after fixing the underlying schema so only one
region per key exists.

## A field I expected to be a nested serializer is a plain `DictField()` instead

Two possibilities, both intentional and documented, not bugs:

1. The field's schema is an **inline anonymous object**
   (`{"type": "object", "properties": {...}}`) rather than a `$ref` -
   this package only generates nested serializers for `$ref`s to a
   named `components.schemas` entry; give the object a name in
   `components.schemas` and reference it via `$ref` if you want a real
   nested serializer.
2. The field is part of a **circular reference** between two schemas -
   see [FAQ](faq.md#what-happens-with-a-circular-schema-reference).

## `check`/CI reports drift but I didn't change anything

Confirm you're comparing the *same* schema file CI is checking against
- a schema regenerated fresh in CI (e.g. via `drf-spectacular`) will
almost never byte-for-byte match a hand-maintained
`api/contract.yml` unless they're deliberately kept identical; use one
canonical schema file, checked into version control, for both
scaffolding and checking.

## An operation is missing from the generated `ViewSet` entirely, with no comment either

Check that the path is actually present under `paths` in the schema you
passed - a schema loaded from the wrong file, or a `paths` key that
didn't survive a manual YAML edit (bad indentation silently dropping a
key), produces no operations for that path at all, which looks
identical to "this operation was never in the contract." Validate the
schema parses as expected first: `python -c "from drf_api_reverse import
load_schema_file; print(load_schema_file('api/contract.yml')['paths'].keys())"`.

## `ImportError: attempted relative import with no known parent package` when testing generated files directly

The generated `views.py`/`urls.py` use relative imports
(`from .serializers import *`) and are meant to be imported as part of
a real Django app package (with an `__init__.py`), not executed or
imported as standalone scripts. If you're smoke-testing generated
output outside a real app (e.g. in a scratch directory), add an empty
`__init__.py` next to the three generated files and import the
directory as a package rather than running a file directly.

## `scaffold_api: command not found` / `Unknown command: 'scaffold_api'`

Add `drf_api_reverse` to `INSTALLED_APPS` - Django only discovers
management commands from installed apps (see [Installation](installation.md#django-project-setup)).

## The CLI exits with status `2` and "Error: ..."

Status `2` means the schema file could not be loaded - either it
doesn't exist (`OSError`) or it isn't valid JSON/YAML
(`SchemaParseError`). Confirm the path passed to `--schema` and that
the file parses standalone: `python -c "import yaml; yaml.safe_load(open('api/contract.yml'))"`.

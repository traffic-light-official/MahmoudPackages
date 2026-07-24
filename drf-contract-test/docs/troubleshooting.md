# Troubleshooting

## `SchemaGenerationError: Could not initialize Django`

`django.setup()` failed — usually an invalid `--settings`/`DJANGO_SETTINGS_MODULE`
value, or a settings module that itself raises on import (missing
environment variables, a bad database URL, etc.). Run
`python -c "import django, os; os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'; django.setup()"`
directly to see the underlying traceback — this package re-raises the
original exception's message but doesn't suppress it.

## `SchemaLoadError: Schema file not found`

The path passed to `compare`/`check`/`load_schema_file()` doesn't exist,
or is relative to a different working directory than you expect (CI
runners often start in the repository root — double check the path is
relative to *that*, not to `docs/` or wherever the command is defined).

## The diff shows changes I didn't make

You're likely comparing against a stale baseline, or drf-spectacular is
generating a schema you don't expect (e.g. it picked up
`SPECTACULAR_SETTINGS` you forgot were set, or a `urlconf` different
from the one you intended). Run `drf-contract-test snapshot` again and
diff the two YAML files by eye to isolate what actually changed.

## Every field shows up as `field_added`/`field_removed` even though I barely touched anything

This almost always means the two schemas' `$ref` targets don't line up —
e.g. you regenerated component schema names (drf-spectacular derives
them from serializer class names; renaming a serializer renames its
component). This isn't a bug in the comparison — the two schemas
genuinely no longer share the referenced component, so every property
inside it reads as entirely new. Avoid renaming serializers between
baseline snapshots, or accept the noise as expected fallout of the
rename.

## `contract_baseline`/`contract_diff`/`contract_version_check` tests are always skipped

You didn't pass `--contract-baseline=PATH` to pytest. This is
intentional (see [FAQ](faq.md)) — pass the flag, or check your pytest
invocation (a `pytest.ini`/`pyproject.toml` `addopts` typo is a common
cause of a flag silently not applying).

## `jsonschema` reports a violation I don't understand

`validate_response_against_schema()`'s violation messages come directly
from `jsonschema`'s `ValidationError.message`, prefixed with the JSON
pointer path (`error.absolute_path`) into the response body where the
mismatch occurred. Read the path first — it tells you exactly which
field or array index failed, before you interpret the message.

## mkdocs build warns about cross-reference targets

If you're building custom documentation on top of this package's
docstrings with mkdocstrings, avoid writing raw dict-literal syntax
(`{"key": "value"}`) inside prose docstring text — griffe's Markdown
post-processing can misinterpret bracket content as a reference link.
Wrap such examples in a fenced code block instead.

## Still stuck?

Open a [GitHub Discussion](https://github.com/mahmoudgshaker/drf-contract-test/discussions)
with your schema snippet (redact anything sensitive) and the exact
command you ran.

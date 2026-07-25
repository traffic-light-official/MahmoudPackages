# Security

## This package writes schema-derived text into Python source files - a real injection surface, taken seriously

Unlike a tool that only *reads* untrusted data, a code generator writes
schema-derived strings (path segments, `$ref` targets, `operationId`
values) directly into files that Python will later execute. A schema
containing a crafted value - say, a path segment with an embedded
newline and a fake comment marker - could otherwise break out of a
string literal, a `#` comment, or a docstring and inject arbitrary code
into the generated file. This package defends against that at every
interpolation site:

- Anything that becomes a Python **identifier** (a class name, a field
  name, a method name) goes through `naming.to_class_name` or
  `naming.to_snake_case`, both of which strip everything but
  alphanumeric characters before re-joining - there is no way for
  schema text to produce anything other than a valid identifier.
- Anything that becomes a Python **string literal** (an `@action`'s
  `url_path=`, a router's registration prefix/basename, a
  `NotImplementedError` message) is passed through `repr()`, never
  hand-quoted with an f-string - `repr()` correctly escapes quotes,
  backslashes, and newlines for any input.
- Anything that becomes a `#` **comment** (an "unsupported operation"
  note, a circular-reference note) is passed through
  `naming.comment_safe`, which collapses embedded newlines to spaces -
  otherwise a newline inside schema text would end the comment early
  and let the rest of the crafted value become a new, uncommented
  source line.

See [Architecture](architecture.md#schema-derived-text-is-never-interpolated-unescaped-into-generated-source)
for where each of these is applied, and the test suite's
`test_unsupported_path_comment_is_newline_safe` and
`test_prefix_with_a_quote_character_is_safely_escaped` for the specific
attack shapes this was verified against.

## Only run `scaffold`/`check` against a contract you trust

The defenses above prevent a malicious schema from achieving code
injection through this package's own generation logic, but the
generated *field definitions themselves* are only as trustworthy as
their source - a schema is still, ultimately, becoming part of your
application's source code. Treat an OpenAPI contract the same as any
other input to your build: reviewed and version-controlled, not fetched
from an untrusted or unauthenticated source at scaffold time.

## No secrets, no network access, no database

`scaffold()`/`check_drift()` read a schema and read/write local files -
nothing else. There is no outbound network call, no subprocess
invocation, and no database access anywhere in this package's execution
path (contrast with the sibling `drf-changelog-generator`, which shells
out to `git show`).

## Dependency posture

This package's runtime dependencies are `PyYAML` (schema parsing),
Django, and Django REST Framework (for the optional management
command). All are widely used, actively maintained projects pinned to
minimum versions in `pyproject.toml` and kept current via Dependabot
(see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-reverse/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.

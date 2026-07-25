# Security

## `MAX_BATCH_SIZE` is your primary defense against resource-exhaustion abuse

Without a cap, a single malicious or buggy client request can submit an
arbitrarily large list, holding a database transaction open (atomic
mode) or running an arbitrarily long series of saves (non-atomic mode)
for as long as the whole batch takes to process - a straightforward
denial-of-service vector against a public-facing bulk endpoint. Set
`MAX_BATCH_SIZE` to the largest value your legitimate use case actually
needs, not the framework default - see [Configuration](configuration.md).

## Permission and authentication semantics are unchanged

Every bulk action goes through the exact same `permission_classes`/
`authentication_classes` your viewset already configures -
`bulk_update`/`bulk_partial_update`/`bulk_destroy` additionally call
`check_object_permissions()` per resolved instance, exactly like DRF's
own single-object `update`/`destroy`. This package changes nothing
about who is authorized to do what; it only changes how many objects
one authorized request can affect.

## A single bulk request can affect many objects at once

This is the actual security-relevant difference from a single-object
endpoint: a bug in `permission_classes` (e.g. an object-level
permission that's supposed to restrict access per-tenant but doesn't)
that would leak or corrupt one row via a single-object endpoint can
leak or corrupt an entire batch via a bulk one. Test object-level
permission enforcement specifically against the bulk endpoints, not
just the single-object ones - `docs/testing.md` shows the pattern this
package's own test suite uses.

## `ObjectNotFoundError`/`MissingLookupFieldError` messages name the lookup value

Error responses for a missing/invalid ID in `bulk_update`/
`bulk_partial_update`/`bulk_destroy` echo back the submitted ID value
(`"No object found with id=42."`). This is the same information a
single-object `404` already reveals (whether a given ID exists at all)
- if your project treats object existence itself as sensitive (e.g. ID
enumeration against another tenant's private data), that's a concern
for your `get_queryset()` filtering (returning a queryset scoped to the
current tenant/user, so a foreign ID is genuinely "not found" rather
than a permission failure), not something specific to bulk operations.

## No user input reaches a file path, subprocess call, or dynamic code execution

Every value this package's code touches (item dicts, lookup field
values, item counts) is only ever compared, used as a queryset filter
value (via Django's parameterized ORM, never raw SQL), or passed to a
DRF serializer - never interpolated into a file path, shell command, or
`eval`/`exec`.

## Dependency posture

This package's only runtime dependencies are Django and Django REST
Framework themselves - no third-party parsing or networking library.
Both are pinned to minimum versions in `pyproject.toml` and kept
current via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-bulk-operations/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.

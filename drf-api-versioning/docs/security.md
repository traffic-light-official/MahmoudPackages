# Security

## `ALLOW_SUNSET = True` is a deliberate, visible override - keep it that way

Setting `ALLOW_SUNSET = True` disables the one enforcement mechanism
this package provides for actually retiring a version - a sunset
version continues serving real traffic indefinitely, with only response
headers as a signal. This is a legitimate staged-rollout tool (see
[Common Patterns](common-patterns.md#staging-a-sunset-date-before-enforcing-it)),
but treat it as a temporary, tracked state (a code comment with a
target removal date, a linked ticket) rather than a permanent
configuration - a forgotten `ALLOW_SUNSET = True` silently defeats the
entire point of declaring a sunset date.

## Version metadata is not a secrets boundary

`API_VERSIONING["VERSIONS"]` (deprecation dates, migration links) is
returned in response headers and the `list_api_versions` management
command output - treat it as public information, since it effectively
already is the moment any client receives a `Deprecation`/`Sunset`
header. Do not put anything sensitive in `deprecation_link` beyond a
public documentation URL.

## Error messages name every declared version

`UnknownAPIVersionError`'s message includes the full list of currently
supported versions (`registry.all_version_names()`). This is
intentional - an API consumer benefits from knowing what's actually
available - but means the set of valid versions is discoverable from a
single failed request, same as it already is from
`list_api_versions`/your own API documentation. This package does not
treat "which versions exist" as sensitive information; if your project
does, catch `UnknownAPIVersionError` yourself and return a generic
message instead.

## No user input reaches Django settings, file paths, or subprocess calls

Every value this package reads comes from `API_VERSIONING`, a
Django settings value under your own control - request data (the
resolved version string, `Accept` header, hostname, query parameter) is
only ever used as a dict lookup key against the registry or compared
against known dates, never interpolated into a file path, a subprocess
command, or written back into settings.

## Dependency posture

This package's only runtime dependencies are Django and Django REST
Framework themselves - no third-party parsing library. Both are pinned
to minimum versions in `pyproject.toml` and kept current via Dependabot
(see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-api-versioning/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.

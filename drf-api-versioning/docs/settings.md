# Settings

All configuration lives under a single Django setting,
`API_VERSIONING`, a dict of overrides merged on top of the defaults
below.

```python
# settings.py
import datetime

API_VERSIONING = {
    "VERSIONS": {
        "v1": {
            "deprecated": datetime.date(2026, 1, 1),
            "sunset": datetime.date(2026, 7, 1),
            "deprecation_link": "https://example.com/docs/migrating-to-v2",
        },
        "v2": {},
    },
    "DEFAULT_VERSION": "v2",
}
```

## `VERSIONS`

- **Type:** `dict[str, dict]`
- **Default:** `{}` (but must declare at least one version - see
  [Installation](installation.md#declaring-at-least-one-version-is-required))

A mapping of version name to its metadata dict. Each entry accepts:

- `"deprecated"` (`datetime.date`, optional): the date this version
  became/becomes deprecated.
- `"sunset"` (`datetime.date`, optional): the date this version
  stops being served (unless `ALLOW_SUNSET` is `True`). Cannot be
  earlier than `"deprecated"` if both are set.
- `"deprecation_link"` (`str`, optional): a migration-docs URL, used in
  the `Link` response header.

A version with an empty dict (or omitted keys) is fully supported - not
deprecated, no sunset date.

## `DEFAULT_VERSION`

- **Type:** `str | None`
- **Default:** `None`
- **Must be:** a key in `VERSIONS`, or `None`

The version used when a request doesn't specify one (passed through to
the wrapped DRF scheme's own `default_version`).

## `ALLOW_SUNSET`

- **Type:** `bool`
- **Default:** `False`

When `False`, a request resolving to a version past its `sunset` date
is rejected with `APIVersionSunsetError` (410). When `True`, sunset
versions are still served normally (headers are still added).

## `DEPRECATION_HEADER`

- **Type:** `str`
- **Default:** `"Deprecation"`

Response header name used to signal deprecation.

## `SUNSET_HEADER`

- **Type:** `str`
- **Default:** `"Sunset"`

Response header name used to signal the sunset date (RFC 8594).

## `LINK_HEADER`

- **Type:** `str`
- **Default:** `"Link"`

Response header name used for the migration-docs link, when a version
defines `deprecation_link`.

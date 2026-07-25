# Common Patterns

## Staging a sunset date before enforcing it

Deploy the sunset date with `ALLOW_SUNSET = True` first, so
`list_api_versions` and the `Sunset` response header both reflect it
immediately, without breaking any client still relying on the version:

```python
API_VERSIONING = {
    "VERSIONS": {"v1": {"sunset": datetime.date(2026, 9, 1)}},
    "ALLOW_SUNSET": True,  # advance warning only, not yet enforced
}
```

Once monitoring (via the `deprecated_version_used` signal, or your own
access logs) confirms traffic has actually stopped, flip to
`ALLOW_SUNSET = False` (or remove the override, since that's the
default) to start rejecting requests.

## Gating a CI job on a version that's already past its sunset date

Useful as a reminder to actually remove a version's code/routes once
its grace period has genuinely ended, rather than leaving
`ALLOW_SUNSET = True` (or the entry itself) in place indefinitely:

```python
# a plain script run in CI
import sys

from drf_api_versioning import all_versions

overdue = [v.name for v in all_versions() if v.is_sunset()]
if overdue:
    print(f"Sunset versions still declared: {overdue}. Remove them or their routes.")
    sys.exit(1)
```

Pair with `python manage.py list_api_versions --status sunset` for a
quick manual check before cutting a release.

## Recording per-client deprecated-version usage

```python
from drf_api_versioning.signals import deprecated_version_used


def record_usage(sender, *, request, version, version_info, **kwargs):
    client_id = request.headers.get("X-Client-Id", "unknown")
    logger.info(
        "deprecated_api_version_used",
        extra={"version": version, "client_id": client_id, "path": request.path},
    )


deprecated_version_used.connect(record_usage)
```

Feed the resulting log stream into whatever aggregation you already use
(structured logging, an APM) - this package intentionally doesn't
bundle a usage-tracking model or dashboard (see
[FAQ](faq.md#why-doesnt-this-package-ship-a-usage-tracking-model)).

## Announcing deprecation in a release without touching enforcement

Add `"deprecated"` to a version's entry in the same release you
announce it in release notes, without adding `"sunset"` yet - clients
start seeing the `Deprecation` header (a machine-readable signal
alongside your human-readable release notes) with no behavior change
otherwise:

```python
API_VERSIONING = {
    "VERSIONS": {
        "v1": {
            "deprecated": datetime.date.today(),
            "deprecation_link": "https://example.com/docs/migrating-to-v2",
        },
        "v2": {},
    },
}
```

Add `"sunset"` in a later release once you've decided on an actual
cutoff date.

## Testing that a specific deprecated endpoint still works correctly

Deprecation is a signal, not a behavior change - assert the endpoint's
actual response is unaffected, alongside the header:

```python
def test_deprecated_v1_endpoint_still_works(api_client):
    response = api_client.get("/v1/articles/")
    assert response.status_code == 200
    assert response["Deprecation"]
    assert response.data == expected_v1_shaped_data
```

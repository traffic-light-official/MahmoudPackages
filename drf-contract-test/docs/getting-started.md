# Getting Started

## Install

```bash
pip install drf-contract-test
```

This installs the `drf-contract-test` CLI, the pytest plugin (auto-registered),
and the Python API. Django, DRF, and drf-spectacular are hard
dependencies — you need a working drf-spectacular schema setup already
(if `python manage.py spectacular` works, you're ready).

## The core workflow

1. **Snapshot** your current API as a baseline, and commit it to your
   repository:

   ```bash
   drf-contract-test snapshot openapi-baseline.yaml --settings myproject.settings
   ```

2. Keep working on your API as normal.

3. **Compare** your current API against that baseline, any time — locally
   or in CI:

   ```bash
   drf-contract-test compare openapi-baseline.yaml --settings myproject.settings
   ```

   This prints every detected change with its severity and exits `1` if
   any change is breaking.

4. When you intentionally ship a breaking change, use **check** instead
   of compare in CI — it additionally requires your API version to have
   been bumped:

   ```bash
   drf-contract-test check openapi-baseline.yaml --settings myproject.settings
   ```

   If this passes, update your baseline (repeat step 1) so the new shape
   becomes the reference point for the next comparison.

## Your first comparison

Given a baseline where a `title` field was optional and is now required:

```
BREAKING POST /articles/ - request.properties.title: is now required (was optional)

1 breaking change(s), 0 safe change(s).
```

That's the signal: an existing client that used to omit `title` will now
get a `400` it didn't get before. See [Architecture](architecture.md) for
why this is breaking for a request but would be safe for a response.

## Next steps

- [Quick Start](quickstart.md) for CI wiring.
- [Configuration](configuration.md) for CLI/pytest-plugin options.
- [Testing](testing.md) for using the pytest plugin and contract-test
  generation directly in your own test suite.

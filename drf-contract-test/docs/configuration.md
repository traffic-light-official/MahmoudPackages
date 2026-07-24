# Configuration

`drf-contract-test` has no settings dictionary of its own (it isn't a
Django app you add to `INSTALLED_APPS`) — it's a schema-generation and
comparison tool that needs to know how to reach your Django project.
There are two things to configure: **how to find your Django settings**,
and **how to generate the live schema**.

## Pointing at your Django project

Every command that needs a live schema (`snapshot`, and `compare`/`check`
when no `current` file is given) accepts:

- `--settings <dotted.path>` — sets `DJANGO_SETTINGS_MODULE` (via
  `os.environ.setdefault`, so an already-set environment variable takes
  precedence) and calls `django.setup()` if the app registry isn't ready
  yet.
- `--urlconf <dotted.path>` — passed to drf-spectacular's
  `SchemaGenerator(urlconf=...)`. Defaults to your settings' `ROOT_URLCONF`.

If Django is already configured in your process — e.g. you're calling
`generate_schema()` from inside a Django management command, or running
under `pytest-django` — omit `--settings` entirely; the existing
configuration is used as-is.

```bash
drf-contract-test snapshot openapi-baseline.yaml \
  --settings myproject.settings \
  --urlconf myproject.urls
```

## Environment variable fallback

`--settings` only sets `DJANGO_SETTINGS_MODULE` if it isn't already set.
This means you can omit `--settings` entirely and rely on the
environment instead, which is often more convenient in CI:

```bash
export DJANGO_SETTINGS_MODULE=myproject.settings
drf-contract-test check openapi-baseline.yaml
```

## drf-spectacular configuration

Schema generation delegates entirely to drf-spectacular's
`SchemaGenerator`. Any `SPECTACULAR_SETTINGS` you've already configured
(schema title/version, component splitting, authentication schemes,
etc.) apply automatically — `drf-contract-test` does not duplicate or
override drf-spectacular's own configuration surface.

## What to configure per environment

| Environment | Typical setup |
|---|---|
| Local development | `--settings` flag, ad hoc `compare` runs |
| CI | `DJANGO_SETTINGS_MODULE` env var + a committed baseline file |
| pytest suite | rely on `pytest-django`'s existing configuration; use `--contract-settings`/`--contract-urlconf` only if you need to point at a different settings module than the one pytest-django already configured |

See [Settings](settings.md) for the full flag/option reference.

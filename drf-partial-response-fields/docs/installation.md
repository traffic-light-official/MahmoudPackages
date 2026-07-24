# Installation

## Requirements

| Dependency | Supported versions |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |

## Standard install

```bash
pip install drf-partial-response-fields
```

## With OpenAPI schema support

If you use [drf-spectacular](https://drf-spectacular.readthedocs.io/) and
want the `fields` query parameter documented automatically, install the
`openapi` extra:

```bash
pip install drf-partial-response-fields[openapi]
```

Nothing else in the package requires `drf-spectacular` — only
`drf_partial_response_fields.openapi` imports it, and only when you import
that module yourself. See [`docs/api-reference.md`](api-reference.md#openapi-drf-spectacular)
for what this unlocks.

## Verifying the install

```bash
python -c "import drf_partial_response_fields; print(drf_partial_response_fields.__version__)"
```

## Django project setup

No entry in `INSTALLED_APPS` is required. This package ships no models, no
migrations, and no Django app config — it is a set of serializer and view
mixins plus a couple of pure-Python helper modules.

If you plan to use the `STRICT`, `QUERY_PARAM`, or other project-wide
settings, see [Configuration](configuration.md).

## Using with Poetry / PDM / uv

Any standard PEP 517/518 installer works, since the package is published as
a normal wheel and sdist:

```bash
poetry add drf-partial-response-fields
# or
pdm add drf-partial-response-fields
# or
uv add drf-partial-response-fields
```

## Upgrading

Check [CHANGELOG.md](https://github.com/mahmoudgshaker/drf-partial-response-fields/blob/main/CHANGELOG.md)
before upgrading across a major version — this package follows
[Semantic Versioning](https://semver.org/), so any breaking change to a
public class, function, or setting bumps the major version and is
accompanied by a migration note.

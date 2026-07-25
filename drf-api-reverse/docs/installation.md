# Installation

```bash
pip install drf-api-reverse
```

Requires Python 3.10+. Django and Django REST Framework are declared
dependencies (for the optional `scaffold_api` management command and to
match the rest of this project's support matrix), but the CLI and
library work standalone - no Django project required to run `scaffold`
or `check`.

## Optional extras

```bash
pip install "drf-api-reverse[spectacular]"
```

Only needed if you plan to generate the "new" side of a diff from a
live Django project's own schema (e.g. in a custom script combining
this package with `drf-spectacular`) - the shipped `scaffold_api`
management command itself does not require `drf-spectacular`, since it
always takes an explicit `--schema` file, not a live introspected one.

## Django project setup

Only required if you want the `scaffold_api` management command
(optional - the standalone CLI needs no Django project at all):

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_api_reverse",
]
```

No migrations to run - this package defines no models.

## Verifying the install

```bash
drf-api-reverse --help
```

```
usage: drf-api-reverse [-h] {scaffold,check} ...
```

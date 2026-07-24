"""Loading and generating OpenAPI schemas.

A schema can come from two places: a static snapshot file (YAML or JSON —
typically a baseline you've committed to your repository) via
:func:`load_schema_file`, or a live Django project via :func:`generate_schema`
(using `drf-spectacular <https://drf-spectacular.readthedocs.io/>`_'s
schema generator).
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import django
import yaml

from drf_contract_test.exceptions import SchemaGenerationError, SchemaLoadError

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options", "trace"})


class Schema:
    """A thin, read-only wrapper around a parsed OpenAPI document.

    Args:
        raw: The parsed OpenAPI document (from JSON or YAML).
    """

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw

    @property
    def version(self) -> str:
        """The document's ``info.version`` string, or ``""`` if absent."""
        return str(self.raw.get("info", {}).get("version", ""))

    @property
    def title(self) -> str:
        """The document's ``info.title`` string, or ``""`` if absent."""
        return str(self.raw.get("info", {}).get("title", ""))

    def operations(self) -> Iterator[tuple[str, str, dict[str, Any]]]:
        """Iterate over every operation in the document.

        Yields:
            ``(method, path, operation_object)`` tuples, where ``method``
            is uppercase (e.g. ``"GET"``) and ``operation_object`` is the
            raw OpenAPI Operation Object.
        """
        paths = self.raw.get("paths") or {}
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if method.lower() in _HTTP_METHODS and isinstance(operation, dict):
                    yield method.upper(), path, operation

    def get_operation(self, method: str, path: str) -> dict[str, Any] | None:
        """Look up a single operation by method and path.

        Args:
            method: The HTTP method, case-insensitive.
            path: The exact path template (e.g. ``"/articles/{id}/"``).

        Returns:
            The raw OpenAPI Operation Object, or ``None`` if not found.
        """
        path_item = (self.raw.get("paths") or {}).get(path)
        if not isinstance(path_item, dict):
            return None
        operation = path_item.get(method.lower())
        return operation if isinstance(operation, dict) else None


def load_schema_file(path: str | Path) -> Schema:
    """Load a schema snapshot from a YAML or JSON file.

    Args:
        path: Path to the schema file. The format is inferred from the
            extension (``.json`` for JSON; anything else is parsed as
            YAML, which is also valid for JSON content).

    Returns:
        The parsed :class:`Schema`.

    Raises:
        drf_contract_test.exceptions.SchemaLoadError: If the file doesn't
            exist or can't be parsed.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise SchemaLoadError(f"Schema file not found: {file_path}")
    text = file_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text) if file_path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SchemaLoadError(f"Could not parse schema file {file_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaLoadError(f"Schema file {file_path} did not contain a JSON/YAML object.")
    return Schema(data)


def dump_schema_file(schema: Schema, path: str | Path) -> None:
    """Write a schema to a YAML or JSON file.

    Args:
        schema: The schema to write.
        path: Destination path. Written as JSON if the extension is
            ``.json``, otherwise as YAML.
    """
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        file_path.write_text(json.dumps(schema.raw, indent=2, sort_keys=False), encoding="utf-8")
    else:
        file_path.write_text(
            yaml.safe_dump(schema.raw, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )


def generate_schema(*, settings_module: str | None = None, urlconf: str | None = None) -> Schema:
    """Generate a schema from a live Django project via drf-spectacular.

    Args:
        settings_module: Dotted path to a Django settings module. If
            given, sets ``DJANGO_SETTINGS_MODULE`` before calling
            ``django.setup()``. If omitted, assumes Django is already
            configured (e.g. this is called from within a Django
            management command or a test already using ``pytest-django``).
        urlconf: Dotted path to a URLconf module to generate the schema
            from. Defaults to ``ROOT_URLCONF``.

    Returns:
        The generated :class:`Schema`.

    Raises:
        drf_contract_test.exceptions.SchemaGenerationError: If Django
            cannot be initialized (e.g. an invalid settings module).
    """
    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    if not django.apps.apps.ready:
        try:
            django.setup()
        except Exception as exc:  # pragma: no cover - defensive, environment-dependent
            raise SchemaGenerationError(f"Could not initialize Django: {exc}") from exc

    # Deferred deliberately: drf-spectacular's generator module reaches into
    # the app registry and DRF settings on import, so it must not be
    # imported until *after* django.setup() has run above.
    from drf_spectacular.generators import SchemaGenerator  # noqa: PLC0415

    # drf-spectacular ships py.typed but leaves these two signatures
    # unannotated (*args/**kwargs and bare params), so mypy still sees
    # them as untyped calls even in a typed context.
    generator = SchemaGenerator(urlconf=urlconf)  # type: ignore[no-untyped-call]
    raw = generator.get_schema(request=None, public=True)  # type: ignore[no-untyped-call]
    return Schema(raw)

"""Orchestrates generating (or idempotently regenerating) an app's files."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from drf_api_reverse.codegen import serializers as serializers_codegen
from drf_api_reverse.codegen import urls as urls_codegen
from drf_api_reverse.codegen import views as views_codegen
from drf_api_reverse.regions import merge

_RegionsFn = Callable[[dict[str, Any]], dict[str, str]]
_RenderFn = Callable[[dict[str, Any]], str]

GENERATORS: tuple[tuple[str, _RegionsFn, _RenderFn], ...] = (
    (
        "serializers.py",
        serializers_codegen.generate_serializer_regions,
        serializers_codegen.render_file,
    ),
    ("views.py", views_codegen.generate_viewset_regions, views_codegen.render_file),
    ("urls.py", urls_codegen.generate_url_regions, urls_codegen.render_file),
)


@dataclass(frozen=True, slots=True)
class FileResult:
    """The outcome of scaffolding a single file."""

    filename: str
    created: bool
    orphaned_keys: list[str] = field(default_factory=list)


def scaffold(schema: dict[str, Any], output_dir: str | Path) -> list[FileResult]:
    """Generate/regenerate ``serializers.py``, ``views.py``, and ``urls.py``.

    Args:
        schema: The full parsed OpenAPI document.
        output_dir: The Django app directory to write into. Created if
            it does not already exist.

    Returns:
        One :class:`FileResult` per generated file, in the order
        ``serializers.py``, ``views.py``, ``urls.py`` (this order
        matters if you're reading the diff by hand: ``views.py``
        imports from ``serializers.py``, and ``urls.py`` imports from
        ``views.py``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[FileResult] = []
    for filename, generate_regions, render_file in GENERATORS:
        target = output_dir / filename

        if target.exists():
            new_text, orphaned = merge(target.read_text(encoding="utf-8"), generate_regions(schema))
            created = False
        else:
            new_text = render_file(schema)
            orphaned = []
            created = True

        target.write_text(new_text, encoding="utf-8")
        results.append(FileResult(filename=filename, created=created, orphaned_keys=orphaned))

    return results

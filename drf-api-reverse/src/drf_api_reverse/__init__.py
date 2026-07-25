"""Design-first DRF scaffolding: generate code from an OpenAPI contract.

The public API is intentionally small. Most projects only need the
``drf-api-reverse`` console script (see ``docs/quickstart.md``), but the
underlying pieces are all importable directly:

* :func:`~drf_api_reverse.scaffolder.scaffold` - generate/regenerate
  ``serializers.py``/``views.py``/``urls.py`` from a schema, merging
  idempotently with any existing files.
* :func:`~drf_api_reverse.checker.check_drift` - compare on-disk
  generated code against what the schema would produce right now.
* :mod:`~drf_api_reverse.codegen` - the individual file generators, if
  you only need one of the three.
"""

from __future__ import annotations

from drf_api_reverse.checker import FileDrift, check_drift, raise_if_drifted
from drf_api_reverse.exceptions import (
    ApiReverseError,
    DriftDetectedError,
    RegionMergeError,
    SchemaParseError,
)
from drf_api_reverse.scaffolder import FileResult, scaffold
from drf_api_reverse.schema_loader import load_schema_file, parse_schema

__version__ = "1.0.0"

__all__ = [
    "ApiReverseError",
    "DriftDetectedError",
    "FileDrift",
    "FileResult",
    "RegionMergeError",
    "SchemaParseError",
    "__version__",
    "check_drift",
    "load_schema_file",
    "parse_schema",
    "raise_if_drifted",
    "scaffold",
]

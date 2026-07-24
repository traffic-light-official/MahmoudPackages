"""Contract testing for Django REST Framework APIs.

Detects breaking changes between OpenAPI schema snapshots, applying
direction-aware rules (a change safe in a request schema may be breaking
in a response schema, and vice versa — see
:mod:`drf_contract_test.rules`), and can enforce that breaking changes
are accompanied by a version bump.

Typical usage::

    from drf_contract_test import compare_schemas, load_schema_file, generate_schema

    baseline = load_schema_file("openapi-baseline.yaml")
    current = generate_schema(settings_module="myproject.settings")
    diff = compare_schemas(baseline, current)
    if diff.has_breaking_changes:
        raise SystemExit("Breaking API changes detected!")
"""

from __future__ import annotations

from drf_contract_test.changes import Change, DiffResult, Severity
from drf_contract_test.diff import compare_schemas
from drf_contract_test.exceptions import ContractTestError, SchemaGenerationError, SchemaLoadError
from drf_contract_test.generator import (
    ContractCase,
    generate_contract_cases,
    validate_response_against_schema,
)
from drf_contract_test.rules import Direction, compare_schema_objects
from drf_contract_test.schema import Schema, dump_schema_file, generate_schema, load_schema_file
from drf_contract_test.versioning import VersionCheckResult, check_version_bump

__version__ = "1.0.0"

__all__ = [
    "Change",
    "ContractCase",
    "ContractTestError",
    "DiffResult",
    "Direction",
    "Schema",
    "SchemaGenerationError",
    "SchemaLoadError",
    "Severity",
    "VersionCheckResult",
    "__version__",
    "check_version_bump",
    "compare_schema_objects",
    "compare_schemas",
    "dump_schema_file",
    "generate_contract_cases",
    "generate_schema",
    "load_schema_file",
    "validate_response_against_schema",
]

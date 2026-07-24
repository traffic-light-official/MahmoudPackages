"""Custom exceptions raised by :mod:`drf_contract_test`.

Everything in this package runs as a developer tool (a CLI, a pytest
plugin) rather than inside a live request/response cycle, so these are
plain Python exceptions — there is no HTTP response to shape.
"""

from __future__ import annotations


class ContractTestError(Exception):
    """Base class for all errors raised by this package."""


class SchemaLoadError(ContractTestError):
    """Raised when an OpenAPI schema cannot be loaded or parsed.

    Args:
        message: A human-readable description of what went wrong.
    """


class SchemaGenerationError(ContractTestError):
    """Raised when a live schema cannot be generated from a Django project.

    Args:
        message: A human-readable description of what went wrong.
    """


class InvalidVersionError(ContractTestError):
    """Raised when an OpenAPI ``info.version`` string cannot be interpreted
    for version-bump comparison purposes.

    Args:
        message: A human-readable description of what went wrong.
    """

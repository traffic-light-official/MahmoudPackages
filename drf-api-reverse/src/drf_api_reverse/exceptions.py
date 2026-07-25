"""Exceptions raised by :mod:`drf_api_reverse`."""

from __future__ import annotations


class ApiReverseError(Exception):
    """Base class for every exception raised by this package."""


class SchemaParseError(ApiReverseError):
    """Raised when a schema document cannot be parsed as JSON or YAML."""


class RegionMergeError(ApiReverseError):
    """Raised when an existing generated file cannot be safely merged.

    For example, a ``BEGIN`` marker with no matching ``END`` marker, or
    two regions sharing the same key.
    """


class DriftDetectedError(ApiReverseError):
    """Raised by :func:`drf_api_reverse.checker.check_drift` in raise mode.

    Indicates that a generated region on disk no longer matches what the
    current schema would generate.
    """

"""Exceptions raised by :mod:`drf_changelog_generator`."""

from __future__ import annotations


class ChangelogGeneratorError(Exception):
    """Base class for every exception raised by this package."""


class SchemaParseError(ChangelogGeneratorError):
    """Raised when a schema document cannot be parsed as JSON or YAML."""


class GitError(ChangelogGeneratorError):
    """Raised when a ``git`` subprocess invocation fails."""

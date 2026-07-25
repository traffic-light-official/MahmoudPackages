"""Reads a file's content as it existed at a specific Git ref.

Uses ``git show <ref>:<path>`` rather than checking out the ref, so the
working tree is never disturbed - this only works if the schema file is
committed to the repository at that ref (the common pattern of committing
a generated ``openapi-schema.yml`` on each release).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from drf_changelog_generator.exceptions import GitError
from drf_changelog_generator.schema_loader import parse_schema


def show_file_at_ref(*, repo: str | Path, ref: str, file_path: str) -> str:
    """Return the content of ``file_path`` as it existed at ``ref``.

    Args:
        repo: Path to the Git repository (working directory for the
            ``git`` invocation).
        ref: Any Git ref: a tag, branch, or commit SHA.
        file_path: Path to the file, relative to the repository root.

    Returns:
        The file's raw text content at that ref.

    Raises:
        GitError: If ``git`` is not installed, ``repo`` is not a Git
            repository, ``ref`` does not exist, or ``file_path`` does
            not exist at ``ref``.
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError("The 'git' executable was not found on PATH.") from exc

    if result.returncode != 0:
        raise GitError(f"'git show {ref}:{file_path}' failed in {repo}: {result.stderr.strip()}")
    return result.stdout


def load_schema_at_ref(*, repo: str | Path, ref: str, file_path: str) -> dict[str, Any]:
    """Load and parse an OpenAPI schema as it existed at a specific Git ref.

    Args:
        repo: Path to the Git repository.
        ref: Any Git ref: a tag, branch, or commit SHA.
        file_path: Path to the schema file, relative to the repository root.

    Returns:
        The parsed schema as a plain dict.

    Raises:
        GitError: See :func:`show_file_at_ref`.
        SchemaParseError: If the file's content cannot be parsed as
            JSON or YAML.
    """
    text = show_file_at_ref(repo=repo, ref=ref, file_path=file_path)
    return parse_schema(text, suffix=Path(file_path).suffix)

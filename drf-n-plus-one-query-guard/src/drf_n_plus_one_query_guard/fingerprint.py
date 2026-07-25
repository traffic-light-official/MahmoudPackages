"""Normalizes SQL text into a fingerprint for repeated-query detection.

Django's ORM always executes parameterized queries - the ``sql`` string
a database backend receives already has placeholders (``%s``, ``?``, or
``%(name)s`` depending on the backend) in place of literal values, with
the actual values passed separately as ``params``. This means two
executions of the same N+1-shaped query (e.g. once per row of an
un-prefetched loop, each with a different foreign key value) already
produce byte-identical ``sql`` text - there is no need to strip literal
numbers or quoted strings out of it, only to normalize incidental
whitespace differences.
"""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_sql(sql: str) -> str:
    """Collapse incidental whitespace so equivalent queries fingerprint alike.

    Args:
        sql: The raw SQL text as passed to the database driver (already
            parameterized by Django's ORM - see the module docstring).

    Returns:
        The same SQL with all runs of whitespace collapsed to a single
        space and leading/trailing whitespace stripped.
    """
    return _WHITESPACE_RE.sub(" ", sql).strip()

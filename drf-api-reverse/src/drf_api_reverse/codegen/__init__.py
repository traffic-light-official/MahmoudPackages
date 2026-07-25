"""Code generators: turn a parsed OpenAPI document into DRF source text.

Each submodule generates one file's worth of source
(``serializers.py``, ``views.py``, ``urls.py``) as a plain string, given
the schema and nothing else - none of them touch the filesystem
directly. See :mod:`drf_api_reverse.scaffolder` for the orchestration
that writes (and idempotently merges) the result to disk.
"""

from __future__ import annotations

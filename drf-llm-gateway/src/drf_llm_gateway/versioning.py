"""Content-hash based schema versioning.

Every :class:`~drf_llm_gateway.registry.ToolDefinition` exposes a
``schema_hash`` computed from its generated JSON Schema. Two generations of
the same tool produce the same hash if and only if the schema (field
names, types, required-ness) is unchanged — giving consumers a cheap way
to detect drift without diffing full schemas.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_schema_hash(schema: dict[str, Any]) -> str:
    """Compute a stable, deterministic hash of a JSON Schema.

    Args:
        schema: A JSON-Schema-compatible ``dict``, as produced by
            :func:`drf_llm_gateway.schema.serializer_to_json_schema` or
            :meth:`drf_llm_gateway.registry.ToolDefinition.input_json_schema`.

    Returns:
        A 16-character hexadecimal digest prefix. Dict key order does not
        affect the result (``json.dumps(..., sort_keys=True)`` is used
        before hashing), so semantically identical schemas always hash
        identically.

    Example:
        >>> compute_schema_hash({"type": "object", "properties": {}})
        '...'  # doctest: +SKIP
    """
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:16]

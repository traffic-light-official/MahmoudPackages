"""Idempotent merging of generated code into a file that may already exist.

Every generated file is split into named regions, each wrapped in a
pair of marker comments:

```
# === BEGIN DRF-API-REVERSE GENERATED: serializer:Article ===
class ArticleSerializer(serializers.Serializer):
    ...
# === END DRF-API-REVERSE GENERATED: serializer:Article ===
```

Re-running ``scaffold`` replaces only the text between a region's own
markers, leaving everything else in the file - including hand-written
code between, before, or after regions - untouched. This is what makes
regeneration safe to run repeatedly as a design-first contract evolves,
instead of a one-shot generator you can only safely run once.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from drf_api_reverse.exceptions import RegionMergeError

_BEGIN_RE = re.compile(r"^# === BEGIN DRF-API-REVERSE GENERATED: (?P<key>.+?) ===\s*$")
_END_RE = re.compile(r"^# === END DRF-API-REVERSE GENERATED: (?P<key>.+?) ===\s*$")


def begin_marker(key: str) -> str:
    """Return the ``BEGIN`` marker comment line for a region key."""
    return f"# === BEGIN DRF-API-REVERSE GENERATED: {key} ==="


def end_marker(key: str) -> str:
    """Return the ``END`` marker comment line for a region key."""
    return f"# === END DRF-API-REVERSE GENERATED: {key} ==="


@dataclass(frozen=True, slots=True)
class _Chunk:
    is_region: bool
    key: str | None
    text: str


def parse_regions(text: str) -> list[_Chunk]:
    """Split ``text`` into literal and generated-region chunks.

    Exposed (beyond :func:`merge`/:func:`existing_region_keys`) so
    callers like :mod:`drf_api_reverse.checker` can inspect existing
    region bodies directly without re-implementing marker parsing.

    Raises:
        RegionMergeError: If ``text`` has malformed or duplicate markers.
    """
    lines = text.splitlines()
    chunks: list[_Chunk] = []
    literal_buf: list[str] = []
    seen_keys: set[str] = set()
    i = 0

    def flush_literal() -> None:
        if literal_buf:
            chunks.append(_Chunk(False, None, "\n".join(literal_buf)))
            literal_buf.clear()

    while i < len(lines):
        begin_match = _BEGIN_RE.match(lines[i])
        if begin_match is None:
            literal_buf.append(lines[i])
            i += 1
            continue

        key = begin_match.group("key")
        if key in seen_keys:
            raise RegionMergeError(f"Duplicate generated region key {key!r} in existing file.")
        flush_literal()
        i += 1
        body: list[str] = []
        end_key: str | None = None
        while i < len(lines):
            end_match = _END_RE.match(lines[i])
            if end_match is not None:
                end_key = end_match.group("key")
                i += 1
                break
            body.append(lines[i])
            i += 1
        if end_key is None:
            raise RegionMergeError(f"BEGIN marker for {key!r} has no matching END marker.")
        if end_key != key:
            raise RegionMergeError(
                f"BEGIN marker for {key!r} is closed by END marker for {end_key!r}."
            )

        seen_keys.add(key)
        chunks.append(_Chunk(True, key, "\n".join(body)))

    flush_literal()
    return chunks


def existing_region_keys(text: str) -> set[str]:
    """Return every generated-region key already present in ``text``.

    Raises:
        RegionMergeError: If ``text`` has malformed or duplicate markers.
    """
    return {chunk.key for chunk in parse_regions(text) if chunk.is_region and chunk.key is not None}


def merge(existing_text: str, generated_regions: dict[str, str]) -> tuple[str, list[str]]:
    """Merge freshly generated regions into an existing file's text.

    Args:
        existing_text: The file's current content.
        generated_regions: Mapping of region key to freshly generated
            body text (no markers), in the order new regions should be
            appended if not already present.

    Returns:
        A ``(new_text, orphaned_keys)`` pair. ``orphaned_keys`` lists
        region keys present in ``existing_text`` but absent from
        ``generated_regions`` (e.g. a component schema that was
        removed) - those regions are left in the file untouched, not
        deleted, since this package never discards code without being
        told to.

    Raises:
        RegionMergeError: If ``existing_text`` has malformed or
            duplicate markers.
    """
    chunks = parse_regions(existing_text)
    existing_keys = {chunk.key for chunk in chunks if chunk.is_region and chunk.key is not None}
    orphaned = [key for key in existing_keys if key not in generated_regions]

    merged: list[_Chunk] = []
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.is_region and chunk.key in generated_regions:
            merged.append(_Chunk(True, chunk.key, generated_regions[chunk.key]))
            seen.add(chunk.key)
        else:
            merged.append(chunk)

    new_keys = [key for key in generated_regions if key not in seen]
    if new_keys:
        appended = "\n\n".join(
            f"{begin_marker(key)}\n{generated_regions[key]}\n{end_marker(key)}" for key in new_keys
        )
        merged.append(_Chunk(False, None, f"\n{appended}\n"))

    return _render(merged), orphaned


def _render(chunks: list[_Chunk]) -> str:
    parts = []
    for chunk in chunks:
        if chunk.is_region and chunk.key is not None:
            parts.append(f"{begin_marker(chunk.key)}\n{chunk.text}\n{end_marker(chunk.key)}")
        else:
            parts.append(chunk.text)
    # Always exactly one trailing newline, regardless of how many blank
    # lines the last chunk happened to end with - otherwise parsing a
    # freshly rendered file back and re-merging the same input would not
    # be a stable fixed point (a spurious "no newline at end of file"
    # diff on every other regeneration).
    return "\n".join(parts).rstrip("\n") + "\n"

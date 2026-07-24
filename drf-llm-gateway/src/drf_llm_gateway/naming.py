"""Naming helpers shared by the registry and schema modules."""

from __future__ import annotations

import re

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_TRAILING_SUFFIXES = ("ViewSet", "APIView", "View")


def viewset_base_name(viewset_class: type) -> str:
    """Derive a snake_case base name from a viewset class name.

    Strips a trailing ``ViewSet``/``APIView``/``View`` suffix, then
    converts CamelCase to snake_case.

    Args:
        viewset_class: The viewset class to derive a name from.

    Returns:
        A lowercase, underscore-separated base name, e.g.
        ``"ArticleViewSet"`` -> ``"article"``.

    Example:
        >>> class ArticleViewSet: ...
        >>> viewset_base_name(ArticleViewSet)
        'article'
    """
    name = viewset_class.__name__
    for suffix in _TRAILING_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    return _CAMEL_BOUNDARY.sub("_", name).lower()

"""Name conversion helpers shared by every code generator.

Deliberately does not attempt English singularization/pluralization
(``"categories"`` -> ``"category"``): that class of heuristic is wrong
often enough on real-world resource names to cause more confusion than
it saves. Resource class names are derived directly from the path
segment as written in the schema - see
:func:`resource_group_key` and :func:`viewset_class_name`.
"""

from __future__ import annotations

import re

_WORD_BOUNDARY_RE = re.compile(r"[^a-zA-Z0-9]+")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _words(name: str) -> list[str]:
    """Split ``name`` into lowercase words, handling snake/kebab/camel case."""
    name = _CAMEL_BOUNDARY_RE.sub("_", name)
    parts = [p for p in _WORD_BOUNDARY_RE.split(name) if p]
    return [p.lower() for p in parts]


def to_class_name(name: str) -> str:
    """Convert any identifier style to ``PascalCase``.

    >>> to_class_name("blog_post")
    'BlogPost'
    >>> to_class_name("blog-post")
    'BlogPost'
    >>> to_class_name("BlogPost")
    'BlogPost'
    """
    words = _words(name)
    if not words:
        return "Unnamed"
    return "".join(word.capitalize() for word in words)


def to_snake_case(name: str) -> str:
    """Convert any identifier style to ``snake_case``.

    >>> to_snake_case("BlogPost")
    'blog_post'
    >>> to_snake_case("blog-post")
    'blog_post'
    """
    words = _words(name)
    return "_".join(words) if words else "unnamed"


def path_segments(path: str) -> list[str]:
    """Split an OpenAPI path template into its literal and param segments.

    >>> path_segments("/articles/{id}/comments/")
    ['articles', '{id}', 'comments']
    """
    return [segment for segment in path.strip("/").split("/") if segment]


def is_param_segment(segment: str) -> bool:
    """Return whether a path segment is a ``{param}`` placeholder."""
    return segment.startswith("{") and segment.endswith("}")


def resource_group_key(path: str) -> str:
    """Return the top-level resource this path belongs to.

    All operations sharing a first literal path segment are generated
    onto one ``ViewSet`` - ``/articles/`` and ``/articles/{id}/`` and
    ``/articles/{id}/comments/`` all share the group key ``"articles"``.

    >>> resource_group_key("/articles/{id}/comments/")
    'articles'
    """
    segments = path_segments(path)
    for segment in segments:
        if not is_param_segment(segment):
            return to_snake_case(segment)
    return "root"


def viewset_class_name(group_key: str) -> str:
    """Return the ``ViewSet`` class name for a resource group.

    >>> viewset_class_name("articles")
    'ArticlesViewSet'
    """
    return f"{to_class_name(group_key)}ViewSet"


def comment_safe(text: str) -> str:
    """Strip line breaks that would let ``text`` escape a ``#`` comment.

    Schema-derived free text (paths, ``$ref`` targets, operation IDs) is
    otherwise trusted (see ``docs/security.md``), but a stray newline
    embedded in it would turn the rest of a crafted value into a new,
    uncommented source line once written into a generated file -
    collapse any line breaks to spaces so one comment can never span
    more than its own physical line.
    """
    return " ".join(text.splitlines())


def serializer_class_name(schema_name: str) -> str:
    """Return the ``Serializer`` class name for a component schema.

    >>> serializer_class_name("Article")
    'ArticleSerializer'
    """
    return f"{to_class_name(schema_name)}Serializer"

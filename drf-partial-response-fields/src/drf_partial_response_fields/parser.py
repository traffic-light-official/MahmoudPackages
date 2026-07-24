"""Parser for the ``fields`` query-parameter mini-language.

Grammar (informal EBNF)::

    fields_expr  := group
    group        := entry ("," entry)* | ""
    entry        := "*"
    entry        := "-" NAME
    entry        := (NAME ":")? NAME ("(" group ")")?
    NAME         := [A-Za-z_][A-Za-z0-9_]*

Semantics:

* An empty group means "no restriction" (``mode="all"``).
* A lone ``*`` also means "no restriction" and cannot be combined with
  anything else in the same group.
* A group made entirely of plain names (optionally aliased and/or nested)
  is an *include* list: only those names are kept.
* A group made entirely of ``-NAME`` entries is an *exclude* list: every
  field is kept except those named.
* Mixing plain names with ``-NAME`` entries, or mixing either with ``*``,
  in the *same* group is rejected as ambiguous — write two separate
  requests, or restructure the expression, instead.

Examples::

    "id,name"                     -> include {id, name}
    "-password,-internal_notes"   -> exclude {password, internal_notes}
    "author(name,email)"          -> include {author: include {name, email}}
    "avatar:profile_picture"      -> include {profile_picture (alias: avatar)}
    "*"                           -> all
"""

from __future__ import annotations

from drf_partial_response_fields.exceptions import InvalidFieldsParameterError
from drf_partial_response_fields.tree import ALL_TREE, FieldSpec, FieldTree

_NAME_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_NAME_CONTINUE = _NAME_START | frozenset("0123456789")
_WHITESPACE = frozenset(" \t\n\r")


def parse_fields(raw: str, *, max_depth: int = 6, max_length: int = 2000) -> FieldTree:
    """Parse a raw ``fields`` query-parameter value into a :class:`FieldTree`.

    Args:
        raw: The raw string value of the query parameter, e.g.
            ``"id,name,author(name,email)"``. An empty string is treated
            as "no restriction".
        max_depth: Maximum allowed parenthesis nesting depth. Guards
            against pathological input designed to exhaust the parser's
            call stack.
        max_length: Maximum allowed length of ``raw``, checked before any
            parsing work is done.

    Returns:
        The parsed, immutable :class:`~drf_partial_response_fields.tree.FieldTree`.

    Raises:
        drf_partial_response_fields.exceptions.InvalidFieldsParameterError: If
            ``raw`` is not valid according to the grammar above, exceeds
            ``max_length``, or exceeds ``max_depth``.

    Example:
        >>> tree = parse_fields("id,author(name,email)")
        >>> tree.mode
        'include'
        >>> sorted(tree.includes)
        ['author', 'id']
    """
    if not raw:
        return ALL_TREE
    if len(raw) > max_length:
        raise InvalidFieldsParameterError(
            f"The fields parameter is too long ({len(raw)} characters); "
            f"the maximum allowed length is {max_length}."
        )
    parser = _Parser(raw, max_depth=max_depth)
    tree = parser.parse_group(depth=1)
    parser.skip_whitespace()
    if parser.pos != len(raw):
        raise InvalidFieldsParameterError(
            f"Unexpected character {raw[parser.pos]!r} at position {parser.pos} "
            f"in fields expression {raw!r}."
        )
    return tree


class _Parser:
    """Stateful recursive-descent parser over a single ``fields`` string."""

    __slots__ = ("max_depth", "pos", "text")

    def __init__(self, text: str, *, max_depth: int) -> None:
        self.text = text
        self.pos = 0
        self.max_depth = max_depth

    def skip_whitespace(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in _WHITESPACE:
            self.pos += 1

    def _peek(self) -> str | None:
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _parse_name(self) -> str:
        start = self.pos
        if self._peek() is None or self.text[self.pos] not in _NAME_START:
            found = self._peek()
            found_desc = repr(found) if found is not None else "end of string"
            raise InvalidFieldsParameterError(
                f"Expected a field name at position {self.pos} in fields expression "
                f"{self.text!r}, found {found_desc}."
            )
        self.pos += 1
        while self._peek() is not None and self.text[self.pos] in _NAME_CONTINUE:
            self.pos += 1
        return self.text[start : self.pos]

    def _expect_separator(self) -> None:
        """Require the next non-whitespace character to end this entry.

        Called immediately after a complete entry (a name, an aliased
        name, a nested group, a ``-name`` exclusion, or a lone ``*``) has
        been consumed. Anything other than ``,``, ``)``, or end-of-string
        at this point means two entries were written without a separating
        comma (e.g. ``"field name"``), which is rejected rather than
        silently accepted as two fields.
        """
        self.skip_whitespace()
        nxt = self._peek()
        if nxt is not None and nxt not in (",", ")"):
            raise InvalidFieldsParameterError(
                f"Expected ',' or ')' at position {self.pos} in fields expression "
                f"{self.text!r}, found {nxt!r}. Did you forget a comma between fields?"
            )

    def parse_group(self, *, depth: int) -> FieldTree:
        includes: dict[str, FieldSpec] = {}
        excludes: set[str] = set()
        saw_star = False
        saw_any = False

        while True:
            self.skip_whitespace()
            ch = self._peek()
            if ch is None or ch == ")":
                break
            if ch == ",":
                self.pos += 1
                continue
            if ch == "*":
                self.pos += 1
                saw_star = True
                saw_any = True
                self._expect_separator()
                continue
            if ch == "-":
                self._parse_exclude_entry(excludes)
                saw_any = True
                continue

            self._parse_include_entry(includes, depth=depth)
            saw_any = True

        return self._build_tree(
            includes=includes, excludes=excludes, saw_star=saw_star, saw_any=saw_any
        )

    def _parse_exclude_entry(self, excludes: set[str]) -> None:
        self.pos += 1
        name = self._parse_name()
        if name in excludes:
            raise InvalidFieldsParameterError(
                f"Field {name!r} was excluded more than once in the same group."
            )
        excludes.add(name)
        self._expect_separator()

    def _parse_include_entry(self, includes: dict[str, FieldSpec], *, depth: int) -> None:
        first = self._parse_name()
        self.skip_whitespace()
        alias: str | None = None
        name = first
        if self._peek() == ":":
            self.pos += 1
            self.skip_whitespace()
            name = self._parse_name()
            alias = first

        children = self._parse_optional_children(depth=depth)

        if name in includes:
            raise InvalidFieldsParameterError(
                f"Field {name!r} was requested more than once in the same group."
            )
        includes[name] = FieldSpec(name=name, alias=alias, children=children)
        self._expect_separator()

    def _parse_optional_children(self, *, depth: int) -> FieldTree | None:
        self.skip_whitespace()
        if self._peek() != "(":
            return None
        if depth >= self.max_depth:
            raise InvalidFieldsParameterError(
                f"Fields expression exceeds the maximum nesting depth "
                f"of {self.max_depth} at position {self.pos}."
            )
        self.pos += 1
        children = self.parse_group(depth=depth + 1)
        self.skip_whitespace()
        if self._peek() != ")":
            raise InvalidFieldsParameterError(
                f"Unbalanced parentheses: expected ')' at position {self.pos} "
                f"in fields expression {self.text!r}."
            )
        self.pos += 1
        return children

    def _build_tree(
        self,
        *,
        includes: dict[str, FieldSpec],
        excludes: set[str],
        saw_star: bool,
        saw_any: bool,
    ) -> FieldTree:
        if not saw_any:
            return ALL_TREE
        if saw_star:
            if includes or excludes:
                raise InvalidFieldsParameterError(
                    "'*' cannot be combined with explicit field names or exclusions "
                    "in the same group."
                )
            return ALL_TREE
        if includes and excludes:
            raise InvalidFieldsParameterError(
                "Cannot combine plain field names with '-'-prefixed exclusions in the "
                "same group; use one style per group."
            )
        if excludes:
            return FieldTree(mode="exclude", excludes=frozenset(excludes))
        return FieldTree(mode="include", includes=includes)

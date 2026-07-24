"""Unit tests for the ``requires_related`` optimizer-hint decorator."""

from __future__ import annotations

from drf_partial_response_fields.decorators import OptimizationHints, get_hints, requires_related


class TestRequiresRelated:
    def test_attaches_hints_to_function(self) -> None:
        @requires_related(select_related=["author"], prefetch_related=["tags"])
        def get_something(self: object, obj: object) -> str:
            return "value"

        hints = get_hints(get_something)
        assert hints == OptimizationHints(select_related=("author",), prefetch_related=("tags",))

    def test_defaults_are_empty_tuples(self) -> None:
        @requires_related()
        def get_something(self: object, obj: object) -> str:
            return "value"

        hints = get_hints(get_something)
        assert hints == OptimizationHints()

    def test_undecorated_function_has_no_hints(self) -> None:
        def get_something(self: object, obj: object) -> str:
            return "value"

        assert get_hints(get_something) is None

    def test_decorator_preserves_function_behavior(self) -> None:
        @requires_related(select_related=["author"])
        def get_something(self: object, obj: object) -> str:
            return "computed"

        assert get_something(None, None) == "computed"

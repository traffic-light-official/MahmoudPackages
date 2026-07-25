"""Tests for :mod:`drf_n_plus_one_query_guard.decorators`."""

from __future__ import annotations

import pytest

from drf_n_plus_one_query_guard.decorators import guard_view
from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError
from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


class TestGuardView:
    def test_wrapped_function_return_value_passes_through(self, make_article) -> None:
        @guard_view()
        def view() -> str:
            list(Article.objects.select_related("author").all())
            return "ok"

        assert view() == "ok"

    def test_raises_when_configured_and_violation_found(self, several_articles) -> None:
        @guard_view(mode="raise", threshold=2)
        def view() -> None:
            for article in Article.objects.all():
                _ = article.author.name

        with pytest.raises(NPlusOneDetectedError):
            view()

    def test_preserves_function_metadata(self) -> None:
        @guard_view()
        def my_view() -> None:
            """A docstring."""

        assert my_view.__name__ == "my_view"
        assert my_view.__doc__ == "A docstring."

    def test_works_on_a_bound_method(self, several_articles) -> None:
        class View:
            @guard_view(mode="raise", threshold=2)
            def list(self) -> None:
                for article in Article.objects.all():
                    _ = article.author.name

        with pytest.raises(NPlusOneDetectedError):
            View().list()

    def test_a_real_exception_from_the_view_propagates(self) -> None:
        @guard_view()
        def view() -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            view()

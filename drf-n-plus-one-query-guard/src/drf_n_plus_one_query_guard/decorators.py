"""A per-view/per-action decorator applying an N+1 guard to one method."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, TypeVar

from drf_n_plus_one_query_guard.guard import NPlusOneGuard

if TYPE_CHECKING:
    from collections.abc import Callable

F = TypeVar("F", bound="Callable[..., Any]")


def guard_view(*, threshold: int | None = None, mode: str | None = None) -> Callable[[F], F]:
    """Wrap a DRF view/viewset method in an :class:`~drf_n_plus_one_query_guard.guard.NPlusOneGuard`
    (see that class for the exact ``warn``/``raise``/``report`` behavior).

    Args:
        threshold: Overrides the ``THRESHOLD`` setting for this view only.
        mode: Overrides the ``MODE`` setting for this view only
            (``"warn"``, ``"raise"``, or ``"report"``).

    Returns:
        A decorator suitable for a ``ViewSet`` method
        (``list``/``retrieve``/a custom ``@action``-decorated method) or
        a function-based view.

    Example:
        .. code-block:: python

            class ArticleViewSet(viewsets.ModelViewSet):
                @guard_view(mode="raise")
                def list(self, request, *args, **kwargs):
                    return super().list(request, *args, **kwargs)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with NPlusOneGuard(threshold=threshold, mode=mode):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator

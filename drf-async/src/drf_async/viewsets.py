"""Async equivalents of ``rest_framework.viewsets``.

Built the same way DRF builds its own ``ModelViewSet``/
``ReadOnlyModelViewSet``: ``ViewSetMixin`` (from DRF - routing an
action name to a bound method is just attribute lookup, no I/O)
combined with :class:`~drf_async.generics.AsyncGenericAPIView` and the
async mixins from :mod:`drf_async.mixins`. Those mixins name their
action methods (``list``/``create``/``retrieve``/``update``/
``partial_update``/``destroy``) identically to DRF's own sync mixins -
required for ``DefaultRouter``/``SimpleRouter`` to bind to them at all,
since routers hardcode those exact strings - so registering an
``AsyncModelViewSet`` with a standard router needs no special handling.

``AsyncGenericViewSet`` does override ``as_view()``, though - see its
docstring for why that one override is unavoidable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from rest_framework.viewsets import ViewSetMixin

if TYPE_CHECKING:
    from rest_framework.decorators import ViewSetAction

from drf_async.generics import AsyncGenericAPIView
from drf_async.mixins import (
    AsyncCreateModelMixin,
    AsyncDestroyModelMixin,
    AsyncListModelMixin,
    AsyncRetrieveModelMixin,
    AsyncUpdateModelMixin,
)


class AsyncGenericViewSet(ViewSetMixin, AsyncGenericAPIView):
    """The async equivalent of ``rest_framework.viewsets.GenericViewSet``.

    ``ViewSetMixin.as_view()`` completely reimplements Django's
    ``View.as_view()`` (it does not call ``super().as_view()`` at all)
    to bind ``{"get": "list", ...}``-style action maps to methods - and
    never calls ``asgiref.sync.markcoroutinefunction()`` on the closure
    it returns, since it predates Django's async view support entirely.
    Without that marking, Django's handler calls the returned view
    synchronously, gets back an un-awaited coroutine (since our action
    methods are ``async def``), and raises
    ``ValueError: ... returned an unawaited coroutine instead``. This
    override calls DRF's own ``as_view()`` to get the fully-bound
    closure, then applies the same marking Django's own
    ``View.as_view()`` would have, based on whether the bound actions
    are themselves coroutine functions.
    """

    @classmethod
    def as_view(
        cls, actions: dict[str, str | ViewSetAction[Any]] | None = None, **initkwargs: Any
    ) -> Any:
        """Bind ``actions`` via DRF's own logic, then mark the result async if needed."""
        view = super().as_view(actions=actions, **initkwargs)
        if actions and all(
            iscoroutinefunction(getattr(cls, action, None))
            for action in actions.values()
            if isinstance(action, str)
        ):
            markcoroutinefunction(view)
        return view


class AsyncReadOnlyModelViewSet(AsyncListModelMixin, AsyncRetrieveModelMixin, AsyncGenericViewSet):
    """The async equivalent of ``rest_framework.viewsets.ReadOnlyModelViewSet``."""


class AsyncModelViewSet(
    AsyncCreateModelMixin,
    AsyncRetrieveModelMixin,
    AsyncUpdateModelMixin,
    AsyncDestroyModelMixin,
    AsyncListModelMixin,
    AsyncGenericViewSet,
):
    """The async equivalent of ``rest_framework.viewsets.ModelViewSet``."""

"""View-level wiring for sparse fieldsets and automatic query optimization.

:class:`PartialResponseMixin` is the integration point most users reach
for: mix it into a :class:`~rest_framework.generics.GenericAPIView`
subclass (including any :class:`~rest_framework.viewsets.ModelViewSet` or
:class:`~rest_framework.viewsets.GenericViewSet`) to get both
``?fields=`` filtering and automatic ``select_related`` /
``prefetch_related`` / ``only`` optimization with zero further
configuration, as long as the view's serializer uses
:class:`~drf_partial_response_fields.serializers.PartialFieldsSerializerMixin`.

For plain :class:`~rest_framework.views.APIView` subclasses, which have no
``get_queryset`` / ``get_serializer_class`` to hook into, use the
module-level :func:`parse_request_fields` helper instead and pass its
result into the serializer context manually — see
``docs/advanced-usage.md``.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.optimizer import optimize_queryset
from drf_partial_response_fields.parser import parse_fields
from drf_partial_response_fields.settings import get_setting
from drf_partial_response_fields.tree import ALL_TREE, FieldTree

_CACHE_ATTR = "_partial_response_fields_tree_cache"


def parse_request_fields(request: Request) -> FieldTree:
    """Parse the ``fields`` query parameter off an in-flight request.

    Use this directly in a plain :class:`~rest_framework.views.APIView`
    (which :class:`PartialResponseMixin` cannot hook into automatically)
    to build the context dict for a serializer by hand:

    .. code-block:: python

        class ArticleDetailView(APIView):
            def get(self, request, pk):
                article = get_object_or_404(Article, pk=pk)
                serializer = ArticleSerializer(
                    article,
                    context={
                        "request": request,
                        PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY: parse_request_fields(request),
                    },
                )
                return Response(serializer.data)

    Args:
        request: The current DRF :class:`~rest_framework.request.Request`.

    Returns:
        The parsed :class:`~drf_partial_response_fields.tree.FieldTree` for
        this request, using the configured ``QUERY_PARAM``, ``MAX_DEPTH``,
        and ``MAX_FIELDS_LENGTH`` settings.

    Raises:
        drf_partial_response_fields.exceptions.InvalidFieldsParameterError: If
            the query parameter value is not syntactically valid.
    """
    raw = request.query_params.get(get_setting("QUERY_PARAM"), "")
    return parse_fields(
        raw,
        max_depth=get_setting("MAX_DEPTH"),
        max_length=get_setting("MAX_FIELDS_LENGTH"),
    )


#: Public alias of :data:`drf_partial_response_fields.constants.CONTEXT_KEY`,
#: exported under a more discoverable name for manual (non-mixin)
#: integrations such as plain ``APIView`` subclasses.
PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY = CONTEXT_KEY


class PartialResponseMixin:
    """Adds ``?fields=`` support and automatic query optimization to a view.

    Mix this into any :class:`~rest_framework.generics.GenericAPIView`
    subclass — including every generic view (``ListAPIView``,
    ``RetrieveUpdateDestroyAPIView``, ...) and every viewset
    (``ModelViewSet``, ``ReadOnlyModelViewSet``, custom
    ``GenericViewSet`` subclasses) — *before* the DRF base class in the
    MRO:

    .. code-block:: python

        class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

    This mixin does two things:

    1. Injects the parsed ``fields`` request into the serializer context
       (via :meth:`get_serializer_context`), which
       :class:`~drf_partial_response_fields.serializers.PartialFieldsSerializerMixin`
       reads to filter fields.
    2. Rewrites the queryset (via :meth:`get_queryset`) to add
       ``select_related``, ``prefetch_related``, and ``only`` so that only
       the data needed for the requested fields is fetched — see
       :func:`drf_partial_response_fields.optimizer.optimize_queryset`.

    Both behaviors compose transparently with pagination: optimization
    happens on the unsliced queryset before the paginator runs, so page
    size and query cost stay independent of which fields were requested.
    """

    request: Request
    kwargs: dict[str, Any]

    def get_serializer_context(self) -> dict[str, Any]:
        """Return the serializer context with the parsed fields tree attached.

        Returns:
            The context dict produced by the next class in the MRO (e.g.
            ``GenericAPIView.get_serializer_context``), with the parsed
            :class:`~drf_partial_response_fields.tree.FieldTree` added
            under
            :data:`~drf_partial_response_fields.constants.CONTEXT_KEY`.
        """
        context: dict[str, Any] = super().get_serializer_context()  # type: ignore[misc]
        context[CONTEXT_KEY] = self.get_partial_response_fields_tree()
        return context

    def get_partial_response_fields_tree(self) -> FieldTree:
        """Return (and cache) the parsed fields tree for the current request.

        When the :ref:`SAFE_METHODS_ONLY <settings-safe-methods-only>`
        setting is enabled (the default), this returns
        :data:`~drf_partial_response_fields.tree.ALL_TREE` for any request
        whose method is not ``GET``, ``HEAD``, or ``OPTIONS`` — see the
        setting's docstring for why this matters for write endpoints.

        Returns:
            The :class:`~drf_partial_response_fields.tree.FieldTree` parsed
            from this request's ``fields`` query parameter. The result is
            cached on the view instance for the lifetime of the request,
            since a view instance handles exactly one request in DRF.
        """
        if not hasattr(self, _CACHE_ATTR):
            if get_setting("SAFE_METHODS_ONLY") and self.request.method not in SAFE_METHODS:
                tree = ALL_TREE
            else:
                tree = parse_request_fields(self.request)
            setattr(self, _CACHE_ATTR, tree)
        cached: FieldTree = getattr(self, _CACHE_ATTR)
        return cached

    def get_queryset(self) -> Any:
        """Return the view's queryset, optimized for the requested fields.

        Returns:
            The queryset produced by the next class in the MRO (e.g.
            ``GenericAPIView.get_queryset``), passed through
            :func:`~drf_partial_response_fields.optimizer.optimize_queryset`
            when the view's serializer is a
            :class:`~rest_framework.serializers.ModelSerializer` subclass
            and query optimization is enabled. Non-model serializers, or
            optimization disabled via the ``ENABLE_QUERY_OPTIMIZATION``
            setting, leave the queryset untouched.
        """
        queryset = super().get_queryset()  # type: ignore[misc]
        serializer_class = self.get_serializer_class()  # type: ignore[attr-defined]
        if not (
            isinstance(serializer_class, type) and issubclass(serializer_class, ModelSerializer)
        ):
            return queryset
        tree = self.get_partial_response_fields_tree()
        return optimize_queryset(queryset, serializer_class, tree)

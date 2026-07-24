"""Tests for :mod:`drf_partial_response_fields.mixins`."""

from __future__ import annotations

import pytest
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from drf_partial_response_fields.constants import CONTEXT_KEY
from drf_partial_response_fields.mixins import PartialResponseMixin, parse_request_fields
from drf_partial_response_fields.tree import ALL_TREE
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleStatsSerializer
from tests.test_app.views import ArticleViewSet

pytestmark = pytest.mark.django_db


def _drf_request(api_rf: APIRequestFactory, path: str) -> Request:
    return Request(api_rf.get(path))


class TestParseRequestFields:
    def test_no_query_param_returns_all(self, api_rf: APIRequestFactory) -> None:
        request = _drf_request(api_rf, "/articles/")
        assert parse_request_fields(request) is ALL_TREE

    def test_query_param_is_parsed(self, api_rf: APIRequestFactory) -> None:
        request = _drf_request(api_rf, "/articles/?fields=title,author(name)")
        tree = parse_request_fields(request)
        assert tree.mode == "include"
        assert set(tree.includes) == {"title", "author"}

    def test_custom_query_param_name_is_respected(self, api_rf: APIRequestFactory) -> None:
        from django.test import override_settings

        with override_settings(PARTIAL_RESPONSE_FIELDS={"QUERY_PARAM": "select"}):
            request = _drf_request(api_rf, "/articles/?select=title")
            tree = parse_request_fields(request)
        assert set(tree.includes) == {"title"}


class TestViewSetIntegration:
    def test_get_partial_response_fields_tree_is_cached_per_request(
        self, api_rf: APIRequestFactory, article: Article
    ) -> None:
        view = ArticleViewSet()
        view.request = _drf_request(api_rf, "/articles/?fields=title")
        view.format_kwarg = None
        tree_first = view.get_partial_response_fields_tree()
        tree_second = view.get_partial_response_fields_tree()
        assert tree_first is tree_second

    def test_get_queryset_is_optimized(self, api_rf: APIRequestFactory, article: Article) -> None:
        view = ArticleViewSet()
        view.request = _drf_request(api_rf, "/articles/?fields=title,author(name)")
        view.format_kwarg = None
        view.kwargs = {}
        qs = view.get_queryset()
        assert "author" in qs.query.select_related

    def test_serializer_context_includes_parsed_tree(
        self, api_rf: APIRequestFactory, article: Article
    ) -> None:
        view = ArticleViewSet()
        view.request = _drf_request(api_rf, "/articles/?fields=title")
        view.format_kwarg = None
        view.kwargs = {}
        context = view.get_serializer_context()
        assert CONTEXT_KEY in context
        assert set(context[CONTEXT_KEY].includes) == {"title"}

    def test_unsafe_method_ignores_fields_param_by_default(
        self, api_rf: APIRequestFactory, article: Article
    ) -> None:
        view = ArticleViewSet()
        request = api_rf.post("/articles/?fields=title")
        view.request = Request(request)
        view.request._request.method = "POST"
        view.format_kwarg = None
        tree = view.get_partial_response_fields_tree()
        assert tree is ALL_TREE

    def test_safe_methods_only_setting_disabled_applies_fields_to_writes(
        self, api_rf: APIRequestFactory, article: Article
    ) -> None:
        from django.test import override_settings

        view = ArticleViewSet()
        request = api_rf.post("/articles/?fields=title")
        view.request = Request(request)
        view.format_kwarg = None
        with override_settings(PARTIAL_RESPONSE_FIELDS={"SAFE_METHODS_ONLY": False}):
            tree = view.get_partial_response_fields_tree()
        assert tree is not ALL_TREE
        assert set(tree.includes) == {"title"}


class _ArticleStatsListView(PartialResponseMixin, ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleStatsSerializer


class TestNonModelSerializerIsUnaffectedByOptimization:
    def test_get_queryset_is_returned_unmodified_for_non_model_serializer(
        self, api_rf: APIRequestFactory, article: Article
    ) -> None:
        view = _ArticleStatsListView()
        view.request = _drf_request(api_rf, "/stats/?fields=title")
        view.format_kwarg = None
        view.kwargs = {}
        qs = view.get_queryset()
        assert qs.query.select_related is False
        fields, defer = qs.query.deferred_loading
        assert defer is True
        assert fields == frozenset()

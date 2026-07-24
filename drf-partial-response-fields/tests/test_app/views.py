"""Views used by the integration test suite."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from drf_partial_response_fields.mixins import PartialResponseMixin
from tests.test_app.models import Article
from tests.test_app.serializers import ArticlePKAuthorSerializer, ArticleSerializer


class ArticlePagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = ArticlePagination


class ArticlePKAuthorListView(PartialResponseMixin, ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticlePKAuthorSerializer

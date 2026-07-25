"""Views for the test suite's Django project."""

from __future__ import annotations

from rest_framework import viewsets

from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

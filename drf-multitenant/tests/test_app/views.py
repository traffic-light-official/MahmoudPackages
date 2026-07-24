"""DRF views used by the test suite."""

from __future__ import annotations

from rest_framework import viewsets

from drf_multitenant.permissions import IsTenantMember
from tests.test_app.models import Article, Author
from tests.test_app.serializers import ArticleSerializer, AuthorSerializer


class AuthorViewSet(viewsets.ModelViewSet[Author]):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsTenantMember]


class ArticleViewSet(viewsets.ModelViewSet[Article]):
    queryset = Article.objects.select_related("tenant", "author").all()
    serializer_class = ArticleSerializer
    permission_classes = [IsTenantMember]

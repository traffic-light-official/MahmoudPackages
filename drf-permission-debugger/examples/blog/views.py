"""Views demonstrating this package's main features."""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from drf_permission_debugger import PermissionDebugMixin
from examples.blog.models import Article
from examples.blog.permissions import IsOwner
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(PermissionDebugMixin, ModelViewSet):
    """Guarded by an object-level permission, for retrieve/update/destroy checks."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("owner").all()

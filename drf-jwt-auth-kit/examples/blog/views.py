"""Example views for the blog API shown in docs/quickstart.md.

``ArticleViewSet`` requires authentication via
:class:`~drf_jwt_auth_kit.authentication.JWTAuthentication` (configured
globally through ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`` -
see ``docs/getting-started.md``) - no extra wiring is needed here beyond
a normal ``IsAuthenticated`` permission.
"""

from __future__ import annotations

from rest_framework import permissions, viewsets

from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer: ArticleSerializer) -> None:
        serializer.save(author=self.request.user)

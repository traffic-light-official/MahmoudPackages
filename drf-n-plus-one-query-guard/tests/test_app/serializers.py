"""DRF serializers for the test app."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer[Author]):
    """Serializes an :class:`~tests.test_app.models.Author`."""

    class Meta:
        model = Author
        fields = ["id", "name"]


class ArticleSerializer(serializers.ModelSerializer[Article]):
    """Serializes an :class:`~tests.test_app.models.Article`.

    ``author_name`` deliberately accesses ``obj.author.name`` - without
    ``select_related("author")`` on the queryset, serializing a list of
    articles triggers exactly one extra query per article (the N+1 this
    whole package exists to catch).
    """

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "author", "author_name"]

    def get_author_name(self, obj: Article) -> str:
        return obj.author.name

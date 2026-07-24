"""Serializers used by the test suite, including a writable nested serializer.

``ArticleSerializer``'s nested, writable ``author`` field is what makes it
possible to exercise nested validation error normalization end-to-end
(``author/email`` style pointers) via real HTTP requests in
``tests/test_integration.py``.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from tests.test_app.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~tests.test_app.models.Author`."""

    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~tests.test_app.models.Article` with a writable nested author."""

    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author"]

    def create(self, validated_data: dict[str, Any]) -> Article:
        author_data = validated_data.pop("author")
        author = Author.objects.create(**author_data)
        return Article.objects.create(author=author, **validated_data)

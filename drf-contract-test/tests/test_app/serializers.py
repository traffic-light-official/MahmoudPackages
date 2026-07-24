"""DRF serializers used by the test suite."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer[Author]):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(serializers.ModelSerializer[Article]):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source="author", write_only=True
    )

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "body",
            "status",
            "author",
            "author_id",
            "published_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

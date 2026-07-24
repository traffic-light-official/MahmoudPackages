"""Example serializers for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from examples.blog.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author", "published"]

    def create(self, validated_data: dict[str, Any]) -> Article:
        author_data = validated_data.pop("author")
        author = Author.objects.create(**author_data)
        return Article.objects.create(author=author, **validated_data)

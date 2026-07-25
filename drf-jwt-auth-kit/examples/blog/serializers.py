"""Example serializers for the blog API shown in docs/quickstart.md."""

from __future__ import annotations

from rest_framework import serializers

from examples.blog.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body", "author"]
        read_only_fields = ["author"]

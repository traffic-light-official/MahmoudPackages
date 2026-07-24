"""Example serializer for the tiered blog API shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import serializers

from examples.blog_api.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body"]

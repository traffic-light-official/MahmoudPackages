"""Example serializers for the blog agent backend shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import serializers

from examples.blog_agent.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body", "author", "status"]
        read_only_fields = ["id"]

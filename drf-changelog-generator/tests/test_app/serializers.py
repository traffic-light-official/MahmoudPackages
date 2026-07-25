"""Serializers for the test suite's Django project."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body"]

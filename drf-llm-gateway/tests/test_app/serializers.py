"""Serializers used by the test suite, exercising every field shape."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article, Author, Tag


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "label"]


class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)
    tag_labels = TagSerializer(source="tags", many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "body",
            "author",
            "tags",
            "tag_labels",
            "status",
            "view_count",
            "comment_count",
            "created_at",
        ]
        read_only_fields = ["id", "view_count", "created_at"]

    def get_comment_count(self, obj: Article) -> int:
        return 0

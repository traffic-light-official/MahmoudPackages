"""Example serializers for the blog API shown in docs/examples.md."""

from __future__ import annotations

from rest_framework import serializers

from drf_partial_response_fields import PartialFieldsModelSerializer, requires_related
from examples.blog.models import Article, Author, Tag


class AuthorSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class TagSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "label"]


class ArticleSerializer(PartialFieldsModelSerializer):
    author = AuthorSerializer()
    tags = TagSerializer(many=True)
    comment_count = serializers.SerializerMethodField()
    editor_note = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "body",
            "author",
            "tags",
            "comment_count",
            "editor_note",
            "created_at",
        ]

    def get_comment_count(self, obj: Article) -> int:
        return obj.comments.count()

    @requires_related(select_related=["author"])
    def get_editor_note(self, obj: Article) -> str:
        return f"Reviewed by {obj.author.name}"

"""Serializers used by the test suite, exercising every field shape."""

from __future__ import annotations

from rest_framework import serializers

from drf_partial_response_fields.decorators import requires_related
from drf_partial_response_fields.serializers import (
    PartialFieldsModelSerializer,
    PartialFieldsSerializer,
)
from tests.test_app.models import Article, Author, Comment, Profile, Tag


class ProfileSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "display_name", "avatar_url"]


class AuthorSerializer(PartialFieldsModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = Author
        fields = ["id", "name", "email", "bio", "profile"]


class TagSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "label"]


class CommentSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "text"]


class ArticleSerializer(PartialFieldsModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        source="author", write_only=True, queryset=Author.objects.all()
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", write_only=True, many=True, queryset=Tag.objects.all(), required=False
    )
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    editor_note = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "body",
            "author",
            "author_id",
            "tags",
            "tag_ids",
            "comments",
            "comment_count",
            "editor_note",
            "view_count",
        ]

    def get_comment_count(self, obj: Article) -> int:
        return obj.comments.count()

    @requires_related(select_related=["author__profile"])
    def get_editor_note(self, obj: Article) -> str:
        try:
            return f"Reviewed by {obj.author.profile.display_name}"
        except Profile.DoesNotExist:
            return "Unreviewed"


class ArticlePKAuthorSerializer(PartialFieldsModelSerializer):
    """Variant exposing ``author`` as a plain PK (no nested serializer)."""

    class Meta:
        model = Article
        fields = ["id", "title", "author", "tags"]


class ArticleStatsSerializer(PartialFieldsSerializer):
    """A plain (non-model) serializer, used to test that query optimization
    is skipped for views whose serializer is not a ``ModelSerializer``."""

    total_articles = serializers.IntegerField()
    total_views = serializers.IntegerField()


class ArticleWithTagCountSerializer(PartialFieldsModelSerializer):
    """Exposes an annotation (``tag_count``) alongside plain model fields,
    used to test that annotated values are never mistaken for relations."""

    tag_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "tag_count"]

"""Example views for the blog API shown in docs/examples.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count
from rest_framework import serializers, viewsets

from drf_partial_response_fields import PartialFieldsModelSerializer, PartialResponseMixin
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class ArticleStatsSerializer(PartialFieldsModelSerializer):
    tag_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "tag_count"]


class ArticleStatsViewSet(PartialResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleStatsSerializer

    def get_queryset(self) -> QuerySet[Article]:
        return Article.objects.annotate(tag_count=Count("tags"))

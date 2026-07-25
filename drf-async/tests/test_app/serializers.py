"""DRF serializers for the test app."""

from __future__ import annotations

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from tests.test_app.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer[Author]):
    """Serializes an :class:`~tests.test_app.models.Author`."""

    class Meta:
        model = Author
        fields = ["id", "name"]


class ArticleSerializer(serializers.ModelSerializer[Article]):
    """Serializes an :class:`~tests.test_app.models.Article`.

    ``title`` carries an explicit ``UniqueValidator`` - a database
    query that runs synchronously during ``is_valid()`` - so tests
    exercise the "validation itself may touch the database" bridging
    path (:mod:`drf_async.mixins`), not just ``.save()``.
    """

    title = serializers.CharField(
        max_length=200, validators=[UniqueValidator(queryset=Article.objects.all())]
    )

    class Meta:
        model = Article
        fields = ["id", "title", "author"]

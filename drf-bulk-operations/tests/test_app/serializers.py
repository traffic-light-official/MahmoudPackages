"""DRF serializers for the test app."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article, Author


class AuthorSerializer(serializers.ModelSerializer[Author]):
    """Serializes an :class:`~tests.test_app.models.Author`."""

    class Meta:
        model = Author
        fields = ["id", "name"]


class ArticleSerializer(serializers.ModelSerializer[Article]):
    """Serializes an :class:`~tests.test_app.models.Article`.

    ``title`` is ``unique=True`` on the model, so ``ModelSerializer``
    automatically attaches a ``UniqueValidator`` - real bulk requests
    submitting a within-batch duplicate title exercise this.
    """

    class Meta:
        model = Article
        fields = ["id", "title", "author", "published"]

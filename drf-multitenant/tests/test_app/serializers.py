"""DRF serializers used by the test suite.

``author`` is deliberately *not* declared explicitly as a
``PrimaryKeyRelatedField(queryset=Author.objects.all())`` class
attribute: that queryset would be built exactly once, at import time,
before any tenant context exists — and TenantManager would return it
permanently empty (see ``docs/faq.md``). Letting ``ModelSerializer``
auto-build the field from the model's ``ForeignKey`` instead means the
field (and its queryset) is rebuilt fresh on every serializer
instantiation, i.e. once per request, correctly scoped to whichever
tenant is current at that point.
"""

from __future__ import annotations

from drf_multitenant.serializers import TenantScopedModelSerializer
from tests.test_app.models import Article, Author


class AuthorSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "tenant", "name"]
        read_only_fields = ["id", "tenant"]


class ArticleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "tenant", "author", "title"]
        read_only_fields = ["id", "tenant"]

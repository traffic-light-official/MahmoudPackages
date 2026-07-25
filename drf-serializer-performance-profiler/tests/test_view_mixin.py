"""Direct unit tests for :class:`ProfileSerializerViewMixin`, without a full HTTP request."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIRequestFactory

from tests.test_app.models import Article
from tests.test_app.views import ArticleViewSet

pytestmark = pytest.mark.django_db

factory = APIRequestFactory()


class _PlainArticleSerializer(ModelSerializer[Article]):
    """Deliberately does NOT mix in ProfileSerializerMixin - never produces a profile."""

    class Meta:
        model = Article
        fields = ["id", "title", "author"]


class _UnprofiledViewSet(ArticleViewSet):
    # ArticleViewSet already mixes in ProfileSerializerViewMixin - only the
    # serializer class needs overriding here, to one that never profiles.
    permission_classes = [AllowAny]
    serializer_class = _PlainArticleSerializer


class TestGetSerializerCalledMoreThanOnce:
    def test_second_call_appends_to_the_existing_capture_list(self, make_article) -> None:
        article = make_article()
        request = factory.get(f"/articles/{article.pk}/")
        view = ArticleViewSet()
        view.action_map = {"get": "retrieve"}
        view.request = view.initialize_request(request)
        view.kwargs = {"pk": article.pk}
        view.format_kwarg = None

        first = view.get_serializer(article)
        second = view.get_serializer(article)

        assert view._profiled_serializers == [first, second]


class TestNoProfileProduced:
    def test_finalize_response_returns_unmodified_when_serializer_never_profiled(
        self, make_article
    ) -> None:
        # Authorized to see the header, but the captured serializer doesn't mix
        # in ProfileSerializerMixin at all, so there's nothing to attach.
        article = make_article()
        request = factory.get(f"/articles/{article.pk}/")
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True, "RESTRICT_TO_STAFF": False}):
            response = _UnprofiledViewSet.as_view({"get": "retrieve"})(request, pk=article.pk)

        assert response.status_code == 200
        assert "X-Serializer-Profile" not in response

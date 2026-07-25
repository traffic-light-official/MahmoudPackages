"""End-to-end tests: real HTTP requests through the router."""

from __future__ import annotations

import pytest
from django.test import override_settings

pytestmark = pytest.mark.django_db


class TestOutputIsUnchanged:
    def test_response_body_is_unaffected_by_profiling(self, api_client, make_article) -> None:
        article = make_article(title="Unaffected", comment_count=2)

        with override_settings(SERIALIZER_PROFILER={"ENABLED": False}):
            disabled_response = api_client.get(f"/articles/{article.pk}/")
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            enabled_response = api_client.get(f"/articles/{article.pk}/")

        assert disabled_response.json() == enabled_response.json()
        assert disabled_response.status_code == enabled_response.status_code == 200


class TestHeaderDisabledByDefault:
    def test_no_header_when_serializer_profiler_disabled(self, api_client, make_article) -> None:
        article = make_article()
        response = api_client.get(f"/articles/{article.pk}/")
        assert "X-Serializer-Profile" not in response.headers


class TestHeaderEnabled:
    def test_staff_user_sees_the_header_on_detail_view(
        self, api_client, make_user, make_article
    ) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        article = make_article(comment_count=3)

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            response = api_client.get(f"/articles/{article.pk}/")

        assert response.status_code == 200
        header = response.headers["X-Serializer-Profile"]
        assert "comment_count=" in header
        assert "(1q)" in header
        assert "total=" in header
        assert "queries=1" in header

    def test_non_staff_user_does_not_see_the_header_by_default(
        self, api_client, make_user, make_article
    ) -> None:
        user = make_user(is_staff=False)
        api_client.force_authenticate(user=user)
        article = make_article()

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            response = api_client.get(f"/articles/{article.pk}/")

        assert "X-Serializer-Profile" not in response.headers

    def test_anonymous_user_does_not_see_the_header_by_default(
        self, api_client, make_article
    ) -> None:
        article = make_article()
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            response = api_client.get(f"/articles/{article.pk}/")
        assert "X-Serializer-Profile" not in response.headers

    def test_restrict_to_staff_false_shows_it_to_everyone(self, api_client, make_article) -> None:
        article = make_article()
        with override_settings(SERIALIZER_PROFILER={"ENABLED": True, "RESTRICT_TO_STAFF": False}):
            response = api_client.get(f"/articles/{article.pk}/")
        assert "X-Serializer-Profile" in response.headers

    def test_custom_header_name(self, api_client, make_user, make_article) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        article = make_article()

        with override_settings(
            SERIALIZER_PROFILER={"ENABLED": True, "HEADER_NAME": "X-Debug-Profile"}
        ):
            response = api_client.get(f"/articles/{article.pk}/")

        assert "X-Debug-Profile" in response.headers


class TestHeaderOnListView:
    def test_list_view_header_aggregates_across_every_row(
        self, api_client, make_user, make_author
    ) -> None:
        staff = make_user(is_staff=True)
        api_client.force_authenticate(user=staff)
        author = make_author()
        from tests.test_app.models import Article, Comment

        for i in range(3):
            article = Article.objects.create(title=f"Article {i}", author=author)
            Comment.objects.create(article=article, body="hi")

        with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
            response = api_client.get("/articles/")

        assert response.status_code == 200
        assert len(response.json()) == 3
        header = response.headers["X-Serializer-Profile"]
        assert "queries=3" in header


class TestLogSlowFieldsIndependentOfHeaderSettings:
    def test_logging_works_with_header_disabled_and_no_staff_user(
        self, api_client, make_article, caplog
    ) -> None:
        import logging

        article = make_article(comment_count=1)
        with (
            override_settings(
                SERIALIZER_PROFILER={
                    "ENABLED": False,
                    "LOG_SLOW_FIELDS": True,
                    "SLOW_FIELD_THRESHOLD_MS": 0.0,
                }
            ),
            caplog.at_level(logging.WARNING, logger="drf_serializer_performance_profiler"),
        ):
            response = api_client.get(f"/articles/{article.pk}/")

        assert "X-Serializer-Profile" not in response.headers
        assert any("comment_count" in record.message for record in caplog.records)

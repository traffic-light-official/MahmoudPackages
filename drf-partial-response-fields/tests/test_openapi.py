"""Tests for the optional drf-spectacular integration."""

from __future__ import annotations

import pytest

pytest.importorskip("drf_spectacular")

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import OpenApiParameter
from rest_framework.routers import DefaultRouter

from drf_partial_response_fields.openapi import (
    PartialResponseAutoSchema,
    fields_query_parameter,
)
from drf_partial_response_fields.settings import get_setting
from tests.test_app.views import ArticleViewSet

pytestmark = pytest.mark.django_db


class TestFieldsQueryParameter:
    def test_default_parameter_name_matches_setting(self) -> None:
        param = fields_query_parameter()
        assert param.name == get_setting("QUERY_PARAM")

    def test_parameter_is_a_query_parameter_and_optional(self) -> None:
        param = fields_query_parameter()
        assert param.location == OpenApiParameter.QUERY
        assert param.required is False

    def test_custom_description_is_used(self) -> None:
        param = fields_query_parameter(description="custom")
        assert param.description == "custom"

    def test_default_description_mentions_nesting_and_exclusion(self) -> None:
        param = fields_query_parameter()
        assert "nested" in param.description
        assert "exclusion" in param.description


class _AutoSchemaArticleViewSet(ArticleViewSet):
    schema = PartialResponseAutoSchema()


class TestSchemaGeneration:
    def test_generated_schema_includes_fields_parameter_for_article_list(self) -> None:
        router = DefaultRouter()
        router.register("articles", _AutoSchemaArticleViewSet, basename="schema-article")
        generator = SchemaGenerator(patterns=router.urls)
        schema = generator.get_schema(request=None, public=True)
        list_operation = schema["paths"]["/articles/"]["get"]
        param_names = {p["name"] for p in list_operation.get("parameters", [])}
        assert get_setting("QUERY_PARAM") in param_names

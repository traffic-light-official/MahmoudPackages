"""Tests for the tool registry and expose_as_tool decorator."""

from __future__ import annotations

import pytest
from rest_framework import viewsets
from rest_framework.decorators import action

from drf_llm_gateway.exceptions import ToolRegistrationError
from drf_llm_gateway.registry import ToolDefinition, ToolRegistry, expose_as_tool
from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer

pytestmark = pytest.mark.django_db


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="foo",
            description="Foo.",
            viewset_class=object,
            action="list",
            http_method="GET",
            detail=False,
            lookup_field="pk",
            serializer_class=None,
        )
        registry.register(tool)
        assert registry.get("foo") is tool
        assert len(registry) == 1
        assert "foo" in registry

    def test_duplicate_name_raises(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="foo",
            description="",
            viewset_class=object,
            action="list",
            http_method="GET",
            detail=False,
            lookup_field="pk",
            serializer_class=None,
        )
        registry.register(tool)
        with pytest.raises(ToolRegistrationError):
            registry.register(tool)

    def test_unregister(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="foo",
            description="",
            viewset_class=object,
            action="list",
            http_method="GET",
            detail=False,
            lookup_field="pk",
            serializer_class=None,
        )
        registry.register(tool)
        registry.unregister("foo")
        assert registry.get("foo") is None

    def test_get_missing_returns_none(self) -> None:
        assert ToolRegistry().get("missing") is None

    def test_clear(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="foo",
                description="",
                viewset_class=object,
                action="list",
                http_method="GET",
                detail=False,
                lookup_field="pk",
                serializer_class=None,
            )
        )
        registry.clear()
        assert len(registry) == 0


class TestExposeAsTool:
    def test_default_name_and_description(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["list"], registry=registry)
        class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_list")
        assert tool is not None
        assert tool.description == "List Article objects."
        assert tool.http_method == "GET"
        assert tool.detail is False

    def test_custom_name_prefix(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["list"], name_prefix="blog", registry=registry)
        class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        assert registry.get("blog_list") is not None

    def test_detail_actions_are_flagged(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["retrieve", "destroy"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        assert registry.get("article_retrieve").detail is True
        assert registry.get("article_destroy").detail is True

    def test_lookup_field_type_is_integer_for_default_pk(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["retrieve"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        schema = registry.get("article_retrieve").input_json_schema()
        assert schema["properties"]["pk"] == {"type": "integer"}

    def test_lookup_field_type_is_string_for_slug_lookup(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["retrieve"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer
            lookup_field = "title"  # not a real slug field, but a CharField works the same way

        schema = registry.get("article_retrieve").input_json_schema()
        assert schema["properties"]["title"] == {"type": "string"}

    def test_lookup_field_defaults_to_integer_when_model_unknown(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["retrieve"], registry=registry)
        class NoQuerysetViewSet(viewsets.ModelViewSet):
            serializer_class = ArticleSerializer

            def get_queryset(self) -> object:
                return Article.objects.all()

        schema = registry.get("no_queryset_retrieve").input_json_schema()
        assert schema["properties"]["pk"] == {"type": "integer"}

    def test_serializer_class_is_none_for_destroy(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["destroy"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_destroy")
        # Even though serializer_class is set on the viewset, destroy's
        # input schema should have no body fields - only the lookup key.
        assert tool.input_json_schema()["properties"].keys() == {"pk"}

    def test_partial_update_has_no_required_body_fields(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["partial_update"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_partial_update")
        schema = tool.input_json_schema()
        assert schema["required"] == ["pk"]  # only the lookup key, never body fields

    def test_update_requires_body_fields(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["update"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_update")
        required = set(tool.input_json_schema()["required"])
        assert "title" in required
        assert "pk" in required

    def test_examples_are_attached(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(
            actions=["create"],
            examples={"create": [{"title": "Hello", "author": 1}]},
            registry=registry,
        )
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_create")
        assert tool.examples == ({"title": "Hello", "author": 1},)
        assert tool.input_json_schema()["examples"] == [{"title": "Hello", "author": 1}]

    def test_custom_action_is_resolved_via_mapping(self) -> None:
        registry = ToolRegistry()

        @expose_as_tool(actions=["publish"], registry=registry)
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

            @action(detail=True, methods=["post"])
            def publish(self, request: object, pk: int | None = None) -> None:
                pass

        tool = registry.get("article_publish")
        assert tool.http_method == "POST"
        assert tool.detail is True

    def test_unknown_action_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolRegistrationError):

            @expose_as_tool(actions=["does_not_exist"], registry=registry)
            class ArticleViewSet(viewsets.ModelViewSet):
                queryset = Article.objects.all()
                serializer_class = ArticleSerializer

    def test_non_viewset_class_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolRegistrationError):

            @expose_as_tool(actions=["list"], registry=registry)
            class NotAViewSet:
                pass

    def test_permission_and_authentication_classes_are_captured(self) -> None:
        from rest_framework.permissions import IsAuthenticated

        registry = ToolRegistry()

        @expose_as_tool(actions=["list"], registry=registry)
        class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer
            permission_classes = [IsAuthenticated]

        assert registry.get("article_list").permission_classes == (IsAuthenticated,)

    def test_schema_hash_reflects_live_serializer_changes(self) -> None:
        """Because ToolDefinition stores a class reference (not a frozen
        schema), editing the serializer class changes the hash on the
        next call - there is no separate "resync" step."""
        from rest_framework import serializers as drf_serializers

        registry = ToolRegistry()

        class DynamicSerializer(drf_serializers.Serializer):
            title = drf_serializers.CharField()

        @expose_as_tool(
            actions=["create"],
            serializer_classes={"create": DynamicSerializer},
            registry=registry,
        )
        class ArticleViewSet(viewsets.ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

        tool = registry.get("article_create")
        original_hash = tool.schema_hash

        DynamicSerializer._declared_fields["extra"] = drf_serializers.CharField(required=False)
        new_hash = tool.schema_hash
        assert new_hash != original_hash

"""Tests for JSON Schema generation from DRF serializers."""

from __future__ import annotations

import pytest
from rest_framework import serializers

from drf_llm_gateway.exceptions import SchemaGenerationError
from drf_llm_gateway.schema import serializer_to_json_schema
from tests.test_app.models import Author, Tag
from tests.test_app.serializers import ArticleSerializer, AuthorSerializer, TagSerializer

pytestmark = pytest.mark.django_db


class TestBasicTypes:
    def test_char_field(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField()

        schema = serializer_to_json_schema(S)
        assert schema["properties"]["name"] == {"type": "string"}

    def test_integer_field(self) -> None:
        class S(serializers.Serializer):
            count = serializers.IntegerField()

        schema = serializer_to_json_schema(S)
        assert schema["properties"]["count"] == {"type": "integer"}

    def test_float_field(self) -> None:
        class S(serializers.Serializer):
            ratio = serializers.FloatField()

        assert serializer_to_json_schema(S)["properties"]["ratio"] == {"type": "number"}

    def test_boolean_field(self) -> None:
        class S(serializers.Serializer):
            active = serializers.BooleanField()

        assert serializer_to_json_schema(S)["properties"]["active"] == {"type": "boolean"}

    def test_decimal_field(self) -> None:
        class S(serializers.Serializer):
            price = serializers.DecimalField(max_digits=10, decimal_places=2)

        assert serializer_to_json_schema(S)["properties"]["price"] == {
            "type": "string",
            "format": "decimal",
        }

    def test_email_field(self) -> None:
        class S(serializers.Serializer):
            email = serializers.EmailField()

        assert serializer_to_json_schema(S)["properties"]["email"] == {
            "type": "string",
            "format": "email",
        }

    def test_url_field(self) -> None:
        class S(serializers.Serializer):
            homepage = serializers.URLField()

        assert serializer_to_json_schema(S)["properties"]["homepage"] == {
            "type": "string",
            "format": "uri",
        }

    def test_uuid_field(self) -> None:
        class S(serializers.Serializer):
            token = serializers.UUIDField()

        assert serializer_to_json_schema(S)["properties"]["token"] == {
            "type": "string",
            "format": "uuid",
        }

    def test_datetime_field(self) -> None:
        class S(serializers.Serializer):
            created_at = serializers.DateTimeField()

        assert serializer_to_json_schema(S)["properties"]["created_at"] == {
            "type": "string",
            "format": "date-time",
        }

    def test_date_field(self) -> None:
        class S(serializers.Serializer):
            day = serializers.DateField()

        assert serializer_to_json_schema(S)["properties"]["day"] == {
            "type": "string",
            "format": "date",
        }


class TestChoiceFields:
    def test_string_choice_field(self) -> None:
        class S(serializers.Serializer):
            status = serializers.ChoiceField(choices=["draft", "published"])

        schema = serializer_to_json_schema(S)["properties"]["status"]
        assert schema == {"type": "string", "enum": ["draft", "published"]}

    def test_integer_choice_field(self) -> None:
        class S(serializers.Serializer):
            priority = serializers.ChoiceField(choices=[1, 2, 3])

        schema = serializer_to_json_schema(S)["properties"]["priority"]
        assert schema == {"type": "integer", "enum": [1, 2, 3]}

    def test_multiple_choice_field(self) -> None:
        class S(serializers.Serializer):
            labels = serializers.MultipleChoiceField(choices=["a", "b", "c"])

        schema = serializer_to_json_schema(S)["properties"]["labels"]
        assert schema["type"] == "array"
        assert schema["items"] == {"type": "string", "enum": ["a", "b", "c"]}

    def test_too_many_choices_falls_back_to_plain_string(self) -> None:
        from django.test import override_settings

        class S(serializers.Serializer):
            code = serializers.ChoiceField(choices=[str(i) for i in range(10)])

        with override_settings(LLM_GATEWAY={"MAX_ENUM_VALUES": 5}):
            schema = serializer_to_json_schema(S)["properties"]["code"]
        assert schema["type"] == "string"
        assert "enum" not in schema


class TestNesting:
    def test_nested_serializer(self) -> None:
        class Inner(serializers.Serializer):
            city = serializers.CharField()

        class Outer(serializers.Serializer):
            address = Inner()

        schema = serializer_to_json_schema(Outer)
        assert schema["properties"]["address"] == {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        }

    def test_nested_list_serializer(self) -> None:
        class Inner(serializers.Serializer):
            label = serializers.CharField()

        class Outer(serializers.Serializer):
            tags = Inner(many=True)

        schema = serializer_to_json_schema(Outer)
        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["tags"]["items"]["properties"] == {"label": {"type": "string"}}

    def test_real_article_serializer_has_expected_shape(self) -> None:
        schema = serializer_to_json_schema(ArticleSerializer, mode="input")
        assert schema["properties"]["title"] == {"type": "string"}
        assert schema["properties"]["author"] == {"type": "integer"}
        assert schema["properties"]["tags"] == {"type": "array", "items": {"type": "integer"}}
        assert "id" not in schema["properties"]  # read-only in input mode
        assert "view_count" not in schema["properties"]
        assert "title" in schema["required"]

    def test_max_schema_depth_is_enforced(self) -> None:
        from django.test import override_settings

        class Level3(serializers.Serializer):
            value = serializers.CharField()

        class Level2(serializers.Serializer):
            level3 = Level3()

        class Level1(serializers.Serializer):
            level2 = Level2()

        with (
            override_settings(LLM_GATEWAY={"MAX_SCHEMA_DEPTH": 2}),
            pytest.raises(SchemaGenerationError),
        ):
            serializer_to_json_schema(Level1)


class TestListField:
    def test_list_field_with_char_child(self) -> None:
        class S(serializers.Serializer):
            labels = serializers.ListField(child=serializers.CharField())

        schema = serializer_to_json_schema(S)["properties"]["labels"]
        assert schema == {"type": "array", "items": {"type": "string"}}

    def test_list_field_without_child_has_empty_items_schema(self) -> None:
        class S(serializers.Serializer):
            values = serializers.ListField()

        schema = serializer_to_json_schema(S)["properties"]["values"]
        assert schema == {"type": "array", "items": {}}


class TestNotASerializerInput:
    def test_passing_a_plain_field_raises(self) -> None:
        from drf_llm_gateway.schema import _serializer_to_schema

        with pytest.raises(SchemaGenerationError):
            _serializer_to_schema(serializers.CharField(), mode="input", depth=1)


class TestRelatedFields:
    def test_primary_key_related_field_integer_pk(self, db: None) -> None:
        class S(serializers.Serializer):
            author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())

        assert serializer_to_json_schema(S)["properties"]["author"] == {"type": "integer"}

    def test_slug_related_field(self, db: None) -> None:
        class S(serializers.Serializer):
            tag = serializers.SlugRelatedField(slug_field="label", queryset=Tag.objects.all())

        assert serializer_to_json_schema(S)["properties"]["tag"] == {"type": "string"}

    def test_string_related_field(self) -> None:
        class S(serializers.Serializer):
            author = serializers.StringRelatedField()

        # StringRelatedField is inherently read-only (it has no reverse
        # mapping from string back to object), so it only appears in
        # "output" mode.
        schema = serializer_to_json_schema(S, mode="output")
        assert schema["properties"]["author"] == {"type": "string", "readOnly": True}

    def test_many_related_field_is_an_array(self, db: None) -> None:
        class S(serializers.Serializer):
            tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())

        schema = serializer_to_json_schema(S)["properties"]["tags"]
        assert schema == {"type": "array", "items": {"type": "integer"}}

    def test_hyperlinked_related_field(self) -> None:
        class S(serializers.Serializer):
            author = serializers.HyperlinkedRelatedField(view_name="author-detail", read_only=True)

        schema = serializer_to_json_schema(S, mode="output")["properties"]["author"]
        assert schema == {"type": "string", "format": "uri", "readOnly": True}

    def test_primary_key_related_field_without_queryset_defaults_to_integer(self) -> None:
        class S(serializers.Serializer):
            author = serializers.PrimaryKeyRelatedField(read_only=True)

        schema = serializer_to_json_schema(S, mode="output")["properties"]["author"]
        assert schema["type"] == "integer"


class TestModesAndFlags:
    def test_input_mode_excludes_read_only_fields(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField()
            computed = serializers.SerializerMethodField()

        schema = serializer_to_json_schema(S, mode="input")
        assert "computed" not in schema["properties"]

    def test_output_mode_includes_read_only_fields_marked(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField()
            id = serializers.IntegerField(read_only=True)

        schema = serializer_to_json_schema(S, mode="output")
        assert schema["properties"]["id"]["readOnly"] is True

    def test_invalid_mode_raises(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField()

        with pytest.raises(SchemaGenerationError):
            serializer_to_json_schema(S, mode="bogus")

    def test_required_field_is_listed(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField(required=True)
            nickname = serializers.CharField(required=False)

        schema = serializer_to_json_schema(S)
        assert schema["required"] == ["name"]

    def test_help_text_becomes_description(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField(help_text="The person's full name.")

        assert serializer_to_json_schema(S)["properties"]["name"]["description"] == (
            "The person's full name."
        )

    def test_nullable_field_gets_null_in_type_array(self) -> None:
        class S(serializers.Serializer):
            nickname = serializers.CharField(allow_null=True, required=False)

        schema = serializer_to_json_schema(S)["properties"]["nickname"]
        assert schema["type"] == ["string", "null"]

    def test_default_value_is_included(self) -> None:
        class S(serializers.Serializer):
            count = serializers.IntegerField(default=0)

        assert serializer_to_json_schema(S)["properties"]["count"]["default"] == 0

    def test_file_field_is_excluded(self) -> None:
        class S(serializers.Serializer):
            name = serializers.CharField()
            avatar = serializers.FileField(required=False)

        schema = serializer_to_json_schema(S)
        assert "avatar" not in schema["properties"]

    def test_accepts_instance_as_well_as_class(self) -> None:
        instance = AuthorSerializer()
        schema = serializer_to_json_schema(instance)
        assert set(schema["properties"]) == {"name", "email"}

    def test_tag_serializer_end_to_end(self, db: None) -> None:
        schema = serializer_to_json_schema(TagSerializer)
        assert schema["properties"]["label"] == {"type": "string"}

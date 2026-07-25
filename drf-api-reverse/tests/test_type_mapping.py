"""Tests for :mod:`drf_api_reverse.type_mapping`."""

from __future__ import annotations

from drf_api_reverse.type_mapping import field_spec, ref_target


class TestRefTarget:
    def test_returns_component_name_for_a_ref(self) -> None:
        assert ref_target({"$ref": "#/components/schemas/Article"}) == "Article"

    def test_returns_none_for_a_non_ref(self) -> None:
        assert ref_target({"type": "string"}) is None

    def test_returns_none_for_an_external_ref(self) -> None:
        assert ref_target({"$ref": "other-file.yml#/Article"}) is None


class TestFieldSpecPrimitives:
    def test_plain_string_maps_to_char_field(self) -> None:
        spec = field_spec({"type": "string"}, required=True)
        assert spec.expression == "serializers.CharField()"
        assert spec.ref is None

    def test_optional_field_gets_required_false(self) -> None:
        spec = field_spec({"type": "string"}, required=False)
        assert spec.expression == "serializers.CharField(required=False)"

    def test_string_with_max_length(self) -> None:
        spec = field_spec({"type": "string", "maxLength": 255}, required=True)
        assert spec.expression == "serializers.CharField(max_length=255)"

    def test_integer_maps_to_integer_field(self) -> None:
        assert field_spec({"type": "integer"}, required=True).expression == (
            "serializers.IntegerField()"
        )

    def test_number_maps_to_float_field(self) -> None:
        assert field_spec({"type": "number"}, required=True).expression == (
            "serializers.FloatField()"
        )

    def test_boolean_maps_to_boolean_field(self) -> None:
        assert field_spec({"type": "boolean"}, required=True).expression == (
            "serializers.BooleanField()"
        )

    def test_unrecognized_type_degrades_to_dict_field(self) -> None:
        spec = field_spec({"type": "frobnicate"}, required=True)
        assert spec.expression.startswith("serializers.DictField()")
        assert "unrecognized type 'frobnicate'" in spec.expression


class TestFieldSpecStringFormats:
    def test_date_time_format(self) -> None:
        spec = field_spec({"type": "string", "format": "date-time"}, required=True)
        assert spec.expression == "serializers.DateTimeField()"

    def test_date_format(self) -> None:
        spec = field_spec({"type": "string", "format": "date"}, required=True)
        assert spec.expression == "serializers.DateField()"

    def test_email_format(self) -> None:
        spec = field_spec({"type": "string", "format": "email"}, required=True)
        assert spec.expression == "serializers.EmailField()"

    def test_uri_format_maps_to_url_field(self) -> None:
        spec = field_spec({"type": "string", "format": "uri"}, required=True)
        assert spec.expression == "serializers.URLField()"

    def test_uuid_format(self) -> None:
        spec = field_spec({"type": "string", "format": "uuid"}, required=True)
        assert spec.expression == "serializers.UUIDField()"

    def test_unrecognized_format_falls_back_to_char_field(self) -> None:
        spec = field_spec({"type": "string", "format": "not-a-real-format"}, required=True)
        assert spec.expression == "serializers.CharField()"


class TestFieldSpecEnum:
    def test_enum_maps_to_choice_field(self) -> None:
        spec = field_spec({"type": "string", "enum": ["draft", "published"]}, required=True)
        assert spec.expression == "serializers.ChoiceField(choices=['draft', 'published'])"

    def test_enum_values_are_safely_repr_escaped(self) -> None:
        spec = field_spec({"type": "string", "enum": ["a'b"]}, required=True)
        assert spec.expression == 'serializers.ChoiceField(choices=["a\'b"])'


class TestFieldSpecRef:
    def test_direct_ref_becomes_nested_serializer(self) -> None:
        spec = field_spec({"$ref": "#/components/schemas/Author"}, required=True)
        assert spec.expression == "AuthorSerializer()"
        assert spec.ref == "Author"

    def test_optional_ref_is_required_false(self) -> None:
        spec = field_spec({"$ref": "#/components/schemas/Author"}, required=False)
        assert spec.expression == "AuthorSerializer(required=False)"


class TestFieldSpecArray:
    def test_array_of_ref_becomes_nested_many_serializer(self) -> None:
        spec = field_spec(
            {"type": "array", "items": {"$ref": "#/components/schemas/Author"}}, required=True
        )
        assert spec.expression == "AuthorSerializer(many=True)"
        assert spec.ref == "Author"

    def test_array_of_primitives_becomes_list_field(self) -> None:
        spec = field_spec({"type": "array", "items": {"type": "string"}}, required=True)
        assert spec.expression == "serializers.ListField(child=serializers.CharField())"
        assert spec.ref is None

    def test_empty_array_items_falls_back_to_char_field_child(self) -> None:
        spec = field_spec({"type": "array", "items": {}}, required=True)
        assert spec.expression == "serializers.ListField(child=serializers.CharField())"

    def test_missing_items_key_falls_back_to_char_field_child(self) -> None:
        spec = field_spec({"type": "array"}, required=True)
        assert spec.expression == "serializers.ListField(child=serializers.CharField())"


class TestFieldSpecInlineObject:
    def test_inline_object_degrades_to_dict_field(self) -> None:
        spec = field_spec(
            {"type": "object", "properties": {"x": {"type": "string"}}}, required=True
        )
        assert spec.expression.startswith("serializers.DictField()")
        assert "inline object" in spec.expression

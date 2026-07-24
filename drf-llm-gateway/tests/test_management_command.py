"""Tests for the generate_llm_tools management command."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db


class TestGenerateLlmToolsCommand:
    def test_default_openai_format(self) -> None:
        out = StringIO()
        call_command("generate_llm_tools", stdout=out)
        payload = json.loads(out.getvalue())
        assert isinstance(payload, list)
        names = {t["function"]["name"] for t in payload}
        assert "article_list" in names

    def test_mcp_format(self) -> None:
        out = StringIO()
        call_command("generate_llm_tools", format="mcp", stdout=out)
        payload = json.loads(out.getvalue())
        names = {t["name"] for t in payload}
        assert "article_list" in names
        assert "inputSchema" in payload[0]

    def test_jsonschema_format(self) -> None:
        out = StringIO()
        call_command("generate_llm_tools", format="jsonschema", stdout=out)
        payload = json.loads(out.getvalue())
        entry = next(t for t in payload if t["name"] == "article_create")
        assert entry["schema"]["type"] == "object"
        assert "schema_hash" in entry
        assert "version" in entry

    def test_compact_indent(self) -> None:
        out = StringIO()
        call_command("generate_llm_tools", indent=0, stdout=out)
        # Compact output has no newline-indentation between top-level items.
        assert "\n  " not in out.getvalue()

    def test_no_tools_registered_raises_command_error(self) -> None:
        from drf_llm_gateway.registry import default_registry

        saved = dict(default_registry._tools)
        default_registry.clear()
        try:
            with pytest.raises(CommandError):
                call_command("generate_llm_tools", stdout=StringIO())
        finally:
            default_registry._tools.update(saved)

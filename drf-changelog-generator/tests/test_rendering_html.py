"""Tests for :mod:`drf_changelog_generator.rendering.html`."""

from __future__ import annotations

from drf_changelog_generator.changes import SchemaDiff
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.rendering.html import render_html


class TestRenderHtml:
    def test_produces_a_complete_html_document(self) -> None:
        rendered = render_html(SchemaDiff(changes=[]), old_ref="v1.0.0", new_ref="v1.1.0")

        assert rendered.startswith("<!doctype html>")
        assert "<html" in rendered
        assert "</html>" in rendered
        assert "v1.0.0" in rendered

    def test_empty_diff_shows_a_message(self) -> None:
        rendered = render_html(SchemaDiff(changes=[]), old_ref="a", new_ref="b")

        assert "No API changes detected." in rendered

    def test_escapes_untrusted_content(self) -> None:
        rendered = render_html(
            SchemaDiff(changes=[]), old_ref="<script>alert(1)</script>", new_ref="b"
        )

        assert "<script>alert(1)</script>" not in rendered
        assert "&lt;script&gt;" in rendered

    def test_includes_change_sections_for_a_rich_diff(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        rendered = render_html(diff, old_ref="v1.0.0", new_ref="v1.1.0")

        assert "Breaking Changes" in rendered
        assert "Added Endpoints" in rendered
        assert "Deprecated Endpoints" in rendered
        assert "<code>DELETE /articles/{id}/</code>" in rendered

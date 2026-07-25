"""Tests for :mod:`drf_changelog_generator.rendering.markdown`."""

from __future__ import annotations

from drf_changelog_generator.changes import Change, ChangeKind, SchemaDiff, Severity
from drf_changelog_generator.diffing.engine import diff_schemas
from drf_changelog_generator.rendering.markdown import render_markdown


class TestRenderMarkdown:
    def test_empty_diff(self) -> None:
        rendered = render_markdown(SchemaDiff(changes=[]), old_ref="v1.0.0", new_ref="v1.1.0")

        assert "No API changes detected." in rendered
        assert "v1.0.0" in rendered
        assert "v1.1.0" in rendered

    def test_includes_every_section_for_a_rich_diff(
        self, old_schema: dict, new_schema: dict
    ) -> None:
        diff = diff_schemas(old_schema, new_schema)

        rendered = render_markdown(diff, old_ref="v1.0.0", new_ref="v1.1.0")

        assert "## Breaking Changes" in rendered
        assert "## Removed Endpoints" in rendered
        assert "## Deprecated Endpoints" in rendered
        assert "## Added Endpoints" in rendered
        assert "## Non-Breaking Changes" in rendered
        assert "`DELETE /articles/{id}/`" in rendered
        assert "`GET /articles/{id}/comments/`" in rendered

    def test_omits_empty_sections(self) -> None:
        diff = SchemaDiff(
            changes=[
                Change(
                    kind=ChangeKind.ENDPOINT_ADDED,
                    severity=Severity.NON_BREAKING,
                    path="/x/",
                    method="get",
                    location="",
                    message="Added GET /x/",
                )
            ]
        )

        rendered = render_markdown(diff, old_ref="a", new_ref="b")

        assert "## Added Endpoints" in rendered
        assert "## Breaking Changes" not in rendered
        assert "## Removed Endpoints" not in rendered
        assert "## Deprecated Endpoints" not in rendered
        assert "## Non-Breaking Changes" not in rendered

    def test_ends_with_a_trailing_newline(self) -> None:
        rendered = render_markdown(SchemaDiff(changes=[]), old_ref="a", new_ref="b")

        assert rendered.endswith("\n")
        assert not rendered.endswith("\n\n")

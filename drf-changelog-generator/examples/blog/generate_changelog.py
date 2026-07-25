"""Example: diff the two schemas in this directory and print a Markdown changelog.

Run with:

    python -m examples.blog.generate_changelog
"""

from __future__ import annotations

from pathlib import Path

from drf_changelog_generator import diff_schemas, load_schema_file, render_markdown

HERE = Path(__file__).parent


def main() -> None:
    """Diff ``schema-v1.yml`` against ``schema-v2.yml`` and print the changelog."""
    old = load_schema_file(HERE / "schema-v1.yml")
    new = load_schema_file(HERE / "schema-v2.yml")
    diff = diff_schemas(old, new)

    print(f"{len(diff.breaking_changes)} breaking change(s) detected.")
    print(render_markdown(diff, old_ref="v1", new_ref="v2"))


if __name__ == "__main__":
    main()

# API Reference

This page documents every public class, function, and exception. It is
generated in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll see
in your editor's tooltips.

## Diffing

### diff_schemas

::: drf_changelog_generator.diffing.engine.diff_schemas

### resolve_ref

::: drf_changelog_generator.diffing.refs.resolve_ref

### deref

::: drf_changelog_generator.diffing.refs.deref

## Data model

### Change

::: drf_changelog_generator.changes.Change

### ChangeKind

::: drf_changelog_generator.changes.ChangeKind

### Severity

::: drf_changelog_generator.changes.Severity

### SchemaDiff

::: drf_changelog_generator.changes.SchemaDiff

## Loading schemas

### load_schema_file

::: drf_changelog_generator.schema_loader.load_schema_file

### parse_schema

::: drf_changelog_generator.schema_loader.parse_schema

### load_schema_at_ref

::: drf_changelog_generator.git_utils.load_schema_at_ref

### show_file_at_ref

::: drf_changelog_generator.git_utils.show_file_at_ref

## Rendering

### summarize

::: drf_changelog_generator.rendering.common.summarize

### ChangeSummary

::: drf_changelog_generator.rendering.common.ChangeSummary

### render_markdown

::: drf_changelog_generator.rendering.markdown.render_markdown

### render_html

::: drf_changelog_generator.rendering.html.render_html

### render_slack_blocks

::: drf_changelog_generator.rendering.slack.render_slack_blocks

### post_to_slack_webhook

::: drf_changelog_generator.rendering.slack.post_to_slack_webhook

### render_github_release_notes

::: drf_changelog_generator.rendering.github.render_github_release_notes

## CLI

### main

::: drf_changelog_generator.cli.main

### build_parser

::: drf_changelog_generator.cli.build_parser

## Exceptions

### ChangelogGeneratorError

::: drf_changelog_generator.exceptions.ChangelogGeneratorError

### SchemaParseError

::: drf_changelog_generator.exceptions.SchemaParseError

### GitError

::: drf_changelog_generator.exceptions.GitError

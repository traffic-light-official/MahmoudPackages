# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-24

### Added

- Initial release.
- `expose_as_tool` decorator and `ToolRegistry` for registering DRF
  viewset actions as callable tools.
- Automatic JSON Schema generation from DRF serializers
  (`serializer_to_json_schema`), covering standard fields, nested
  serializers, list serializers, related fields, and choice fields.
- OpenAI function-calling export (`to_openai_tool(s)`).
- MCP tool format export (`to_mcp_tool(s)`).
- `execute_tool` runtime dispatcher with permission/authentication
  enforcement and serializer-backed argument validation.
- Content-hash based schema versioning (`ToolDefinition.schema_hash`).
- `generate_llm_tools` Django management command (CLI export).
- Full test suite across Python 3.10-3.13 and Django 4.2-5.2.

[Unreleased]: https://github.com/mahmoudgshaker/drf-llm-gateway/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mahmoudgshaker/drf-llm-gateway/releases/tag/v1.0.0

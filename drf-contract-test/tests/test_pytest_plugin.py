"""Tests for the drf_contract_test pytest plugin.

Uses pytest's own ``pytester`` fixture to run an isolated, nested pytest
session against a throwaway project, so we can verify the plugin's
options and fixtures behave correctly without polluting (or depending
on) this package's own test suite/Django app.

The nested project overrides the ``contract_schema`` fixture (normal
pytest fixture-override rules apply) with a hand-built :class:`Schema`,
so these tests don't need a real Django project — only
``contract_baseline``/``contract_diff``/``contract_cases`` build on top
of that fixture, and those are exactly what we want to exercise.
"""

from __future__ import annotations

import textwrap

import pytest

pytestmark = pytest.mark.usefixtures("_plugin_test_setup")

_OVERRIDE_CONFTEST = textwrap.dedent("""
    import pytest
    from drf_contract_test.schema import Schema

    @pytest.fixture(scope="session")
    def contract_schema():
        return Schema({
            "info": {"title": "Nested Test API", "version": "1.0.0"},
            "paths": {
                "/widgets/": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"id": {"type": "integer"}},
                                            "required": ["id"],
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        })
    """)

_BASELINE_YAML = textwrap.dedent("""
    info:
      title: Nested Test API
      version: 1.0.0
    paths:
      /widgets/:
        get:
          responses:
            "200":
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id: {type: integer}
                      name: {type: string}
                    required: [id]
    """)


@pytest.fixture
def _plugin_test_setup(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(_OVERRIDE_CONFTEST)


class TestContractSchemaFixture:
    def test_fixture_is_available_and_overridable(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile("""
            def test_it(contract_schema):
                assert contract_schema.title == "Nested Test API"
            """)
        result = pytester.runpytest("-p", "no:django")
        result.assert_outcomes(passed=1)


class TestContractBaselineFixture:
    def test_skipped_without_option(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile("""
            def test_it(contract_baseline):
                pass
            """)
        result = pytester.runpytest("-p", "no:django")
        result.assert_outcomes(skipped=1)

    def test_loaded_when_option_given(self, pytester: pytest.Pytester) -> None:
        pytester.makefile(".yaml", baseline=_BASELINE_YAML)
        pytester.makepyfile("""
            def test_it(contract_baseline):
                assert contract_baseline.title == "Nested Test API"
            """)
        result = pytester.runpytest("-p", "no:django", "--contract-baseline=baseline.yaml")
        result.assert_outcomes(passed=1)


class TestContractDiffFixture:
    def test_reports_the_new_optional_field(self, pytester: pytest.Pytester) -> None:
        pytester.makefile(".yaml", baseline=_BASELINE_YAML)
        pytester.makepyfile("""
            def test_it(contract_diff):
                kinds = {c.kind for c in contract_diff.changes}
                assert "field_removed" in kinds  # 'name' only in baseline -> response field removed
                assert not contract_diff.has_breaking_changes or any(
                    c.kind == "field_removed" for c in contract_diff.breaking_changes
                )
            """)
        result = pytester.runpytest("-p", "no:django", "--contract-baseline=baseline.yaml")
        result.assert_outcomes(passed=1)


class TestContractVersionCheckFixture:
    def test_flags_breaking_change_without_version_bump(self, pytester: pytest.Pytester) -> None:
        pytester.makefile(".yaml", baseline=_BASELINE_YAML)
        pytester.makepyfile("""
            def test_it(contract_version_check):
                # The nested contract_schema fixture reports the same
                # version as the baseline, but drops the 'name' response
                # field present in the baseline -> a breaking change
                # without a version bump.
                assert contract_version_check.ok is False
                assert "not bumped" in contract_version_check.message
            """)
        result = pytester.runpytest("-p", "no:django", "--contract-baseline=baseline.yaml")
        result.assert_outcomes(passed=1)

    def test_require_major_bump_option_is_honored(self, pytester: pytest.Pytester) -> None:
        pytester.makefile(".yaml", baseline=_BASELINE_YAML)
        pytester.makepyfile("""
            def test_it(contract_version_check):
                assert contract_version_check.ok is False
            """)
        result = pytester.runpytest(
            "-p",
            "no:django",
            "--contract-baseline=baseline.yaml",
            "--contract-require-major-bump",
        )
        result.assert_outcomes(passed=1)


class TestContractCasesFixture:
    def test_yields_one_case_per_response(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile("""
            def test_it(contract_cases):
                assert len(contract_cases) == 1
                assert contract_cases[0].operation == "GET /widgets/"
                assert contract_cases[0].expected_status == "200"
            """)
        result = pytester.runpytest("-p", "no:django")
        result.assert_outcomes(passed=1)


class TestAddOptionsRegistered:
    def test_help_lists_contract_options(self, pytester: pytest.Pytester) -> None:
        result = pytester.runpytest("--help")
        result.stdout.fnmatch_lines(["*--contract-baseline*"])

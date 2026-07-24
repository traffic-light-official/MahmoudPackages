"""pytest plugin exposing OpenAPI contract-testing fixtures and options.

Enabled automatically once the package is installed (registered via the
``pytest11`` entry point). Adds:

- ``--contract-baseline=PATH``: path to a baseline schema snapshot to
  compare the live schema against.
- ``--contract-settings=MODULE`` / ``--contract-urlconf=MODULE``: passed
  through to schema generation.
- ``--contract-require-major-bump``: passed through to
  :func:`drf_contract_test.versioning.check_version_bump`.

And fixtures:

- ``contract_schema``: the live schema generated from the current Django
  project (session-scoped).
- ``contract_baseline``: the baseline schema loaded from
  ``--contract-baseline`` (session-scoped; skips the test if the option
  wasn't given).
- ``contract_diff``: the :class:`~drf_contract_test.changes.DiffResult`
  of comparing ``contract_baseline`` against ``contract_schema``.
- ``contract_version_check``: the
  :class:`~drf_contract_test.versioning.VersionCheckResult` of enforcing
  a version bump for ``contract_diff``, honoring
  ``--contract-require-major-bump``.
- ``contract_cases``: one :class:`~drf_contract_test.generator.ContractCase`
  per documented response in ``contract_schema``, for parametrizing your
  own live-response validation tests.
"""

from __future__ import annotations

import pytest

from drf_contract_test.changes import DiffResult
from drf_contract_test.diff import compare_schemas
from drf_contract_test.generator import ContractCase, generate_contract_cases
from drf_contract_test.schema import Schema, generate_schema, load_schema_file
from drf_contract_test.versioning import VersionCheckResult, check_version_bump


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--contract-*`` command-line options."""
    group = parser.getgroup("drf-contract-test")
    group.addoption(
        "--contract-baseline",
        action="store",
        default=None,
        help="Path to a baseline OpenAPI schema snapshot to compare the live schema against.",
    )
    group.addoption(
        "--contract-settings",
        action="store",
        default=None,
        help="Dotted path to the Django settings module (if not already configured).",
    )
    group.addoption(
        "--contract-urlconf",
        action="store",
        default=None,
        help="Dotted path to the URLconf module to generate the schema from.",
    )
    group.addoption(
        "--contract-require-major-bump",
        action="store_true",
        default=False,
        help="Require the major version component to increase when breaking changes are present.",
    )


@pytest.fixture(scope="session")
def contract_schema(pytestconfig: pytest.Config) -> Schema:
    """The live OpenAPI schema generated from the current Django project."""
    return generate_schema(
        settings_module=pytestconfig.getoption("--contract-settings"),
        urlconf=pytestconfig.getoption("--contract-urlconf"),
    )


@pytest.fixture(scope="session")
def contract_baseline(pytestconfig: pytest.Config) -> Schema:
    """The baseline schema loaded from ``--contract-baseline``.

    Skips the requesting test if the option wasn't passed.
    """
    baseline_path = pytestconfig.getoption("--contract-baseline")
    if not baseline_path:
        pytest.skip("--contract-baseline was not given; skipping baseline-comparison test.")
    return load_schema_file(baseline_path)


@pytest.fixture(scope="session")
def contract_diff(contract_baseline: Schema, contract_schema: Schema) -> DiffResult:
    """The result of comparing ``contract_baseline`` against ``contract_schema``."""
    return compare_schemas(contract_baseline, contract_schema)


@pytest.fixture(scope="session")
def contract_version_check(
    pytestconfig: pytest.Config,
    contract_baseline: Schema,
    contract_schema: Schema,
    contract_diff: DiffResult,
) -> VersionCheckResult:
    """Whether a version bump was made alongside any breaking changes in ``contract_diff``.

    Honors ``--contract-require-major-bump``. Use this in an assertion,
    e.g.::

        def test_version_bumped_for_breaking_changes(contract_version_check):
            assert contract_version_check.ok, contract_version_check.message
    """
    return check_version_bump(
        contract_baseline,
        contract_schema,
        contract_diff,
        require_major_bump=pytestconfig.getoption("--contract-require-major-bump"),
    )


@pytest.fixture(scope="session")
def contract_cases(contract_schema: Schema) -> list[ContractCase]:
    """One :class:`~drf_contract_test.generator.ContractCase` per documented response.

    Useful for parametrizing your own tests that call each endpoint and
    validate the real response against what's documented, e.g.::

        def test_responses_match_contract(contract_cases, api_client):
            for case in contract_cases:
                ...  # call case.method/case.path with api_client, then
                ...  # validate_response_against_schema(case, ...)
    """
    return generate_contract_cases(contract_schema)

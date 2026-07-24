"""A pytest module validating live responses against their documented contract.

Copy this pattern into your own project's test suite (it needs a real
Django project and database, so it's not runnable standalone). Requires
``pytest-django``.

Usage:
    DJANGO_SETTINGS_MODULE=myproject.settings pytest examples/validate_live_responses.py
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from drf_contract_test import (
    generate_contract_cases,
    generate_schema,
    validate_response_against_schema,
)
from drf_contract_test.generator import ContractCase

_schema = generate_schema()
_cases = generate_contract_cases(_schema, statuses={"200", "201"})


@pytest.mark.django_db
@pytest.mark.parametrize("case", _cases, ids=lambda c: c.operation)
def test_response_matches_documented_contract(case: ContractCase) -> None:
    client = APIClient()
    response = getattr(client, case.method.lower())(case.path)
    violations = validate_response_against_schema(
        case, status_code=response.status_code, data=response.json(), root=_schema.raw
    )
    assert not violations, violations

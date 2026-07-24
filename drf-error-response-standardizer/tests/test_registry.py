"""Tests for :mod:`drf_error_response_standardizer.registry`."""

from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions

from drf_error_response_standardizer.codes import ErrorType
from drf_error_response_standardizer.problem import ProblemDetail
from drf_error_response_standardizer.registry import (
    ProblemRegistry,
    default_registry,
    register,
    register_builder,
)


class DomainError(Exception):
    pass


class SpecificDomainError(DomainError):
    pass


class UnrelatedError(Exception):
    pass


@pytest.fixture
def registry() -> ProblemRegistry:
    return ProblemRegistry()


class TestRegisterAndFindErrorType:
    def test_find_error_type_returns_none_when_nothing_registered(
        self, registry: ProblemRegistry
    ) -> None:
        assert registry.find_error_type(UnrelatedError()) is None

    def test_find_error_type_matches_exact_class(self, registry: ProblemRegistry) -> None:
        error_type = ErrorType(
            code="domain_error", title="Domain Error", slug="domain-error", status=422
        )
        registry.register(DomainError, error_type)

        assert registry.find_error_type(DomainError()) is error_type

    def test_find_error_type_matches_via_subclass_mro(self, registry: ProblemRegistry) -> None:
        error_type = ErrorType(
            code="domain_error", title="Domain Error", slug="domain-error", status=422
        )
        registry.register(DomainError, error_type)

        assert registry.find_error_type(SpecificDomainError()) is error_type

    def test_more_specific_registration_wins_over_base_class(
        self, registry: ProblemRegistry
    ) -> None:
        base_type = ErrorType(
            code="domain_error", title="Domain Error", slug="domain-error", status=422
        )
        specific_type = ErrorType(
            code="specific_domain_error", title="Specific", slug="specific-domain-error", status=409
        )
        registry.register(DomainError, base_type)
        registry.register(SpecificDomainError, specific_type)

        assert registry.find_error_type(SpecificDomainError()) is specific_type
        assert registry.find_error_type(DomainError()) is base_type

    def test_unregister_removes_the_mapping(self, registry: ProblemRegistry) -> None:
        error_type = ErrorType(
            code="domain_error", title="Domain Error", slug="domain-error", status=422
        )
        registry.register(DomainError, error_type)

        registry.unregister(DomainError)

        assert registry.find_error_type(DomainError()) is None


class TestRegisterBuilder:
    def test_find_builder_returns_none_when_nothing_registered(
        self, registry: ProblemRegistry
    ) -> None:
        assert registry.find_builder(UnrelatedError()) is None

    def test_find_builder_invokes_and_returns_registered_callable(
        self, registry: ProblemRegistry
    ) -> None:
        def builder(exc: Exception) -> ProblemDetail:
            return ProblemDetail(status=418, title="I'm a teapot", detail=str(exc))

        registry.register_builder(DomainError, builder)

        found = registry.find_builder(DomainError("brewing"))
        assert found is builder
        assert found(DomainError("brewing")).status == 418

    def test_find_builder_matches_via_subclass_mro(self, registry: ProblemRegistry) -> None:
        def builder(exc: Exception) -> ProblemDetail:
            return ProblemDetail(status=418, title="I'm a teapot")

        registry.register_builder(DomainError, builder)

        assert registry.find_builder(SpecificDomainError()) is builder

    def test_unregister_removes_the_builder(self, registry: ProblemRegistry) -> None:
        def builder(exc: Exception) -> ProblemDetail:
            return ProblemDetail(status=418, title="I'm a teapot")

        registry.register_builder(DomainError, builder)
        registry.unregister(DomainError)

        assert registry.find_builder(DomainError()) is None


class TestAllErrorTypes:
    def test_returns_empty_list_for_empty_registry(self, registry: ProblemRegistry) -> None:
        assert registry.all_error_types() == []

    def test_deduplicates_by_code(self, registry: ProblemRegistry) -> None:
        error_type = ErrorType(
            code="domain_error", title="Domain Error", slug="domain-error", status=422
        )
        registry.register(DomainError, error_type)
        registry.register(SpecificDomainError, error_type)

        assert registry.all_error_types() == [error_type]

    def test_returns_every_distinct_error_type(self, registry: ProblemRegistry) -> None:
        first = ErrorType(code="a", title="A", slug="a", status=400)
        second = ErrorType(code="b", title="B", slug="b", status=409)
        registry.register(DomainError, first)
        registry.register(UnrelatedError, second)

        assert {e.code for e in registry.all_error_types()} == {"a", "b"}


class TestDefaultRegistry:
    @pytest.mark.parametrize(
        ("exc", "expected_code"),
        [
            (drf_exceptions.ParseError(), "parse_error"),
            (drf_exceptions.NotAuthenticated(), "not_authenticated"),
            (drf_exceptions.AuthenticationFailed(), "authentication_failed"),
            (drf_exceptions.PermissionDenied(), "permission_denied"),
            (DjangoPermissionDenied(), "permission_denied"),
            (drf_exceptions.NotFound(), "not_found"),
            (Http404(), "not_found"),
            (drf_exceptions.MethodNotAllowed("POST"), "method_not_allowed"),
            (drf_exceptions.NotAcceptable(), "not_acceptable"),
            (drf_exceptions.UnsupportedMediaType("text/plain"), "unsupported_media_type"),
            (drf_exceptions.Throttled(), "throttled"),
            (drf_exceptions.ValidationError("bad"), "validation_error"),
        ],
    )
    def test_builtin_drf_and_django_exceptions_are_preregistered(
        self, exc: Exception, expected_code: str
    ) -> None:
        error_type = default_registry.find_error_type(exc)

        assert error_type is not None
        assert error_type.code == expected_code

    def test_module_level_register_writes_to_default_registry(self) -> None:
        class _ModuleLevelDomainError(Exception):
            pass

        error_type = ErrorType(
            code="module_level", title="Module Level", slug="module-level", status=400
        )
        register(_ModuleLevelDomainError, error_type)

        try:
            assert default_registry.find_error_type(_ModuleLevelDomainError()) is error_type
        finally:
            default_registry.unregister(_ModuleLevelDomainError)

    def test_module_level_register_builder_writes_to_default_registry(self) -> None:
        class _ModuleLevelBuiltError(Exception):
            pass

        def builder(exc: Exception) -> ProblemDetail:
            return ProblemDetail(status=418, title="I'm a teapot")

        register_builder(_ModuleLevelBuiltError, builder)

        try:
            assert default_registry.find_builder(_ModuleLevelBuiltError()) is builder
        finally:
            default_registry.unregister(_ModuleLevelBuiltError)

"""Tests for :mod:`drf_n_plus_one_query_guard.fingerprint`."""

from __future__ import annotations

from drf_n_plus_one_query_guard.fingerprint import normalize_sql


class TestNormalizeSql:
    def test_collapses_internal_whitespace(self) -> None:
        assert normalize_sql("SELECT  *   FROM  t") == "SELECT * FROM t"

    def test_collapses_newlines_and_tabs(self) -> None:
        assert normalize_sql("SELECT *\nFROM t\n\tWHERE x = %s") == "SELECT * FROM t WHERE x = %s"

    def test_strips_leading_and_trailing_whitespace(self) -> None:
        assert normalize_sql("  SELECT 1  ") == "SELECT 1"

    def test_two_parameterized_queries_with_different_values_fingerprint_alike(self) -> None:
        query_a = "SELECT * FROM t WHERE id = %s"
        query_b = "SELECT * FROM t WHERE id = %s"
        assert normalize_sql(query_a) == normalize_sql(query_b)

    def test_already_normalized_text_is_unchanged(self) -> None:
        sql = "SELECT * FROM t WHERE id = %s"
        assert normalize_sql(sql) == sql

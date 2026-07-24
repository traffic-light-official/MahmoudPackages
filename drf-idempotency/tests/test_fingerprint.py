"""Unit tests for request fingerprinting."""

from __future__ import annotations

from rest_framework.test import APIRequestFactory

from drf_idempotency.fingerprint import compute_fingerprint

factory = APIRequestFactory()


class TestComputeFingerprint:
    def test_identical_requests_produce_identical_fingerprints(self) -> None:
        r1 = factory.post("/payments/", data={"amount": 100}, format="json")
        r2 = factory.post("/payments/", data={"amount": 100}, format="json")
        assert compute_fingerprint(r1) == compute_fingerprint(r2)

    def test_different_bodies_produce_different_fingerprints(self) -> None:
        r1 = factory.post("/payments/", data={"amount": 100}, format="json")
        r2 = factory.post("/payments/", data={"amount": 200}, format="json")
        assert compute_fingerprint(r1) != compute_fingerprint(r2)

    def test_different_paths_produce_different_fingerprints(self) -> None:
        r1 = factory.post("/payments/", data={"amount": 100}, format="json")
        r2 = factory.post("/refunds/", data={"amount": 100}, format="json")
        assert compute_fingerprint(r1) != compute_fingerprint(r2)

    def test_different_methods_produce_different_fingerprints(self) -> None:
        r1 = factory.post("/payments/", data={"amount": 100}, format="json")
        r2 = factory.put("/payments/", data={"amount": 100}, format="json")
        assert compute_fingerprint(r1) != compute_fingerprint(r2)

    def test_returns_a_64_character_hex_digest(self) -> None:
        r1 = factory.post("/payments/", data={"amount": 100}, format="json")
        digest = compute_fingerprint(r1)
        assert len(digest) == 64
        int(digest, 16)

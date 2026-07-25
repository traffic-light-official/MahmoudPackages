"""Tests for :mod:`drf_notification.url_safety`.

Uses an injected ``resolver`` throughout so these tests never perform
real DNS lookups (fast, deterministic, and safe to run offline/in CI).
"""

from __future__ import annotations

import pytest

from drf_notification.url_safety import Resolver, UnsafeWebhookUrlError, validate_public_url


def _resolver_returning(*ips: str) -> Resolver:
    def resolver(host: str) -> list[str]:
        del host
        return list(ips)

    return resolver


class TestValidatePublicUrl:
    def test_accepts_a_host_resolving_to_a_public_ip(self) -> None:
        validate_public_url(
            "https://example.com/webhook", resolver=_resolver_returning("93.184.216.34")
        )

    def test_rejects_localhost_by_name_without_resolving(self) -> None:
        def resolver(host: str) -> list[str]:
            raise AssertionError("localhost should be rejected before resolution is attempted")

        with pytest.raises(UnsafeWebhookUrlError):
            validate_public_url("http://localhost/webhook", resolver=resolver)

    def test_rejects_loopback_ip(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="disallowed address"):
            validate_public_url(
                "http://example.com/webhook", resolver=_resolver_returning("127.0.0.1")
            )

    def test_rejects_private_ip(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="disallowed address"):
            validate_public_url(
                "http://example.com/webhook", resolver=_resolver_returning("10.0.0.5")
            )

    def test_rejects_link_local_cloud_metadata_ip(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="disallowed address"):
            validate_public_url(
                "http://example.com/latest/meta-data/",
                resolver=_resolver_returning("169.254.169.254"),
            )

    def test_rejects_reserved_ip(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="disallowed address"):
            validate_public_url(
                "http://example.com/webhook", resolver=_resolver_returning("240.0.0.1")
            )

    def test_rejects_multicast_ip(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="disallowed address"):
            validate_public_url(
                "http://example.com/webhook", resolver=_resolver_returning("224.0.0.1")
            )

    def test_rejects_url_with_no_host(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="no host"):
            validate_public_url("not-a-url")

    def test_wraps_resolution_failure(self) -> None:
        def resolver(host: str) -> list[str]:
            raise OSError("name resolution failed")

        with pytest.raises(UnsafeWebhookUrlError, match="Could not resolve"):
            validate_public_url("http://example.com/webhook", resolver=resolver)

    def test_uses_real_dns_by_default(self) -> None:
        with pytest.raises(UnsafeWebhookUrlError, match="Could not resolve"):
            validate_public_url("http://this-host-should-never-resolve.invalid/webhook")

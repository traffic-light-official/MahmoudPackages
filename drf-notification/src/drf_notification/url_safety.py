"""Best-effort SSRF guard for user-supplied webhook URLs.

This blocks the most common accidental or malicious targets (localhost,
private/link-local IP ranges, cloud metadata endpoints) by resolving the
hostname and inspecting the resulting IP addresses. It is **not** a
complete SSRF defense: DNS can be re-pointed after this check runs
(a time-of-check/time-of-use gap), and it does not protect against
redirects. Projects accepting webhook URLs from lower-trust users should
also enforce network-level egress controls (a proxy/allowlist) - see
``docs/security.md``.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlparse

_BLOCKED_HOSTNAMES = frozenset({"localhost", "metadata.google.internal"})

#: Signature of a hostname resolver: takes a hostname, returns the IP
#: address strings it resolves to. Overridable via :func:`validate_public_url`'s
#: ``resolver`` argument for deterministic, network-free testing.
Resolver = Callable[[str], list[str]]


class UnsafeWebhookUrlError(ValueError):
    """Raised when a webhook URL resolves to a disallowed host or address."""


def _default_resolver(host: str) -> list[str]:
    return [str(info[4][0]) for info in socket.getaddrinfo(host, None)]


def validate_public_url(url: str, *, resolver: Resolver | None = None) -> None:
    """Raise :class:`UnsafeWebhookUrlError` if ``url`` looks unsafe to POST to.

    Args:
        url: The candidate webhook URL.
        resolver: Hostname-to-IP-addresses resolver to use instead of
            :func:`socket.getaddrinfo`. Exposed mainly for tests; real
            callers should leave this unset.

    Raises:
        UnsafeWebhookUrlError: If the URL has no host, resolves to a
            known-blocked hostname, cannot be resolved at all, or
            resolves to a private, loopback, link-local, reserved, or
            multicast IP address.
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise UnsafeWebhookUrlError(f"URL has no host: {url!r}")
    if host.lower() in _BLOCKED_HOSTNAMES:
        raise UnsafeWebhookUrlError(f"Webhook host is not allowed: {host!r}")

    resolve = resolver or _default_resolver
    try:
        addresses = resolve(host)
    except OSError as exc:
        raise UnsafeWebhookUrlError(f"Could not resolve webhook host {host!r}: {exc}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeWebhookUrlError(
                f"Webhook host {host!r} resolves to a disallowed address: {ip}"
            )

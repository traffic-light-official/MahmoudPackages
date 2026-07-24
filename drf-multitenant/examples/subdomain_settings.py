"""Example settings snippet for subdomain-based tenant resolution.

See ``docs/examples.md`` and ``docs/configuration.md``.
"""

from __future__ import annotations

MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
    "RESOLVER": "drf_multitenant.resolvers.subdomain_resolver",
}

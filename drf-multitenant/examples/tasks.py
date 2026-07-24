"""Example: a Celery task binding its own tenant context.

Illustrative only — this package has no dependency on Celery.
See ``docs/examples.md`` and ``docs/advanced-usage.md``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from examples.minimal_app.models import Project, Tenant

from drf_multitenant.context import tenant_context


def archive_stale_projects(tenant_id: int) -> None:
    """Archive projects untouched for 90+ days, scoped to one tenant.

    In a real project this would be decorated with e.g.
    ``@celery.shared_task`` and invoked once per tenant on a schedule.
    """
    tenant = Tenant.objects.get(pk=tenant_id)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=90)
    with tenant_context(tenant):
        Project.objects.filter(updated_at__lt=cutoff).update(archived=True)

"""``manage.py show_view_permissions <path>``: describe a URL's permission stack."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.urls import Resolver404, resolve

from drf_permission_debugger.introspection import describe_view


class Command(BaseCommand):
    """Resolve a URL path and print its view's permission/authentication/throttle classes."""

    help = "Show the permission/authentication/throttle classes configured for a URL path."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("path", help="A URL path to resolve, e.g. /api/articles/1/")

    def handle(self, *args: Any, **options: Any) -> None:
        path: str = options["path"]
        try:
            match = resolve(path)
        except Resolver404 as exc:
            raise CommandError(f"No URL matches {path!r}.") from exc

        view_class = getattr(match.func, "cls", None) or getattr(match.func, "view_class", None)
        if view_class is None:
            raise CommandError(f"{path!r} does not resolve to a class-based view.")

        self.stdout.write(
            self.style.SUCCESS(f"{path} -> {view_class.__module__}.{view_class.__qualname__}")
        )

        description = describe_view(view_class)

        permissions = description["permissions"]
        self.stdout.write(f"\npermission_classes ({len(permissions)}):")
        if not permissions:
            self.stdout.write("  (none)")
        for item in permissions:
            marker = " [object-level]" if item.checks_object_permission else ""
            self.stdout.write(f"  - {item.name}{marker}")
            if item.docstring:
                self.stdout.write(f"      {item.docstring.splitlines()[0]}")

        authentication_classes = description["authentication_classes"]
        self.stdout.write(f"\nauthentication_classes ({len(authentication_classes)}):")
        for name in authentication_classes:
            self.stdout.write(f"  - {name}")
        if not authentication_classes:
            self.stdout.write("  (none)")

        throttle_classes = description["throttle_classes"]
        self.stdout.write(f"\nthrottle_classes ({len(throttle_classes)}):")
        for name in throttle_classes:
            self.stdout.write(f"  - {name}")
        if not throttle_classes:
            self.stdout.write("  (none)")

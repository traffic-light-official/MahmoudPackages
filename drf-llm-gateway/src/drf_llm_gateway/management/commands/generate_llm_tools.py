"""``generate_llm_tools`` management command.

Exports every tool registered via
:func:`~drf_llm_gateway.registry.expose_as_tool` as JSON, in OpenAI
function-calling format, MCP tool format, or plain JSON Schema.

.. code-block:: bash

    python manage.py generate_llm_tools --format openai > tools.json
    python manage.py generate_llm_tools --format mcp --indent 2
    python manage.py generate_llm_tools --format jsonschema --urlconf myproject.urls
"""

from __future__ import annotations

import json
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.urls import get_resolver

from drf_llm_gateway.mcp import to_mcp_tools
from drf_llm_gateway.openai_tools import to_openai_tools
from drf_llm_gateway.registry import default_registry


class Command(BaseCommand):
    """Export registered LLM tool definitions as JSON."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register this command's CLI arguments.

        Args:
            parser: The argument parser to add options to.
        """
        parser.add_argument(
            "--format",
            choices=["openai", "mcp", "jsonschema"],
            default="openai",
            help="Output format. 'jsonschema' emits each tool's name, "
            "description, and raw input schema without OpenAI/MCP "
            "envelope fields. Defaults to 'openai'.",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON indentation level. Use 0 for compact single-line output.",
        )
        parser.add_argument(
            "--urlconf",
            default=None,
            help="Dotted path to a URLconf module to import before exporting, "
            "so that @expose_as_tool-decorated viewsets referenced by its "
            "routers are registered. Defaults to ROOT_URLCONF.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the command.

        Args:
            *args: Unused positional arguments.
            **options: Parsed CLI options (``format``, ``indent``, ``urlconf``).

        Raises:
            django.core.management.base.CommandError: If no tools are
                registered after importing the URLconf, which almost
                always means the URLconf wasn't the right one, or no
                viewset in the project uses ``@expose_as_tool``.
        """
        get_resolver(options["urlconf"]).url_patterns  # noqa: B018 - forces urlconf import

        if len(default_registry) == 0:
            raise CommandError(
                "No tools are registered. Ensure the URLconf that imports your "
                "@expose_as_tool-decorated viewsets is loaded (pass --urlconf "
                "if it isn't ROOT_URLCONF)."
            )

        if options["format"] == "openai":
            payload: Any = to_openai_tools(default_registry)
        elif options["format"] == "mcp":
            payload = to_mcp_tools(default_registry)
        else:
            payload = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.input_json_schema(),
                    "version": tool.version,
                    "schema_hash": tool.schema_hash,
                }
                for tool in default_registry
            ]

        indent = options["indent"] or None
        self.stdout.write(json.dumps(payload, indent=indent, default=str))

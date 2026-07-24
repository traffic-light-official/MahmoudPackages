# Deployment

## There is nothing to deploy separately

This package adds no processes, no background workers, and no external
service dependencies. Tool registration happens as a side effect of
importing your viewset modules (which already happens when Django loads
your URLconf); `execute_tool` runs synchronously inside whatever
request/job context calls it.

## Version pinning

```
drf-llm-gateway>=1.0,<2.0
```

Any breaking change bumps the major version per
[Semantic Versioning](https://semver.org/), with a migration note in
`CHANGELOG.md`.

## Supported runtime versions

| Dependency | Supported |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |

## Exposing tools to an external agent runtime

If your agent framework runs as a separate service (not in-process with
Django), generate a static tool manifest at deploy/build time:

```bash
python manage.py generate_llm_tools --format mcp > tools.json
```

and ship `tools.json` alongside your agent service. For tool *execution*,
either:

- Run the agent framework in-process with Django and call `execute_tool`
  directly, or
- Expose a small internal API endpoint that accepts `{name, arguments}`
  and calls `execute_tool` on the agent framework's behalf, authenticating
  the request however you authenticate other internal service-to-service
  calls.

## `INSTALLED_APPS` in production

Only include `"drf_llm_gateway"` in `INSTALLED_APPS` if you actually use
the `generate_llm_tools` management command in your deployment pipeline
(e.g. a CI step that regenerates `tools.json`). It has no runtime cost
beyond registering the management command.

## Rolling out new tools safely

1. Add `@expose_as_tool` to a viewset with a narrow `actions=[...]` list
   first (read-only).
2. Verify the generated schema in a non-production environment:
   `python manage.py generate_llm_tools --format jsonschema`.
3. Expand to write actions only once you've decided on permission
   modeling for the calling identity — see
   [Configuration](configuration.md#deciding-on-permission-modeling-for-agent-identities).
4. Track `schema_hash` in your agent framework's tool cache so schema
   drift after a deploy is detected automatically rather than silently
   causing malformed tool calls.

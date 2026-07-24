# Common Patterns

## Scoped tool sets per agent trust level

Expose a narrow, read-only tool set to a fully autonomous agent and a
wider read/write set to one operating under human review:

```python
@expose_as_tool(actions=["list", "retrieve"], name_prefix="ro_article", registry=autonomous_registry)
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    ...

@expose_as_tool(actions=["list", "retrieve", "create", "update", "destroy"], registry=supervised_registry)
class ArticleViewSet(viewsets.ModelViewSet):
    ...
```

## Human-in-the-loop confirmation before destructive tools

`execute_tool` doesn't have an opinion about confirmation flows — build it
one layer up, in whatever code receives the model's tool call before
handing it to `execute_tool`:

```python
DESTRUCTIVE_ACTIONS = {"destroy", "update", "partial_update"}


def dispatch_tool_call(name, arguments, *, user, confirmed=False):
    tool = default_registry.get(name)
    if tool and tool.action in DESTRUCTIVE_ACTIONS and not confirmed:
        return {"requires_confirmation": True, "tool": name, "arguments": arguments}
    return execute_tool(name, arguments, user=user)
```

## Rate-limiting agent tool calls

Since `execute_tool` dispatches through the real view, any throttle
classes configured on the viewset (`throttle_classes`) apply automatically
— no extra work needed. Configure them the same way you would for a
regular API consumer.

## Auditing every tool call

Wrap `execute_tool` at your call site to log every invocation — this
package doesn't emit logs itself, keeping the audit trail's shape entirely
under your control:

```python
import logging

logger = logging.getLogger("llm_gateway.audit")


def audited_execute_tool(name, arguments, *, user):
    logger.info("tool_call", extra={"tool": name, "user": user.pk, "arguments": arguments})
    result = execute_tool(name, arguments, user=user)
    logger.info("tool_result", extra={"tool": name, "status": result.status_code})
    return result
```

## Exposing a subset of a large ViewSet

If a viewset has many actions but only some make sense as agent tools,
just list the ones you want:

```python
@expose_as_tool(actions=["list", "retrieve"])  # no create/update/destroy exposed
class ArticleViewSet(viewsets.ModelViewSet):
    ...
```

The viewset continues to work exactly as before for normal HTTP clients —
`expose_as_tool` only adds registry entries, it never changes the
viewset's own behavior.

## Generating a static tools.json for a non-Python agent runtime

```bash
python manage.py generate_llm_tools --format mcp > tools.json
```

Ship `tools.json` to a runtime written in another language — it's plain
JSON with no Python-specific structure.

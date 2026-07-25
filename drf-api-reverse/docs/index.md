# drf-api-reverse

Design-first DRF scaffolding: generate `serializers.py`, `views.py`, and
`urls.py` directly from an OpenAPI contract - idempotently, so the
generated code and your hand-written implementation can coexist and
evolve together.

```bash
drf-api-reverse scaffold --schema api/contract.yml --output myapp/
```

## Why this exists

Code-first DRF works well once an API exists: models come first,
`drf-spectacular` derives the schema from the code. A design-first team
works the other way around - the contract is agreed on first, often
before a single Django model exists - and hand-translating that
contract into serializer fields and viewset methods by eye is slow and
error-prone. This package generates that translation directly and
mechanically, and - critically - lets you regenerate it as the contract
evolves without clobbering the business logic you've since written.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring this into CI? See [Deployment](deployment.md).
- Want to know exactly how idempotent regeneration works? Read
  [Architecture](architecture.md).
- Looking for a specific function? Jump to [API Reference](api-reference.md).
- Something not behaving as expected? Check [Troubleshooting](troubleshooting.md)
  and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Generate/regenerate code from a schema | [`scaffold()`](api-reference.md#scaffold) / [CLI](getting-started.md) |
| Detect drift between contract and code | [`check_drift()`](api-reference.md#check_drift) |
| Gate CI on drift | `drf-api-reverse check` / [Deployment](deployment.md) |
| Wire into an existing Django project | [`scaffold_api`](advanced-usage.md#django-management-command) |
| Understand what gets scaffolded vs. left alone | [Architecture](architecture.md) |

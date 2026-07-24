# drf-contract-test

Catch breaking API changes before they ship.

`drf-contract-test` compares two OpenAPI schema snapshots — your last
release and your current working tree — and reports exactly what
changed, using the *correct* notion of "breaking" for each side of the
contract:

- A **request** schema describes what a client may send. Making it more
  permissive is safe; making it more restrictive is breaking.
- A **response** schema describes what the server promises. Promising
  more is safe; promising less is breaking.

A naive structural diff can't tell these apart — a new required field is
breaking in a request but harmless in a response, and vice versa for a
removed field. `drf-contract-test` encodes this asymmetry directly, so
its output is a real compatibility signal, not just a list of
differences.

## What it does

- Diffs two OpenAPI schemas operation-by-operation, classifying every
  change as `breaking`, `safe`, or `info`.
- Generates contract test cases from a schema and validates live
  responses against their documented shape.
- Enforces that breaking changes are accompanied by a version bump.
- Ships a CLI, a pytest plugin, and JSON/HTML report renderers for CI.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring it into CI? See [Quick Start](quickstart.md) and
  [Deployment](deployment.md).
- Want to understand the directional rules in depth? See
  [Architecture](architecture.md).
- Looking for a specific function or class? See
  [API Reference](api-reference.md).

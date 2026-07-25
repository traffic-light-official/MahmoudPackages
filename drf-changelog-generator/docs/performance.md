# Performance

## The diff itself is O(schema size), not O(history)

`diff_schemas()` walks exactly the two documents given to it - paths,
then operations, then parameters/request body/response bodies per
operation, with recursive field diffing bounded by the depth of the
JSON Schema itself. It does not walk Git history, does not diff every
commit between two refs, and its cost is entirely a function of how
large the two OpenAPI documents are, not how many commits separate
them.

## Loading a schema at a Git ref is a single `git show`, not a checkout

`git_utils.load_schema_at_ref()` shells out to `git show <ref>:<path>`
once per ref - two subprocess calls total for a two-way diff, regardless
of repository size or history depth, since `git show` reads one blob
directly from Git's object database rather than materializing a
worktree. This is the reason the CLI and GitHub Action are fast even
against large, long-lived repositories: no `git checkout`, no dependency
install at the historical ref, no second clone.

## `$ref` resolution is cached per diff, not per field

`diffing.refs.deref()` resolves a `$ref` by walking the document's own
structure directly (a dict traversal, not a network call or file read -
this package only supports *local* `#/...` JSON pointers, see
[Architecture](architecture.md)). A schema with the same `$ref` repeated
across many operations (a shared `Article` schema used in ten
endpoints, say) pays that dict-traversal cost once per occurrence, which
in practice is negligible even for schemas with hundreds of operations -
there is no measurable benefit to adding a resolution cache on top, and
this package deliberately does not carry that complexity.

## Rendering is linear in the number of changes

Every renderer (`render_markdown`, `render_html`, `render_slack_blocks`,
`render_github_release_notes`) calls `rendering.common.summarize()`
once, which partitions `SchemaDiff.changes` in a single pass, then
formats each partition - there is no repeated re-scanning of the full
change list per section.

## CI cost is dominated by `git fetch`, not this tool

In a GitHub Actions job, the overwhelming majority of wall-clock time
attributable to this package's use is `actions/checkout@v4` with
`fetch-depth: 0` (needed so `--old-ref` is actually resolvable locally -
see [Common Patterns](common-patterns.md#gating-a-pr-on-breaking-api-changes)),
not the diff or render step itself, which typically completes in well
under a second for schemas up to several hundred operations. If checkout
time matters, prefer a shallower `fetch-depth` scoped to just the refs
you need (e.g. `git fetch --depth=1 origin main`) over a full history
fetch.

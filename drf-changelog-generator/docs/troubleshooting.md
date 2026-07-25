# Troubleshooting

## The CLI exits with status `2` and "Error: ..."

Status `2` means a usage or loading error, not a diffing result -
`--fail-on-breaking` exiting `1` for a real breaking change is a
different, expected outcome. Check the printed message against
[Git-related errors](#git-related-errors) or
[Schema parsing errors](#schema-parsing-errors) below.

## Git-related errors

`GitError: 'git show <ref>:<path>' failed in <repo>: ...` means one of:

1. `<ref>` does not exist in `<repo>` - confirm with `git tag`/`git
   branch -a` inside that repository, and remember that a shallow
   checkout (GitHub Actions' default `fetch-depth: 1`) will not have
   older refs; use `fetch-depth: 0` - see
   [Deployment](deployment.md#checklist).
2. `<path>` was not committed at `<ref>` - it may have been added,
   renamed, or moved after that ref (e.g. you renamed
   `schema.yml` to `api/schema.yml` at some point; use the *old* path
   for `--old-ref` and the *new* path for `--new-ref` if they differ, by
   loading each side separately rather than via a single `--schema-path`).
3. `<repo>` is not a Git repository, or `git` is not on `PATH` -
   `GitError: The 'git' executable was not found on PATH.` is raised
   distinctly for the latter case.

## Schema parsing errors

`SchemaParseError` means the file's content could not be parsed as
either JSON or YAML - most commonly because it isn't actually an OpenAPI
document (e.g. `--schema-path` points at the wrong file), or because it
is genuinely malformed (check it parses standalone with `python -c
"import yaml, sys; yaml.safe_load(open(sys.argv[1]))" schema.yml`).

## The diff shows no changes, but I know the schema changed

Confirm the diff is actually comparing what you think it is:

1. With `--old-file`/`--new-file`, both paths must resolve to the files
   you expect - a stale build artifact from a previous run is a common
   culprit, especially if `--old-file`/`--new-file` point at a
   generated (not committed) schema.
2. With `--repo`/`--old-ref`/`--new-ref`, both refs must actually differ
   at `--schema-path` - `git diff <old-ref> <new-ref> -- <schema-path>`
   directly is a fast way to confirm the file itself changed before
   suspecting this package.
3. A change to a part of the OpenAPI document this package does not
   model (e.g. `info.description`, `servers`, `tags` at the document
   level, security schemes) will not appear - only `paths` (operations,
   parameters, request/response bodies) is diffed; see the
   [module map](architecture.md#module-map).

## A field change I expected as non-breaking shows as breaking (or vice versa)

Re-check against the
[exhaustive rule table](architecture.md#the-breaking-change-rule-set) -
every classification is a fixed rule, not a heuristic. The most common
surprise is a field moving from optional to required (breaking, since a
previously-valid request may now be rejected) being mistaken for "just
adding validation," which is a meaningful behavior change for existing
clients regardless of intent.

## `--fail-on-breaking` didn't fail the CI job even though breaking changes are shown

Confirm the step's shell actually propagates the exit code - some CI
systems swallow a failing exit code if the step is not the last command
in a script block, or if output is piped through another command (a
trailing `| tee changelog.md` replaces the exit code with `tee`'s own,
`0`). Use `--output` to write to a file instead of piping stdout, if you
need both the file and a propagated exit code.

## `generate_changelog: command not found` / `Unknown command: 'generate_changelog'`

Add `drf_changelog_generator` to `INSTALLED_APPS` - Django only
discovers management commands from installed apps. Also confirm
`drf-spectacular` is installed (`pip install
drf-changelog-generator[spectacular]`), since the command imports and
calls it directly.

## The GitHub Action step succeeds but `has-breaking-changes` is always `"false"`

Confirm `fetch-depth: 0` is set on the preceding `actions/checkout`
step - if `old-ref` cannot be resolved locally, `git show` fails, which
the composite action treats as a step failure (visible in the job log),
not as "no breaking changes." Check the actual job log output rather
than only the output value if this happens.

# Security

## This package never executes untrusted schema content

An OpenAPI document is data - `schema_loader.parse_schema()` uses
`yaml.safe_load()` (never `yaml.load()` with a permissive loader) and
`json.loads()`, neither of which can execute arbitrary code or construct
arbitrary Python objects from the input. A malicious or malformed schema
file can, at worst, cause a `SchemaParseError` or produce a nonsensical
diff - it cannot achieve code execution through this package.

## `git show` runs with a fixed, minimal argument list

`git_utils.show_file_at_ref()` invokes `subprocess.run(["git", "show",
f"{ref}:{file_path}"], ...)` with `shell=False` and a static argument
list built entirely from function parameters, never from string
concatenation into a shell command - there is no shell injection surface
even if `ref` or `file_path` originate from untrusted input (e.g. a PR
title or branch name in a CI context). That said, treat `--repo`,
`--old-ref`, `--new-ref`, and `--schema-path` as trusted, operator-supplied
configuration, not end-user input, the same as any other CI job
parameter - a ref like `HEAD; rm -rf /` is passed to `git show` as a
single literal argument (Git will simply fail to resolve it), but this
package still runs wherever `git` is invoked, with whatever permissions
the calling process has.

## The Slack webhook poster validates the URL scheme, nothing more

`rendering.slack.post_to_slack_webhook()` performs an HTTPS `POST` via
`urllib.request` to the URL given in `--slack-webhook`/`slack-webhook-url`.
It does not restrict the target host - the assumption is that the
webhook URL comes from your own CI secret, not user input. Do not wire
`--slack-webhook`/`slack-webhook-url` to anything other than a trusted
secret, since this package will POST the rendered changelog body to
whatever URL it is given.

## No secrets are logged

Rendered changelogs contain schema structure (paths, field names, types)
- never request/response *data*, credentials, or tokens, since this
package only ever reads OpenAPI schema documents, never live API
traffic. The GitHub Action does not print the Slack webhook URL or any
other input to the job log.

## Dependency posture

This package's runtime dependencies are `PyYAML` (schema parsing),
Django, and Django REST Framework (for the optional management
command); `drf-spectacular` is an optional extra, only required if you
use `generate_changelog`. All are widely used, actively maintained
projects pinned to minimum versions in `pyproject.toml` and kept current
via Dependabot (see [Contributing](contributing.md)).

## Reporting a vulnerability

See [`SECURITY.md`](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-changelog-generator/SECURITY.md)
for the disclosure process. Do not open a public issue for a suspected
vulnerability.

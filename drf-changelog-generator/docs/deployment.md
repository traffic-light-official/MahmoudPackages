# Deployment

This package has no runtime component to deploy - it runs as a CLI step
in CI, a GitHub Action, or an ad hoc/pre-commit invocation. "Deployment"
here means wiring it correctly into your CI pipeline.

## Checklist

- [ ] `actions/checkout@v4` uses `fetch-depth: 0` (or a `--old-ref`-scoped
      shallow fetch) - `git show <ref>:<path>` needs the historical
      commit to be present locally, and the default shallow checkout
      only has the current one.
- [ ] The schema file at `--schema-path`/`schema-path` is actually
      committed to the repository at every ref you plan to diff against
      - a generated-but-gitignored schema file cannot be read at a past
        ref.
- [ ] `--fail-on-breaking`/`fail-on-breaking: "true"` is set on the job
      that should block a merge, and *not* set on a job that should
      always post/publish regardless (see
      [Common Patterns](common-patterns.md#posting-a-changelog-to-slack-on-release)).
- [ ] If using `--slack-webhook`, the webhook URL is a CI secret, never
      committed or logged - see [Security](security.md#the-slack-webhook-poster-validates-the-url-scheme-nothing-more).
- [ ] If using the `generate_changelog` management command,
      `drf-spectacular` is installed (`pip install
      drf-changelog-generator[spectacular]`) and already configured for
      the project (`SPECTACULAR_SETTINGS`, a working `ROOT_URLCONF`).

## Wiring into an existing CI pipeline

The GitHub Action ([Advanced Usage](advanced-usage.md#github-action)) is
the lowest-friction path for GitHub Actions specifically. For any other
CI system (GitLab CI, CircleCI, Jenkins, etc.), install the package and
call the console script directly - it has no CI-specific dependency:

```yaml
# .gitlab-ci.yml
api-changelog:
  stage: test
  script:
    - pip install drf-changelog-generator
    - drf-changelog-generator diff --repo . --old-ref origin/main --new-ref HEAD
      --schema-path api/schema.yml --fail-on-breaking
  variables:
    GIT_DEPTH: 0
```

## Versioning the schema file itself

This package diffs whatever is committed at `--schema-path` - it does
not generate that file for you (except via the optional
`generate_changelog` management command, which generates only the "new"
side via `drf-spectacular`). Commit a schema snapshot on every release
tag if you plan to diff against tags rather than branch history; a
common pattern is a release workflow step that runs `manage.py
spectacular --file api/schema.yml` and commits it as part of the release
commit, before tagging.

## Running entirely offline / air-gapped

The CLI's `--old-file`/`--new-file` mode needs no network access and no
Git repository at all - two local files are sufficient. Only
`--repo`/`--old-ref`/`--new-ref` mode needs `git` on `PATH` (no network
access either, as long as the refs are already present locally), and
only `--slack-webhook` needs outbound network access.

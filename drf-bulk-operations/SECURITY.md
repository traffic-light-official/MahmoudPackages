# Security Policy

## Supported Versions

Security fixes are provided for the latest minor release on the current
major version line. Older major versions do not receive security patches
once a new major version has been released for at least 3 months.

| Version    | Supported          |
| ---------- | ------------------ |
| Latest 1.x | :white_check_mark: |
| < 1.0      | :x:                |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security vulnerabilities by emailing
**mahmoudgshaker2023@gmail.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce, including a minimal reproduction if possible
- The version of `drf-bulk-operations` affected
- Any known mitigations

You should receive an acknowledgement within **5 business days**. We will
keep you informed of progress toward a fix and will credit you in the
release notes unless you request otherwise.

Once a fix is available, we will:

1. Publish a patched release to PyPI.
2. Publish a GitHub Security Advisory describing the issue and affected
   versions.
3. Update `CHANGELOG.md` with a `Security` entry.

## Disclosure Policy

We follow coordinated disclosure. Please allow a reasonable window (target:
90 days) to release a fix before any public disclosure of vulnerability
details.

## Security Best Practices for Users

- Pin `drf-bulk-operations` to a specific version range in production and
  review `CHANGELOG.md` before upgrading.
- Keep Django and Django REST Framework up to date.
- Set `MAX_BATCH_SIZE` to a value appropriate for your deployment - an
  unbounded bulk request holds a database transaction (in atomic mode)
  or a long series of independent saves (in non-atomic mode) open for
  as long as the whole batch takes to process. See `docs/security.md`.

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
- The version of `drf-n-plus-one-query-guard` affected
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

- Pin `drf-n-plus-one-query-guard` to a specific version range in
  production and review `CHANGELOG.md` before upgrading.
- Keep Django and Django REST Framework up to date.
- Never enable `MODE = "raise"` for `NPlusOneGuardMiddleware` in
  production - a suspected N+1 becomes an unhandled exception (a 500
  response) for real users; reserve `"raise"` for development, CI, and
  staging. See `docs/security.md`.
- The `RESPONSE_HEADER` is only ever added when `settings.DEBUG` is
  `True`, regardless of `MODE` - do not rely on it in production
  monitoring.

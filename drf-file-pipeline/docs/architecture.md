# Architecture

## Why validation runs twice

`InitiateUploadSerializer` validates content-type and size against what
the *client declares* before any bytes exist — this is a cheap, early
rejection for the common case, but it's not authoritative: a client can
declare `size: 100` and then upload 100MB directly to S3, bypassing
Django entirely (that's the whole point of presigned uploads — Django
never sees the bytes in transit). `process_upload()` re-validates
against the *actual* object in storage (`storage.head()`'s real
`ContentLength`), overwriting `upload.size` with the true value first.
Only the second pass can be trusted; the first pass exists purely to
reject obviously-bad requests before generating a presigned URL at all.

## Why `process_upload()` isn't a worker

This package ships no Celery app, no RQ integration, no polling loop —
`process_upload(upload_id)` is a plain function. Every team already runs
*some* task queue (or none, and wants a management-command loop
instead), and re-implementing queue integration for each one would be
both redundant and opinionated in a way that doesn't fit a general-purpose
package. Keeping `process_upload()` queue-agnostic means it's a
one-line wrapper away from working with whatever you already have — see
[Advanced Usage](advanced-usage.md) and [Deployment](deployment.md).

## Resumability: why `UploadPart` is a separate model

A multipart upload could track its completed parts as a JSON blob on
`FileUpload` itself. It's a separate model instead because: (a) parts
are reported one at a time, over what can be a long-lived upload
(minutes to hours for very large files) — a separate row per part
avoids read-modify-write races on a single JSON field across concurrent
part-completion requests; (b) `unique_together` on `(upload, part_number)`
gives "report the same part twice" (a client retry after a flaky
response) idempotent `update_or_create()` semantics for free, which a
hand-rolled JSON list wouldn't; and (c) it makes "which parts are already
done" a plain indexed query (`upload.parts.values_list("part_number")`)
instead of JSON-field introspection.

## Storage as a `Protocol`, not a base class

`StorageBackend` is `typing.Protocol`, not an abstract base class —
implementations don't need to import or subclass anything from this
package, just structurally match the method signatures. This keeps a
custom backend (GCS, Azure, a test double) fully decoupled from this
package's own class hierarchy — see
[Advanced Usage](advanced-usage.md#writing-a-custom-storage-backend).

## A real bug this design caught: image format detection

`render_preset()` originally read `source.format` *after* calling
`ImageOps.exif_transpose(source)`. That function returns a **new**
`Image` object when it performs a rotation (or an unchanged copy
otherwise) — and a transformed/copied image built via Pillow transform
operations doesn't carry over the `.format` attribute (only images
loaded directly via `Image.open()` have one). The result: every
generated preset was silently saved as PNG regardless of the original
format, only caught by a test asserting the *saved* preset's format
matched the source (`test_jpeg_with_alpha_source_is_converted_to_rgb`).
The fix — capture `image_format = source.format` **before** calling
`exif_transpose()` — is now load-bearing: format detection must happen
against the freshly-opened image, never a derived one.

## Why the manager isn't a `TenantManager`-style auto-scoper

Unlike this author's `drf-multitenant` package, `FileUpload.objects` is
a plain Django manager — there's no automatic "current user" scoping.
`FileUploadViewSet.get_queryset()` filters by `owner` explicitly instead.
This is deliberate: uploads support an anonymous-owner flow
(`owner=None`) that a blanket auto-scoping manager would need special-cased
logic to handle correctly, and object-level access for anonymous
uploads is enforced by `IsUploadOwner` rather than at the queryset layer
at all — see [Security](security.md) for the full access model.

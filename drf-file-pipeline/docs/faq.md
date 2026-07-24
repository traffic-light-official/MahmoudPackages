# FAQ

## Why is `upload.size` different from what I sent at `initiate/`?

Because `process_upload()` overwrites it with the real object size from
storage — the client-declared size at initiate time is never trusted
for anything beyond an early sanity check. See
[Architecture](architecture.md#why-validation-runs-twice).

## Does this package upload files itself?

No. It only issues presigned URLs (or presigned multipart part URLs) —
the client uploads directly to S3. Django never receives the file's
bytes. This is the entire point (see [Performance](performance.md)).

## My upload is stuck in "uploading" forever

The client either never called `complete/`, or is still in progress.
Nothing marks an upload `FAILED` just for taking a while — that's
intentional (large multipart uploads can legitimately take hours).
Use `cleanup_abandoned_uploads` to reclaim uploads that are *actually*
abandoned, past a configurable age.

## Why didn't my image get any presets generated?

Check: (1) `IMAGE_PRESETS` is actually configured (empty by default);
(2) the upload's `content_type` starts with `IMAGE_CONTENT_TYPE_PREFIX`
(default `"image/"`); (3) `process_upload()` has actually run — presets
are generated during processing, not at `complete/` time. If processing
ran and failed, check `upload.error_message`.

## Can I use this without a task queue at all?

Yes — call `process_upload()` synchronously wherever's convenient (a
management command, a scheduled poll, even directly in the view after
`complete/` for low-traffic applications where the processing latency
is acceptable in the request/response cycle). It's a plain function; a
task queue is a recommendation for anything with meaningful traffic or
slow processing (image presets, a real virus scanner), not a
requirement.

## Does this support non-S3 storage (GCS, Azure)?

Not built in, but the storage layer is a `Protocol` specifically so you
can implement one — see
[Advanced Usage](advanced-usage.md#writing-a-custom-storage-backend).

## Why is `null_scanner` the default instead of requiring a scanner to be configured?

Because this package ships no scanning engine of its own, and forcing a
hard dependency on a specific one (ClamAV bindings, a particular cloud
API) would be wrong for the many deployments that don't need it or use
a different one. The tradeoff is that the safe-by-default posture this
package aims for elsewhere (queryset scoping in `drf-multitenant`,
tenant isolation) isn't achievable here without picking a scanner for
you — see [Security](security.md), which spells this out explicitly
rather than leaving it implicit.

## Can multiple uploads share the same S3 key?

No — `build_object_key()` always generates a fresh UUID-prefixed key
per upload, and `FileUpload.key` has a unique database constraint. Two
uploads, even of files with the identical filename, never collide.

## How do I delete an upload (and its S3 object) that's already completed?

There's no built-in "delete a completed upload" endpoint or function —
`cleanup_abandoned_uploads` only targets `PENDING`/`UPLOADING` uploads.
Delete the object via `storage.delete(key=upload.key)` (and, for images,
each preset key in `upload.metadata["presets"]`) and the `FileUpload`
row yourself; this is intentionally left as an application-level
decision (soft-delete? audit trail? cascading to your own models
referencing the upload?) rather than a one-size-fits-all default.

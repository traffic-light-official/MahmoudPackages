# Performance

## The whole point: Django never touches file bytes

`InitiateUploadView` and `CompleteUploadView` only ever exchange small
JSON payloads and presigned URLs — the file's actual bytes travel
directly between the client and S3. This is the single biggest
performance property of this package: your Django workers' memory and
request-handling capacity are never a function of upload size or
concurrency, unlike a traditional proxy-through-the-server upload
endpoint.

## Multipart chunk size is a real tradeoff

`MULTIPART_CHUNK_SIZE` controls how many presigned part URLs
`InitiateUploadView` generates up front (`ceil(size / chunk_size)`) —
each one is a local, offline signing operation (no network round-trip),
so generating even hundreds of them is fast, but the response payload
grows linearly with part count. Larger chunks mean fewer parts (smaller
response, less resumability granularity — losing one part costs more
re-upload); smaller chunks mean the opposite. S3's own minimum
(5 MiB, enforced by `MULTIPART_CHUNK_SIZE`'s settings validation) is a
hard floor regardless.

## `process_upload()` cost scales with what you configure

With no virus scanner and no image presets configured, `process_upload()`
is dominated by one `storage.head()` call (fast) plus your validation
callbacks (typically fast, pure-Python checks). Image preset generation
adds one `download_to_path()` (network-bound, proportional to file
size) plus one Pillow render and one `upload_from_path()` per configured
preset — for large images or many presets, this is the dominant cost.
Run `process_upload()` from a background worker (as designed — see
[Architecture](architecture.md)), never inline in a request/response
cycle.

## Presigning is local; S3 operations are not

`create_presigned_post()`, `presign_upload_part()`, and
`generate_presigned_get_url()` are pure local computation (HMAC
signing) — no network call, no latency, safe to call as often as
needed. `create_multipart_upload()`, `complete_multipart_upload()`,
`abort_multipart_upload()`, `head()`, `delete()`,
`download_to_path()`, and `upload_from_path()` are real S3 API calls
and carry normal network latency.

## Cleanup is a periodic batch job, not a hot path

`cleanup_abandoned_uploads` is designed to run on a schedule (see
[Deployment](deployment.md)), not per-request — it queries and deletes
in bulk rather than one row at a time, and there's no reason to run it
more than every few minutes to hours depending on your abandonment
tolerance.

## Testing performance without hitting real S3

The test suite mocks S3 entirely via `moto` (see [Testing](testing.md)),
so the test suite's speed reflects your own code's overhead, not S3
network latency — a useful property when profiling `process_upload()`'s
non-network-bound cost (validation, image rendering) in isolation.

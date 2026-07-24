# Security

## Threat model

1. **Idempotency keys are not authentication.** Anyone who can send an
   authenticated request to your API can send any idempotency key value
   they like. This package assumes normal authentication/authorization
   already happens elsewhere in your stack (DRF permission classes,
   session/token auth, ...) — it only deduplicates *within* whatever
   already-authorized request stream reaches it.
2. **Keys are not scoped to a user by default.** If two different users
   could plausibly send the same literal key value (e.g. both generate
   `"1"` due to a client bug), one user's request could be replayed for
   the other. **Recommendation**: if your key generation isn't already
   effectively unique per-request (e.g. proper UUIDs), incorporate the
   authenticated user's ID into the key namespace at the application
   layer — e.g. `f"{request.user.id}:{client_supplied_key}"` — before it
   reaches this package's header. This package deliberately doesn't force
   a particular scoping scheme, since the right one depends on your auth
   model.
3. **Fingerprinting prevents cross-request replay, not cross-user
   replay.** `IdempotencyKeyReuseError` protects against a key being
   reused for a *different request body* — it does not, by itself,
   prevent a key from being reused for the *same* request body by a
   different (or unauthorized) caller if your key scoping doesn't account
   for identity. See point 2.
4. **Stored response bodies may contain sensitive data.** A completed
   record's response body is stored verbatim (base64-encoded for the
   database backend) until `TTL_SECONDS` expires. Treat your idempotency
   store with the same care as any other store of API response data —
   database backend records live in your primary database (subject to
   your existing access controls and backup/encryption policies); Redis
   records should be in a Redis instance with equivalent access controls,
   not a shared/public cache.
5. **The key itself is validated but not secret.** `validate_key()`
   rejects malformed input (length, character set) to prevent obviously
   malicious values from reaching your storage backend, but a key is not
   a credential — don't rely on key unguessability for access control.

## Denial-of-service considerations

- `MAX_KEY_LENGTH` (default 255) bounds the size of the key itself.
- Request body size should already be bounded by your web server/Django's
  own `DATA_UPLOAD_MAX_MEMORY_SIZE` — this package doesn't impose an
  additional limit, since fingerprinting cost scales linearly and
  harmlessly with whatever body size your stack already accepts.
- `LOCK_TTL_SECONDS` bounds how long a single (possibly malicious, slow,
  or hung) request can hold a lock before it's reclaimable.

## Recommended production configuration

```python
IDEMPOTENCY = {
    "REQUIRE_KEY": True,       # once all clients have adopted the header
    "MAX_KEY_LENGTH": 128,     # tighter than the default 255, if your keys are UUIDs
    "TTL_SECONDS": 86400,
    "LOCK_TTL_SECONDS": 30,    # tuned to your view's actual p99 latency
}
```

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-idempotency/blob/main/SECURITY.md).

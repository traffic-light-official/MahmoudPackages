# Security

## Threat model

1. **Rate limiting is a mitigation, not a complete defense.** It reduces
   the *rate* at which an attacker can act, but a sufficiently patient or
   distributed attacker (many IPs, many accounts) can still eventually
   exceed what a single-dimension limit catches. Combine key functions
   (`combine("ip", "user")`) or add IP-based limits alongside user-based
   ones for defense in depth against credential-stuffing-style attacks
   that rotate identities.
2. **`by_ip` trusts `X-Forwarded-For`.** If your app is directly exposed
   to the internet (not behind a trusted proxy/load balancer that
   sanitizes this header), a client can forge `X-Forwarded-For` to evade
   IP-based limiting entirely. Only rely on `by_ip` behind infrastructure
   you trust to set that header correctly (or write a custom key function
   reading whatever header your actual proxy sets, e.g.
   `True-Client-IP` or a signed header).
3. **Rate-limit state is visible to anyone with Redis access.** Keys are
   prefixed (`KEY_PREFIX`) but not encrypted — treat your Redis instance
   with the same access controls you'd apply to any other
   operationally-sensitive store. An identity string derived from
   `by_user`/`by_tenant` could reveal user/tenant IDs to anyone who can
   read Redis keys directly (not to API clients, who never see raw keys).
4. **A misconfigured `cost` callable can be a denial-of-service vector
   against your *own* users.** If `cost=lambda request: ...` reads
   attacker-controlled input without bounds (e.g. an unvalidated "count"
   field), a malicious request could claim an enormous cost, exhausting
   a shared budget for other users under the same key. Validate/clamp any
   request-derived cost value.
5. **This package doesn't rate-limit at the network/connection level.**
   A sufficiently large flood of *distinct* identities (e.g. a botnet with
   thousands of IPs, each under the per-IP threshold) isn't caught by a
   per-identity limiter — that's a job for infrastructure-level DDoS
   protection (a CDN, a WAF, `iptables`/`nftables` rate limiting), not an
   application-layer library like this one.

## Recommended production configuration

```python
RATELIMIT_PLUS = {
    "REDIS_URL": "redis://ratelimit-redis.internal:6379/3",  # dedicated instance/DB
}
```

- Use a Redis instance/logical DB dedicated to rate limiting, separate
  from your caching/session store, so a rate-limiting incident (e.g.
  unexpectedly high key volume) can't degrade unrelated Redis usage.
- Set conservative default limits on authentication and password-reset
  endpoints specifically (see
  [Common Patterns](common-patterns.md#loginauth-endpoints-strict-per-ip-limiting)).
- Prefer `key="user"` (falls back to IP for anonymous requests) over bare
  `key="ip"` wherever authentication is available, since it's harder for
  a single attacker to acquire many distinct authenticated accounts than
  many distinct IPs.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-ratelimit-plus/blob/main/SECURITY.md).

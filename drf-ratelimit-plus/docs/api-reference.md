# API Reference

Generated in part from source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/).

## Throttles

### rate_limit

::: drf_ratelimit_plus.throttles.rate_limit

### RateLimitThrottle

::: drf_ratelimit_plus.throttles.RateLimitThrottle

## Decorator

### ratelimit

::: drf_ratelimit_plus.decorators.ratelimit

## Headers

### RateLimitHeadersMixin

::: drf_ratelimit_plus.mixins.RateLimitHeadersMixin

## Keys

### by_ip

::: drf_ratelimit_plus.keys.by_ip

### by_user

::: drf_ratelimit_plus.keys.by_user

### by_api_key

::: drf_ratelimit_plus.keys.by_api_key

### by_tenant

::: drf_ratelimit_plus.keys.by_tenant

### by_view

::: drf_ratelimit_plus.keys.by_view

### combine

::: drf_ratelimit_plus.keys.combine

### resolve_key_func

::: drf_ratelimit_plus.keys.resolve_key_func

## Rates

### Rate

::: drf_ratelimit_plus.rates.Rate

### parse_rate

::: drf_ratelimit_plus.rates.parse_rate

## Tiers

### default_tier_resolver

::: drf_ratelimit_plus.tiers.default_tier_resolver

### resolve_tier_rate

::: drf_ratelimit_plus.tiers.resolve_tier_rate

## Algorithms

### fixed_window_check

::: drf_ratelimit_plus.algorithms.fixed_window_check

### sliding_window_check

::: drf_ratelimit_plus.algorithms.sliding_window_check

### token_bucket_check

::: drf_ratelimit_plus.algorithms.token_bucket_check

## Results

### LimitResult

::: drf_ratelimit_plus.results.LimitResult

## Client

### get_redis_client

::: drf_ratelimit_plus.client.get_redis_client

### set_redis_client

::: drf_ratelimit_plus.client.set_redis_client

## Exceptions

### RateLimitPlusError

::: drf_ratelimit_plus.exceptions.RateLimitPlusError

### InvalidRateError

::: drf_ratelimit_plus.exceptions.InvalidRateError

### InvalidKeyError

::: drf_ratelimit_plus.exceptions.InvalidKeyError

### InvalidAlgorithmError

::: drf_ratelimit_plus.exceptions.InvalidAlgorithmError

### UnknownTierError

::: drf_ratelimit_plus.exceptions.UnknownTierError

## Settings

See [Settings](settings.md) for the full list of recognized
`RATELIMIT_PLUS` keys.

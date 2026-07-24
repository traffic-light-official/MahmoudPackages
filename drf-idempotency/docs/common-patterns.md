# Common Patterns

## Payment/order creation

The canonical use case: a client generates a UUID once per checkout
attempt and reuses it across retries. See
[Examples](examples.md#client-side-retry-logic).

## Webhook delivery deduplication

If you receive webhooks from a third party that includes its own
delivery ID, forward that ID as the `Idempotency-Key` on your internal
processing endpoint, so a webhook redelivery (common with most providers
after a timeout) doesn't reprocess the event twice:

```python
class WebhookView(APIView):
    def post(self, request):
        # Some providers put the ID in a header; adapt as needed.
        request.META["HTTP_IDEMPOTENCY_KEY"] = request.headers["X-Provider-Delivery-Id"]
        return super().post(request)
```

## Idempotent background job triggers

If an API endpoint's job is to enqueue a background task (rather than do
work synchronously), idempotency still matters — you don't want a retried
request to enqueue the task twice:

```python
class TriggerReportView(APIView):
    def post(self, request):
        job_id = generate_report.delay(request.data["report_type"]).id
        return Response({"job_id": job_id}, status=202)
```

Wrapped in `@idempotent()`, a retry replays the *same* `job_id` rather
than enqueueing a second job.

## Combining with rate limiting

Idempotency and rate limiting solve different problems and compose
without conflict: apply your rate limiter (e.g. `drf-ratelimit-plus`) as
you normally would — a request that gets replayed from cache never even
reaches your view body, but it's still a real HTTP request that should
count against a client's rate limit the same as any other. Order the
middleware however you'd naturally reason about precedence (typically
rate limiting first, so an already-rate-limited client doesn't even reach
idempotency handling).

## Testing idempotent client code

If you're writing the *client* side (not just the API), test that your
retry logic reuses one key across attempts rather than generating a new
one per HTTP call — this is the single most common integration mistake:

```python
def test_retry_reuses_the_same_key(mocker):
    mock_post = mocker.patch("requests.post")
    create_payment_with_retries(amount=100)
    keys_used = {call.kwargs["headers"]["Idempotency-Key"] for call in mock_post.call_args_list}
    assert len(keys_used) == 1
```

## Exposing idempotency status to end users

For a long-running operation, let users check status without resubmitting
— see [Examples](examples.md#checking-status-without-resending-the-request).
Combine with a documented convention (e.g. echoing the key back in your
`201` response) so clients always know which key to check.

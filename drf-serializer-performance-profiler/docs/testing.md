# Testing

## Running this package's own test suite

```bash
pip install -e ".[test]"
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

Across the full Python/Django support matrix via [tox](https://tox.wiki):

```bash
tox
```

## Proving the mixin never changes serialized output

This is the single most important property to test if you extend or
modify this package (see
[Architecture](architecture.md#the-core-guarantee-identical-output-to-a-plain-serializer)).
This package's own `tests/test_mixins.py::TestOutputIsUnchanged`
demonstrates the pattern: assert byte-identical `.data` both against a
disabled-profiler run of the same serializer, and against a completely
separate, undecorated `ModelSerializer`.

```python
def test_output_matches_a_plain_modelserializer(make_article):
    article = make_article(comment_count=2)
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        profiled_data = ArticleSerializer(article).data
    plain_data = PlainArticleSerializer(article).data  # no mixin at all
    assert dict(profiled_data) == dict(plain_data)
```

## Testing per-field query counts precisely

Query counts are fully deterministic (unlike timing, which varies by
machine) - assert them exactly:

```python
def test_comment_count_query_count(make_article):
    article = make_article(comment_count=4)
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        serializer = ArticleSerializer(article)
        _ = serializer.data

    profile = get_serializer_profile(serializer)
    assert profile.fields["comment_count"].query_count == 1
    assert profile.fields["title"].query_count == 0
```

Avoid asserting exact timing values in tests - real elapsed time
depends on the machine running the suite. If you need a deterministic
test for `LOG_SLOW_FIELDS`, set `SLOW_FIELD_THRESHOLD_MS` to `0.0`
(guarantees a log fires regardless of actual timing) or an extremely
high value (guarantees it never does), rather than depending on a
real-world timing threshold.

```python
def test_logs_a_warning_regardless_of_actual_timing(make_article, caplog):
    article = make_article(comment_count=1)
    with (
        override_settings(
            SERIALIZER_PROFILER={"LOG_SLOW_FIELDS": True, "SLOW_FIELD_THRESHOLD_MS": 0.0}
        ),
        caplog.at_level(logging.WARNING, logger="drf_serializer_performance_profiler"),
    ):
        _ = ArticleSerializer(article).data
    assert any("comment_count" in record.message for record in caplog.records)
```

## Testing list-view aggregation

Remember the profile is recorded on the `ListSerializer`'s `.child`,
not the `ListSerializer` instance itself (see
[Architecture](architecture.md#why-get_serializer-must-handle-a-listserializers-child-specially)):

```python
def test_many_true_aggregates_across_every_row():
    serializer = ArticleSerializer(Article.objects.all(), many=True)
    _ = serializer.data
    profile = get_serializer_profile(serializer.child)  # .child, not serializer itself
    assert profile.fields["comment_count"].call_count == Article.objects.count()
```

## Testing the header end-to-end

```python
def test_staff_user_sees_the_header(api_client, make_user, make_article):
    staff = make_user(is_staff=True)
    api_client.force_authenticate(user=staff)
    article = make_article(comment_count=3)
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        response = api_client.get(f"/articles/{article.pk}/")
    assert "comment_count=" in response.headers["X-Serializer-Profile"]
```

Forgetting either `ENABLED: True` or a staff user is the most common
reason a header test fails with a `KeyError` on the header lookup -
see [Troubleshooting](troubleshooting.md).

## Fixtures used by this package's own suite

`tests/test_app` declares `Author`/`Article`/`Comment` models and an
`ArticleSerializer` whose `comment_count`
(`SerializerMethodField`) deliberately queries the database once per
instance - a realistic, deterministic N+1-shaped field for testing
query counting precisely, without relying on real timing at all -
reuse this shape in your own project's test suite.

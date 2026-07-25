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

## Testing both atomic and non-atomic behavior explicitly

Since `ATOMIC` is a project-wide setting, most projects only exercise
one mode in normal use - but it's worth testing both code paths for any
viewset where the choice actually matters, using
`@override_settings`/`override_settings()`:

```python
from django.test import override_settings


def test_atomic_batch_with_one_bad_item_saves_nothing(api_client, make_author):
    author = make_author()
    response = api_client.post(
        "/articles/bulk/",
        [{"title": "Good", "author": author.pk}, {"title": "", "author": author.pk}],
        format="json",
    )
    assert response.status_code == 400
    assert Article.objects.count() == 0


def test_non_atomic_batch_with_one_bad_item_saves_the_rest(api_client, make_author):
    author = make_author()
    with override_settings(BULK_OPERATIONS={"ATOMIC": False}):
        response = api_client.post(
            "/articles/bulk/",
            [{"title": "Good", "author": author.pk}, {"title": "", "author": author.pk}],
            format="json",
        )
    assert response.status_code == 207
    assert Article.objects.count() == 1
```

## Testing a real database-level failure, not just a validation error

Validation errors (blank fields, wrong types) are the easy case -
they're caught before any database write, in both modes. The more
interesting failure mode is a real `django.db.DatabaseError` raised
*during* save, after validation already passed - this package's own
test suite (`tests/test_db_errors.py`) demonstrates two ways to trigger
this deterministically:

1. **A genuine within-batch conflict**: two items whose values don't
   conflict with anything currently in the database, but do conflict
   with *each other* once both are written in the same transaction
   (e.g. the same value for a `unique=True` field) - see
   `tests/test_bulk_create.py`'s
   `test_within_batch_duplicate_title_rolls_back_the_whole_batch`.
2. **A sentinel-triggered override**: a small test-only viewset
   subclass whose `perform_create`/`perform_update`/`perform_destroy`
   raises `django.db.IntegrityError` deterministically for one specific
   input value, when there's no natural database constraint to trigger
   the same failure:

```python
from django.db import IntegrityError


class _FlakySaveViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def perform_create(self, serializer):
        if serializer.validated_data.get("title") == "trigger-db-error":
            raise IntegrityError("simulated failure")
        serializer.save()
```

Prefer option 1 when a real constraint naturally produces the failure
you're testing (it proves the actual database behavior, not just that
your `except DatabaseError` branch runs); reach for option 2 only when
there's no such natural trigger.

## Testing object-level permission denial on bulk update/destroy

```python
from rest_framework.permissions import BasePermission
from rest_framework.test import APIRequestFactory


class _DenyObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return False


def test_denied_object_permission_returns_403(make_article):
    article = make_article()

    class _DeniedViewSet(BulkModelViewSet):
        permission_classes = [_DenyObjectPermission]
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer

    request = APIRequestFactory().delete("/x/bulk-delete/", [article.pk], format="json")
    response = _DeniedViewSet.as_view({"delete": "bulk_destroy"})(request)
    assert response.status_code == 403
```

## Fixtures used by this package's own suite

`tests/test_app` declares `Author`/`Article` models (`Article.title` is
`unique=True`, so tests can exercise the `UniqueValidator`/
`IntegrityError` distinction described in
[Architecture](architecture.md)) and one `ArticleViewSet`
(`BulkModelViewSet`) registered on a real `DefaultRouter` - reuse this
shape, including `api_client`/`make_author`/`make_article` fixtures in
`conftest.py`, in your own project's test suite.

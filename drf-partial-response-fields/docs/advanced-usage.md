# Advanced Usage

## Optimizing `SerializerMethodField`

A method field has no direct mapping to a model column, so the optimizer
can't infer what it needs. Declare it explicitly with `requires_related`:

```python
from drf_partial_response_fields import requires_related


class ArticleSerializer(PartialFieldsModelSerializer):
    editor_note = serializers.SerializerMethodField()

    @requires_related(select_related=["editor__profile"])
    def get_editor_note(self, obj):
        return f"Reviewed by {obj.editor.profile.display_name}"
```

When `editor_note` is requested, the optimizer adds `editor__profile` to
`select_related` on the queryset — but only then, so unrelated requests
that don't need `editor_note` don't pay for the extra join. You can declare
`prefetch_related` paths the same way:

```python
@requires_related(prefetch_related=["tags", "comments__author"])
def get_summary(self, obj):
    ...
```

## Plain `APIView` integration

`PartialResponseMixin` needs `get_queryset()` / `get_serializer_class()` /
`get_serializer_context()` to hook into, which plain `APIView` doesn't
provide. Wire it up manually with `parse_request_fields`:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_partial_response_fields import parse_request_fields
from drf_partial_response_fields.mixins import PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY


class ArticleDetailView(APIView):
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        serializer = ArticleSerializer(
            article,
            context={
                "request": request,
                PARTIAL_RESPONSE_FIELDS_CONTEXT_KEY: parse_request_fields(request),
            },
        )
        return Response(serializer.data)
```

This gets you output filtering; automatic queryset optimization is a
`GenericAPIView`-only feature (there's no generic `get_queryset()` to hook
into on a plain `APIView`). If you need it, call
`drf_partial_response_fields.optimize_queryset()` yourself:

```python
from drf_partial_response_fields import optimize_queryset

tree = parse_request_fields(request)
queryset = optimize_queryset(Article.objects.all(), ArticleSerializer, tree)
```

## OpenAPI documentation

Install the `openapi` extra first: `pip install drf-partial-response-fields[openapi]`.

**Per-view**, using `@extend_schema`:

```python
from drf_spectacular.utils import extend_schema
from drf_partial_response_fields.openapi import fields_query_parameter


@extend_schema(parameters=[fields_query_parameter()])
class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    ...
```

**Automatically, for every action**, using a custom `AutoSchema`:

```python
from drf_partial_response_fields.openapi import PartialResponseAutoSchema


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    schema = PartialResponseAutoSchema()
    ...
```

## Custom query parameter name

```python
PARTIAL_RESPONSE_FIELDS = {"QUERY_PARAM": "select"}
```

```
GET /articles/?select=title,author(name)
```

## Restricting depth for untrusted clients

If your API is public and you want to bound worst-case parsing/optimization
cost regardless of what a client sends:

```python
PARTIAL_RESPONSE_FIELDS = {"MAX_DEPTH": 3, "MAX_FIELDS_LENGTH": 500}
```

## Combining with `django-filter` / custom `get_queryset()`

`PartialResponseMixin.get_queryset()` calls `super().get_queryset()`
first, then optimizes the result. It composes cleanly with any other
`get_queryset()` override earlier in the MRO (filtering, ordering,
tenant scoping, ...):

```python
class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilterSet  # django-filter

    def get_queryset(self):
        # Any additional narrowing here still gets optimized afterward,
        # since PartialResponseMixin.get_queryset() runs after this
        # via super() in the MRO — put PartialResponseMixin first.
        return super().get_queryset().filter(is_published=True)
```

Because `PartialResponseMixin` is listed first in the class bases, its
`get_queryset()` runs *last* in the MRO chain when you also override
`get_queryset()` on the view itself — Python's MRO calls the most-derived
`get_queryset()` first, and each override's `super().get_queryset()` call
walks toward the base class. In the example above, the view's own override
is the most-derived, so it runs first and calls `super().get_queryset()`
which reaches `PartialResponseMixin.get_queryset()`, which itself calls
`super().get_queryset()` to reach `ModelViewSet`'s default. The net effect:
`ModelViewSet` gives you `Article.objects.all()`, `PartialResponseMixin`
optimizes it, and *then* your `.filter(is_published=True)` is applied on
top — meaning the optimization was computed before your extra filter. This
is safe (optimization doesn't change query *results*, only which columns
and joins are fetched), but keep in mind any relations referenced only by
your custom `.filter()` are not automatically added to `select_related` —
Django resolves query-only lookups without needing the relation object
materialized.

## Testing views that use `PartialResponseMixin`

See [Testing](testing.md#testing-views-with-partialresponsemixin) for
patterns using `APIRequestFactory` and `rest_framework.test.APIClient`.

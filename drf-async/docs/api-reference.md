# API Reference

This page documents every public class and function. It is generated
in part from the source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/) - the same text you'll
see in your editor's tooltips.

## Views

### AsyncAPIView

::: drf_async.views.AsyncAPIView

## Generic views

### AsyncGenericAPIView

::: drf_async.generics.AsyncGenericAPIView

### Concrete generic views

Nine concrete views, each a one-line delegation to the matching mixin
action - identical in shape to `rest_framework.generics`'s own
`ListAPIView`/`CreateAPIView`/etc.

::: drf_async.generics.AsyncListAPIView

::: drf_async.generics.AsyncCreateAPIView

::: drf_async.generics.AsyncRetrieveAPIView

::: drf_async.generics.AsyncUpdateAPIView

::: drf_async.generics.AsyncDestroyAPIView

::: drf_async.generics.AsyncListCreateAPIView

::: drf_async.generics.AsyncRetrieveUpdateAPIView

::: drf_async.generics.AsyncRetrieveDestroyAPIView

::: drf_async.generics.AsyncRetrieveUpdateDestroyAPIView

## Mixins

### AsyncListModelMixin

::: drf_async.mixins.AsyncListModelMixin

### AsyncCreateModelMixin

::: drf_async.mixins.AsyncCreateModelMixin

### AsyncRetrieveModelMixin

::: drf_async.mixins.AsyncRetrieveModelMixin

### AsyncUpdateModelMixin

::: drf_async.mixins.AsyncUpdateModelMixin

### AsyncDestroyModelMixin

::: drf_async.mixins.AsyncDestroyModelMixin

## Viewsets

### AsyncGenericViewSet

::: drf_async.viewsets.AsyncGenericViewSet

### AsyncReadOnlyModelViewSet

::: drf_async.viewsets.AsyncReadOnlyModelViewSet

### AsyncModelViewSet

::: drf_async.viewsets.AsyncModelViewSet

## Permissions

### BaseAsyncPermission

::: drf_async.permissions.BaseAsyncPermission

### check_permission

::: drf_async.permissions.check_permission

### check_object_permission

::: drf_async.permissions.check_object_permission

## Throttling

### BaseAsyncThrottle

::: drf_async.throttling.BaseAsyncThrottle

### AsyncSimpleRateThrottle

::: drf_async.throttling.AsyncSimpleRateThrottle

### AsyncAnonRateThrottle

::: drf_async.throttling.AsyncAnonRateThrottle

### AsyncUserRateThrottle

::: drf_async.throttling.AsyncUserRateThrottle

### check_throttle

::: drf_async.throttling.check_throttle

### wait_for_throttle

::: drf_async.throttling.wait_for_throttle

## Sync/async bridging primitives

These are the low-level building blocks the classes above are built
on - most projects never call them directly, but they're public and
useful when writing your own async-aware DRF extension.

### is_async_callable

::: drf_async.compat.is_async_callable

### call_maybe_async

::: drf_async.compat.call_maybe_async

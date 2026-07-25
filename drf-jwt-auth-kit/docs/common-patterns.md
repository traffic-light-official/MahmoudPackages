# Common Patterns

## Showing "this device" in a device list

The `DeviceViewSet` list response marks the device the current request
authenticated with via `is_current`, derived from the access token's own
`device_id` claim (`request.auth["device_id"]`):

```json
[
  {"id": "3fa8...", "label": "Chrome on macOS", "is_current": true},
  {"id": "9c1a...", "label": "iPhone 15", "is_current": false}
]
```

```jsx
{devices.map((d) => (
  <DeviceRow key={d.id} device={d} highlighted={d.is_current} />
))}
```

## Forcing re-login after a password change

Revoke every device whenever a user changes their password, so a
previously-issued refresh token (which does not know the password
changed) cannot keep the old session alive:

```python
from drf_jwt_auth_kit.constants import REVOKED_REASON_LOGOUT_ALL
from drf_jwt_auth_kit.devices import revoke_all_devices


def change_password(user, new_password):
    user.set_password(new_password)
    user.save()
    revoke_all_devices(user, reason=REVOKED_REASON_LOGOUT_ALL)
```

## Naming a device from the client

Pass a human-readable label at login time:

```json
{"username": "ada", "password": "hunter2", "device_label": "Ada's MacBook Pro"}
```

A good default if the client does not supply one is to derive something
from the `User-Agent` server-side - this package stores the raw
`user_agent` on every `Device` regardless, so you can always fall back
to parsing it for display if `label` is blank.

## Testing that a view requires authentication

```python
def test_protected_view_requires_a_token(api_client):
    response = api_client.get("/api/articles/")
    assert response.status_code == 401


def test_protected_view_works_with_a_valid_token(api_client, user, device):
    from drf_jwt_auth_kit.tokens import encode_access_token

    token = encode_access_token(user_id=user.pk, device_id=device.pk)
    response = api_client.get("/api/articles/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
```

## Detecting and alerting on reuse

`TokenReuseDetectedError` is a strong signal of a stolen refresh token.
Wire up an alert alongside the shipped `RefreshView`'s handling by
subscribing to `LoginHistory`/`Device.revoked_reason ==
"reuse_detected"` in a periodic check, or wrap
`rotate_refresh_token()` yourself if you need synchronous alerting - see
[Advanced Usage](advanced-usage.md#custom-exception-mapping-for-reuse-detection).

## Rate limiting login attempts

This package does not rate-limit `/auth/login/` itself (that is a
cross-cutting concern better handled by a dedicated package or your
edge/gateway). Pair it with `drf-ratelimit-plus` (a sibling package) by
subclassing `LoginView` and setting `throttle_classes`, since
`LoginView` is a class-based view:

```python
# myproject/views.py
from drf_ratelimit_plus.throttles import rate_limit
from drf_jwt_auth_kit.views import LoginView


class RateLimitedLoginView(LoginView):
    throttle_classes = [rate_limit(rate="5/m", key="ip")]
```

```python
# urls.py
urlpatterns = [
    path("auth/login/", RateLimitedLoginView.as_view(), name="login"),
    # ... the rest of drf_jwt_auth_kit.urls' patterns, or include() the
    # rest of the package's urls.py and override just this one route.
]
```

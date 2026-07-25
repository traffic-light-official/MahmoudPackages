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

## Testing an authenticated view

Build a valid access token directly rather than going through the full
login flow, when the test isn't about login itself:

```python
from drf_jwt_auth_kit.models import Device
from drf_jwt_auth_kit.tokens import encode_access_token


def test_protected_endpoint(api_client, user):
    device = Device.objects.create(user=user)
    token = encode_access_token(user_id=user.pk, device_id=device.pk)

    response = api_client.get("/api/articles/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
```

## Testing the full login/refresh/logout cycle

```python
def test_login_then_refresh(api_client, user):
    login_response = api_client.post(
        "/auth/login/", {"username": "ada", "password": "..."}, format="json"
    )
    csrf_token = api_client.cookies["refresh_csrftoken"].value

    refresh_response = api_client.post(
        "/auth/refresh/", HTTP_X_REFRESH_CSRFTOKEN=csrf_token
    )

    assert refresh_response.status_code == 200
    assert refresh_response.data["access_token"] != login_response.data["access_token"]
```

Remember that **every** cookie-setting response (login, refresh) issues
a fresh CSRF cookie - always re-read `api_client.cookies["refresh_csrftoken"]`
immediately before the next cookie-authenticated request rather than
reusing a value captured earlier in the test, or you will get a 403
instead of the response you're actually testing.

## Testing reuse detection

```python
def test_replayed_refresh_token_is_rejected(api_client, user):
    api_client.post("/auth/login/", {"username": "ada", "password": "..."}, format="json")
    csrf = api_client.cookies["refresh_csrftoken"].value
    old_refresh_cookie = api_client.cookies["refresh_token"].value

    api_client.post("/auth/refresh/", HTTP_X_REFRESH_CSRFTOKEN=csrf)  # rotates

    api_client.cookies["refresh_token"] = old_refresh_cookie  # simulate replay
    response = api_client.post(
        "/auth/refresh/", HTTP_X_REFRESH_CSRFTOKEN=api_client.cookies["refresh_csrftoken"].value
    )

    assert response.status_code == 401
```

## Testing TOTP without waiting 30 seconds

Generate the code directly against the same secret rather than
interacting with a real authenticator app:

```python
from drf_jwt_auth_kit.mfa import generate_totp_code, generate_totp_secret
from drf_jwt_auth_kit.models import TOTPDevice


def test_login_with_mfa(api_client, user):
    secret = generate_totp_secret()
    TOTPDevice.objects.create(user=user, secret=secret, confirmed=True)

    response = api_client.post(
        "/auth/login/",
        {"username": "ada", "password": "...", "mfa_code": generate_totp_code(secret)},
        format="json",
    )

    assert response.status_code == 200
```

## Freezing time carefully

If you use `freezegun` to test lifetime/expiry behavior, freeze to a
*relative* offset (`timezone.now() + timedelta(...)`), not a fixed
absolute date - jumping to an arbitrary calendar date can land past an
unrelated token's own expiry and fail the test for the wrong reason.

## Fixtures used by this package's own suite

`tests/conftest.py` provides `api_rf`, `api_client`, `user`,
`other_user`, `device`, and `authenticated_client` fixtures - copy this
pattern into your own project's `conftest.py` if you do not already have
equivalents.

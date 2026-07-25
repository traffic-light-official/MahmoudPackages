# Examples

A runnable server-side example (models, serializers, a protected
`ArticleViewSet`) lives in
[`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-jwt-auth-kit/examples/blog)
in the repository. This page focuses on the client side.

## SPA (JavaScript) client

A same-origin single-page app talking to the API on the same domain
(cookies work automatically with `credentials: "same-origin"`, the
`fetch()` default):

```javascript
let accessToken = null;

async function login(username, password) {
  const response = await fetch("/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const data = await response.json();
    if (data.mfa_required) return { mfaRequired: true };
    throw new Error("Login failed");
  }
  const data = await response.json();
  accessToken = data.access_token;
  return { device: data.device };
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function refresh() {
  const response = await fetch("/auth/refresh/", {
    method: "POST",
    headers: { "X-Refresh-CSRFToken": getCookie("refresh_csrftoken") },
  });
  if (!response.ok) {
    accessToken = null; // force the user back to the login screen
    throw new Error("Session expired");
  }
  const data = await response.json();
  accessToken = data.access_token;
}

async function apiFetch(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${accessToken}` },
  });
  if (response.status === 401) {
    await refresh();
    response = await fetch(url, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${accessToken}` },
    });
  }
  return response;
}

async function logout() {
  await fetch("/auth/logout/", {
    method: "POST",
    headers: { "X-Refresh-CSRFToken": getCookie("refresh_csrftoken") },
  });
  accessToken = null;
}
```

## Cross-site SPA (different domain than the API)

Set `credentials: "include"` on every call, and configure the server
for cross-site cookies (see
[Configuration](configuration.md#cross-site-spa-on-a-different-domain-deployments)):

```javascript
const response = await fetch("https://api.example.com/auth/login/", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
```

Every subsequent call (`refresh`, `logout`, and any `apiFetch`-style
wrapper) needs `credentials: "include"` too, or the browser will not
send the refresh cookie.

## Mobile client (no cookie jar)

Native mobile HTTP clients typically do maintain a cookie jar (both
`URLSession` on iOS and `OkHttp`/`Cronet` on Android do by default), so
the cookie-based flow above works unchanged in most cases. If your
client deliberately does not use cookies, store the refresh token
yourself in the platform keychain/keystore and send it explicitly - a
minimal companion header-based refresh path is a straightforward
addition on top of `drf_jwt_auth_kit.rotation.rotate_refresh_token()`
directly:

```python
# myproject/views.py - a header-based refresh endpoint for cookie-less clients
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from drf_jwt_auth_kit.exceptions import (
    DeviceRevokedError, InvalidTokenError, TokenExpiredError, TokenReuseDetectedError,
)
from drf_jwt_auth_kit.rotation import rotate_refresh_token


class MobileRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request):
        raw_refresh_token = request.data.get("refresh_token")
        if not raw_refresh_token:
            return Response({"detail": "refresh_token is required."}, status=400)
        try:
            pair = rotate_refresh_token(raw_refresh_token)
        except (TokenExpiredError, InvalidTokenError, DeviceRevokedError, TokenReuseDetectedError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"access_token": pair.access_token, "refresh_token": pair.refresh_token})
```

Store the returned `refresh_token` in the Keychain (iOS) or
EncryptedSharedPreferences/Keystore (Android) - never in plain
`UserDefaults`/`SharedPreferences`, and never in application logs.

## Kotlin (Android) sketch

```kotlin
suspend fun login(username: String, password: String): LoginResult {
    val response = httpClient.post("$baseUrl/auth/login/") {
        contentType(ContentType.Application.Json)
        setBody(LoginRequest(username, password))
    }
    val body = response.body<LoginResponse>()
    accessToken = body.accessToken
    // OkHttp's CookieJar already captured the httpOnly refresh cookie.
    return LoginResult(body.device)
}
```

## Swift (iOS) sketch

```swift
func login(username: String, password: String) async throws -> LoginResponse {
    var request = URLRequest(url: baseURL.appending(path: "/auth/login/"))
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try JSONEncoder().encode(LoginRequest(username: username, password: password))
    // URLSession's shared HTTPCookieStorage captures the httpOnly refresh cookie automatically.
    let (data, _) = try await session.data(for: request)
    return try JSONDecoder().decode(LoginResponse.self, from: data)
}
```

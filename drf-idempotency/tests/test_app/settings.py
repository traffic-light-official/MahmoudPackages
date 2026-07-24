"""Minimal Django settings for running the test suite."""

from __future__ import annotations

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_idempotency",
    "tests.test_app",
]

MIDDLEWARE = [
    "drf_idempotency.middleware.IdempotencyMiddleware",
]

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
}

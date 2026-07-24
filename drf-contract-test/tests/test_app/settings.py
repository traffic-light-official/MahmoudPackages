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
    "drf_spectacular",
    "tests.test_app",
]

MIDDLEWARE: list[str] = []

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Test App API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

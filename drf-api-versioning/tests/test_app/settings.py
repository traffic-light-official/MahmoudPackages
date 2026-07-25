"""Minimal Django settings for running the test suite."""

from __future__ import annotations

import datetime

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
USE_TZ = True
ALLOWED_HOSTS = ["*"]

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
    "drf_api_versioning",
    "tests.test_app",
]

MIDDLEWARE: list[str] = []

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# v1: deprecated and sunset, both safely in the past regardless of when
# the test suite actually runs. v2: deprecated but not yet sunset. v3:
# fully supported, the default.
API_VERSIONING = {
    "VERSIONS": {
        "v1": {
            "deprecated": datetime.date(2020, 1, 1),
            "sunset": datetime.date(2020, 6, 1),
            "deprecation_link": "https://example.com/docs/migrating-to-v3",
        },
        "v2": {
            "deprecated": datetime.date(2020, 1, 1),
        },
        "v3": {},
    },
    "DEFAULT_VERSION": "v3",
}

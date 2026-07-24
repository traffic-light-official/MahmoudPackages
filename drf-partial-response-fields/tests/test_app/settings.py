"""Minimal Django settings for running the test suite."""

from __future__ import annotations

import importlib.util

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
    "tests.test_app",
]

# drf-spectacular is an optional extra of the package under test; only wire
# it into INSTALLED_APPS when it's actually installed, so the suite still
# runs (minus the OpenAPI tests, which self-skip) without the extra.
if importlib.util.find_spec("drf_spectacular") is not None:
    INSTALLED_APPS.append("drf_spectacular")
    SPECTACULAR_SETTINGS = {
        "TITLE": "Test API",
        "VERSION": "1.0.0",
    }

MIDDLEWARE: list[str] = []

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

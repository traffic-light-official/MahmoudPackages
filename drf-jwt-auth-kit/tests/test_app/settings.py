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
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "drf_jwt_auth_kit",
    "tests.test_app",
]

if importlib.util.find_spec("drf_spectacular") is not None:
    INSTALLED_APPS.append("drf_spectacular")
    SPECTACULAR_SETTINGS = {"TITLE": "Test API", "VERSION": "1.0.0"}

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "drf_jwt_auth_kit.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Local development over plain HTTP in the test client - never do this in production.
# MFA_PROVIDER is TOTPProvider so tests can exercise the real MFA flow simply by
# creating a confirmed TOTPDevice row for a user (it stays a no-op otherwise).
JWT_AUTH_KIT = {
    "REFRESH_COOKIE_SECURE": False,
    "MFA_PROVIDER": "drf_jwt_auth_kit.mfa.TOTPProvider",
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

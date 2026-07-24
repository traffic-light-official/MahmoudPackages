"""Minimal Django settings for running the test suite."""

from __future__ import annotations

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
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "tests.test_app",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "drf_multitenant.middleware.TenantMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

MULTITENANT = {
    "TENANT_MODEL": "test_app.Tenant",
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
    "drf_file_pipeline",
]

MIDDLEWARE: list[str] = []

ROOT_URLCONF = "tests.test_app.urls"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

FILE_PIPELINE = {
    "BUCKET_NAME": "test-bucket",
    "AWS_REGION": "us-east-1",
    "MULTIPART_THRESHOLD": 10 * 1024 * 1024,
    "MULTIPART_CHUNK_SIZE": 5 * 1024 * 1024,
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

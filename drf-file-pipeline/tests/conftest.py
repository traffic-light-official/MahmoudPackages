"""Shared pytest fixtures for the test suite.

S3 is mocked via ``moto`` — no real AWS credentials or network access
are used or required.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import boto3
import pytest
from moto import mock_aws
from rest_framework.test import APIClient

from drf_file_pipeline.storage import S3StorageBackend

if TYPE_CHECKING:
    # boto3-stubs[s3] is a dev-only dependency, not part of the `test`
    # extra CI's test matrix installs — only import this for type
    # checking, never at runtime.
    from mypy_boto3_s3.client import S3Client
else:
    S3Client = Any

_BUCKET_NAME = "test-bucket"
_REGION = "us-east-1"


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", _REGION)


@pytest.fixture
def s3_client() -> Iterator[S3Client]:
    with mock_aws():
        client: S3Client = boto3.client("s3", region_name=_REGION)
        client.create_bucket(Bucket=_BUCKET_NAME)
        yield client


@pytest.fixture
def storage(s3_client: S3Client) -> S3StorageBackend:
    return S3StorageBackend(bucket_name=_BUCKET_NAME, client=s3_client)


@pytest.fixture
def client() -> APIClient:
    return APIClient()

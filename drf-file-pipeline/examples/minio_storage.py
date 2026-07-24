"""A custom S3-compatible backend (MinIO). See ``docs/examples.md``."""

from __future__ import annotations

import boto3

from drf_file_pipeline.storage import S3StorageBackend


class MinIOStorageBackend(S3StorageBackend):
    def __init__(self) -> None:
        client = boto3.client(
            "s3",
            endpoint_url="https://minio.internal:9000",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
        )
        super().__init__(client=client)

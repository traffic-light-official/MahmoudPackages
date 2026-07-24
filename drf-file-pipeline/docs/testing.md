# Testing

This page covers testing your own project's use of
`drf-file-pipeline`. For running this package's own test suite, see
[Contributing](contributing.md).

## Mocking S3 with `moto`

This package's own tests mock S3 entirely via
[`moto`](https://github.com/getmoto/moto)'s `mock_aws()` — no real AWS
account, network access, or credentials are needed. Use the same
approach in your project's tests:

```python
# conftest.py
import boto3
import pytest
from moto import mock_aws

@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test-bucket")
        yield client
```

Make sure `FILE_PIPELINE["BUCKET_NAME"]` in your test settings matches
the bucket name you create in the fixture.

## Testing the initiate/complete flow

```python
def test_small_upload_flow(client, s3_bucket):
    response = client.post(
        "/uploads/initiate/",
        data={"filename": "a.txt", "content_type": "text/plain", "size": 100},
    )
    assert response.status_code == 201
    upload_id = response.json()["upload"]["id"]

    complete = client.post(f"/uploads/{upload_id}/complete/")
    assert complete.status_code == 200
    assert complete.json()["status"] == "uploaded"
```

Note the flow doesn't actually upload bytes to the presigned POST URL
in this test — `complete/` only cares that the client says it's done;
`process_upload()` is what verifies the object actually exists (see
below), matching the real division of responsibility between the HTTP
layer and background processing.

## Testing `process_upload()` directly

Upload real (small) test bytes via the boto3 client directly — no need
to exercise the actual presigned-URL HTTP mechanics to test your own
validation/scanning/preset logic:

```python
def test_processing_generates_thumbnail(s3_bucket, tmp_path):
    upload = FileUpload.objects.create(
        key="uploads/a/photo.png", original_filename="photo.png",
        content_type="image/png", status="uploaded",
    )
    source = tmp_path / "photo.png"
    Image.new("RGB", (400, 300)).save(source, format="PNG")
    s3_bucket.upload_file(str(source), "test-bucket", upload.key)

    with override_settings(FILE_PIPELINE={
        "BUCKET_NAME": "test-bucket",
        "IMAGE_PRESETS": {"thumb": {"width": 100, "height": 100}},
    }):
        result = process_upload(upload.pk)

    assert result.status == "completed"
    assert "thumb" in result.metadata["presets"]
```

## Testing multipart uploads

Simulate the client's direct-to-S3 part upload via the boto3 client,
not a real HTTP `PUT` against the presigned URL — presigning is AWS's
own contract, not something your tests need to re-verify:

```python
def test_multipart_flow(client, s3_bucket):
    initiate = client.post("/uploads/initiate/", data={
        "filename": "big.bin", "content_type": "application/octet-stream",
        "size": 20 * 1024 * 1024,
    })
    upload = initiate.json()["upload"]
    for part_number in range(1, 5):
        response = s3_bucket.upload_part(
            Bucket="test-bucket", Key=upload["key"],
            UploadId=..., PartNumber=part_number, Body=b"x" * (5 * 1024 * 1024),
        )
        client.post(f"/uploads/{upload['id']}/parts/", data={
            "part_number": part_number, "etag": response["ETag"], "size": 5 * 1024 * 1024,
        })
    client.post(f"/uploads/{upload['id']}/complete/")
```

## Testing custom validators and scanners in isolation

Both are plain functions — test them directly without going through the
HTTP layer or `process_upload()` at all:

```python
def test_reject_executables():
    upload = FileUpload(original_filename="virus.exe", content_type="application/octet-stream")
    with pytest.raises(ValidationFailedError):
        reject_executables(upload)
```

## Running this package's own test suite

```bash
git clone https://github.com/mahmoudgshaker/drf-file-pipeline.git
cd drf-file-pipeline
pip install -e ".[dev]"
pytest --cov
```

Tests span storage (against `moto`), models, validation, virus scanning,
image preset rendering (including format-preservation edge cases),
processing orchestration, permissions, serializers, full HTTP request
flows, and the cleanup management command — comfortably above the 90%
coverage floor enforced by `pytest-cov`'s `fail_under` in
`pyproject.toml`.

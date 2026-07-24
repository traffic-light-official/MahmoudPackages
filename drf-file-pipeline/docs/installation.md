# Installation

## Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Django 4.2, 5.0, 5.1, or 5.2
- Django REST Framework 3.14+
- An S3 bucket (or S3-compatible storage — see
  [Advanced Usage](advanced-usage.md) for non-AWS backends) and AWS
  credentials boto3 can discover

## Install from PyPI

```bash
pip install drf-file-pipeline
```

`boto3` and `Pillow` are hard dependencies — both are load-bearing for
this package's core functionality (S3 operations and image preset
generation, respectively), not optional add-ons.

## Add the app

```python
INSTALLED_APPS = [
    ...,
    "drf_file_pipeline",
]
```

Unlike some of this author's other packages, `drf-file-pipeline` *is* a
real Django app — it ships models (`FileUpload`, `UploadPart`) that
track upload lifecycle state, and therefore needs migrations:

```bash
python manage.py migrate drf_file_pipeline
```

## Configure the bucket

```python
FILE_PIPELINE = {
    "BUCKET_NAME": "my-uploads-bucket",
}
```

This is the only setting without a usable default — everything else has
one. See [Settings](settings.md) for the full reference.

## AWS credentials and permissions

The built-in `S3StorageBackend` uses `boto3.client("s3")` with no
credentials passed explicitly — it relies on boto3's standard credential
chain (environment variables, an IAM role, a shared credentials file,
etc.). The IAM identity needs, at minimum:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject", "s3:GetObject", "s3:DeleteObject",
    "s3:ListMultipartUploadParts", "s3:AbortMultipartUpload"
  ],
  "Resource": "arn:aws:s3:::my-uploads-bucket/*"
}
```

## Verify the install

```bash
python -c "import drf_file_pipeline; print(drf_file_pipeline.__version__)"
python manage.py cleanup_abandoned_uploads --dry-run
```

## Development install

```bash
git clone https://github.com/mahmoudgshaker/drf-file-pipeline.git
cd drf-file-pipeline
pip install -e ".[dev]"
```

Tests mock S3 entirely via [`moto`](https://github.com/getmoto/moto) —
no real AWS account or network access is needed to run the suite. See
[Contributing](contributing.md).

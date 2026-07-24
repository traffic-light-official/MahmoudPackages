# API Reference

Generated in part from source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/).

## Models

### FileUpload

::: drf_file_pipeline.models.FileUpload

### UploadPart

::: drf_file_pipeline.models.UploadPart

### UploadStatus

::: drf_file_pipeline.models.UploadStatus

## Storage

### StorageBackend

::: drf_file_pipeline.storage.StorageBackend

### S3StorageBackend

::: drf_file_pipeline.storage.S3StorageBackend

### PresignedPost

::: drf_file_pipeline.storage.PresignedPost

### ObjectInfo

::: drf_file_pipeline.storage.ObjectInfo

### get_storage_backend

::: drf_file_pipeline.storage.get_storage_backend

## Views

### InitiateUploadView

::: drf_file_pipeline.views.InitiateUploadView

### PresignPartView

::: drf_file_pipeline.views.PresignPartView

### ReportPartView

::: drf_file_pipeline.views.ReportPartView

### CompleteUploadView

::: drf_file_pipeline.views.CompleteUploadView

### AbortUploadView

::: drf_file_pipeline.views.AbortUploadView

### FileUploadViewSet

::: drf_file_pipeline.views.FileUploadViewSet

## Serializers

### InitiateUploadSerializer

::: drf_file_pipeline.serializers.InitiateUploadSerializer

### FileUploadSerializer

::: drf_file_pipeline.serializers.FileUploadSerializer

### ReportPartSerializer

::: drf_file_pipeline.serializers.ReportPartSerializer

## Permissions

### IsUploadOwner

::: drf_file_pipeline.permissions.IsUploadOwner

## Validation

### validate_upload

::: drf_file_pipeline.validation.validate_upload

### validate_content_type

::: drf_file_pipeline.validation.validate_content_type

### validate_size

::: drf_file_pipeline.validation.validate_size

## Virus Scanning

### ScanResult

::: drf_file_pipeline.virus_scan.ScanResult

### null_scanner

::: drf_file_pipeline.virus_scan.null_scanner

### scan_upload

::: drf_file_pipeline.virus_scan.scan_upload

## Images

### ImagePreset

::: drf_file_pipeline.images.ImagePreset

### generate_image_presets

::: drf_file_pipeline.images.generate_image_presets

## Processing

### process_upload

::: drf_file_pipeline.processing.process_upload

## Exceptions

### FilePipelineError

::: drf_file_pipeline.exceptions.FilePipelineError

### StorageError

::: drf_file_pipeline.exceptions.StorageError

### ValidationFailedError

::: drf_file_pipeline.exceptions.ValidationFailedError

### VirusDetectedError

::: drf_file_pipeline.exceptions.VirusDetectedError

### InvalidUploadStateError

::: drf_file_pipeline.exceptions.InvalidUploadStateError

## Settings

See [Settings](settings.md) for the full list of recognized
`FILE_PIPELINE` keys.

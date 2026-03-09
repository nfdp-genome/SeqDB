# Staging API

The staging area holds uploaded files before they are linked to samples via bulk submission.

## Upload a file

```
POST /api/v1/staging/upload
```

Requires authentication. Upload files directly — MD5 is computed server-side.

```bash
curl -X POST http://localhost:8000/api/v1/staging/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@SAMPLE_001_R1.fastq.gz"
```

**Response:**
```json
{
  "id": 1,
  "filename": "SAMPLE_001_R1.fastq.gz",
  "file_size": 1234567890,
  "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
  "status": "VERIFIED",
  "upload_method": "direct",
  "created_at": "2026-01-15T10:30:00"
}
```

## List staged files

```
GET /api/v1/staging/files
```

Returns all files staged by the authenticated user.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/staging/files
```

## Delete a staged file

```
DELETE /api/v1/staging/files/{file_id}
```

```bash
curl -X DELETE http://localhost:8000/api/v1/staging/files/42 \
  -H "Authorization: Bearer $TOKEN"
```

## Presigned upload (alternative)

For large files or S3-compatible clients:

### Initiate

```bash
curl -X POST http://localhost:8000/api/v1/staging/initiate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "SAMPLE_001_R1.fastq.gz", "file_size": 1234567890}'
```

**Response:**
```json
{
  "staged_file_id": 1,
  "presigned_url": "http://minio:9000/nfdp-staging/...",
  "staging_path": "user_1/1/SAMPLE_001_R1.fastq.gz",
  "expires_in": 86400
}
```

### Upload to presigned URL

```bash
curl -X PUT "$PRESIGNED_URL" \
  --upload-file SAMPLE_001_R1.fastq.gz
```

### Complete

```bash
curl -X POST http://localhost:8000/api/v1/staging/complete/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Lifecycle

1. **Upload** — File stored in staging bucket
2. **Validation** — Bulk submit matches staged files to sample sheet
3. **Confirmation** — Files linked to runs, marked as "linked"
4. **Cleanup** — Linked files moved to raw storage

!!! info
    Staged files persist across sessions until used or deleted.

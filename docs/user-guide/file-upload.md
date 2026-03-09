# File Staging & Upload

Files must be staged (uploaded to a temporary area) before they can be linked to samples via bulk submission.

## Upload methods

### Browser upload (recommended for < 5 GB)

1. Go to **Submit** → **Bulk Submit** → Step 2 (Upload Files)
2. Click **Choose Files** to select one or more files
3. Files upload directly to the backend
4. MD5 checksums are computed server-side automatically
5. Upload progress is shown per file

### API upload

```bash
curl -X POST http://localhost:8000/api/v1/staging/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@SAMPLE_001_R1.fastq.gz"
```

Response:
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

### FTP upload (recommended for large files)

For files larger than 5 GB, use FTP to avoid browser timeout issues.

#### Connect

=== "Linux / macOS"

    ```bash
    # Using lftp (recommended — supports resume)
    lftp -u your_email@example.com ftp://ftp.nfdp.example.sa
    > mput *.fastq.gz
    > quit

    # Using standard ftp
    ftp ftp.nfdp.example.sa
    > put SAMPLE_001_R1.fastq.gz
    ```

=== "Windows"

    ```
    # Using FileZilla
    Host: ftp.nfdp.example.sa
    Username: your_email@example.com
    Password: your SeqDB password
    Port: 21
    ```

#### Tips

- Use `lftp` for resume support on interrupted uploads
- Upload to your user directory — files appear in staging automatically
- Supported formats: `.fastq`, `.fastq.gz`, `.fq`, `.fq.gz`, `.bam`, `.cram`, `.vcf`, `.vcf.gz`

## Managing staged files

### List staged files

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/staging/files
```

### Delete a staged file

```bash
curl -X DELETE http://localhost:8000/api/v1/staging/files/42 \
  -H "Authorization: Bearer $TOKEN"
```

## What happens to staged files

1. **Upload** — File stored in staging bucket (`nfdp-staging`)
2. **Validation** — Bulk submit matches staged files to sample sheet rows
3. **Confirmation** — Matched files are linked to runs and marked as "linked"
4. **Cleanup** — Linked files are moved from staging to the raw bucket (`nfdp-raw`)

!!! info "Files persist across sessions"
    Staged files remain available until used or deleted. You can upload files in one session and submit the sample sheet later.

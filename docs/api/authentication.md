# Authentication

The SeqDB API uses JWT (JSON Web Token) Bearer authentication. Read-only endpoints are public; write operations require a token.

## Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@university.edu",
    "password": "secure-password-123",
    "full_name": "Ahmed Ali",
    "role": "researcher"
  }'
```

**Response (201):**
```json
{
  "id": 1,
  "email": "researcher@university.edu",
  "full_name": "Ahmed Ali",
  "role": "researcher"
}
```

## Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "researcher@university.edu", "password": "secure-password-123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

## Using the token

Include the `access_token` in the `Authorization` header:

```bash
curl -H "Authorization: Bearer eyJhbG..." \
  http://localhost:8000/api/v1/projects/
```

## Token expiration

Tokens expire after 1 hour (3600 seconds). When a token expires, login again to get a new one.

## Scripting

=== "Bash"

    ```bash
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email": "user@example.com", "password": "pass123"}' \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    # Use in subsequent requests
    curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/staging/files
    ```

=== "Python"

    ```python
    import requests

    BASE = "http://localhost:8000/api/v1"

    # Login
    resp = requests.post(f"{BASE}/auth/login", json={
        "email": "user@example.com",
        "password": "pass123"
    })
    token = resp.json()["access_token"]

    # Use in subsequent requests
    headers = {"Authorization": f"Bearer {token}"}
    projects = requests.get(f"{BASE}/projects/", headers=headers).json()
    ```

## Public endpoints

These endpoints work without authentication:

- `GET /projects/`, `GET /projects/{accession}`
- `GET /samples/`, `GET /samples/{accession}`
- `GET /experiments/`, `GET /experiments/{accession}`
- `GET /runs/`, `GET /runs/{accession}`, `GET /runs/{accession}/download`
- `GET /filereport`
- `GET /search/`
- `GET /checklists/`
- `GET /bulk-submit/template/{checklist_id}`
- `GET /health`

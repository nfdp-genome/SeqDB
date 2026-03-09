# Cloud Deployment Guide — SeqDB Genomic Deposition System

## Architecture: Hybrid On-Prem + Cloud

```
┌─────────────────────────────────────────────────────────────┐
│  Cloud (AWS/Azure/GCP)                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Frontend  │ │ Backend  │ │ Workers  │ │ Managed Redis │  │
│  │ (Vercel/  │ │ (ECS/    │ │ (ECS/    │ │ (ElastiCache/ │  │
│  │  CDN)     │ │  AKS/    │ │  AKS/    │ │  MemoryStore) │  │
│  │           │ │  Cloud   │ │  Cloud   │ │               │  │
│  │           │ │  Run)    │ │  Run)    │ │               │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
│                      │                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Managed PostgreSQL (RDS / Cloud SQL / Azure DB)     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                    VPN / Private Link
                           │
┌─────────────────────────────────────────────────────────────┐
│  On-Premises (Sequencing Facility)                           │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │ MinIO / NAS      │  │ Nextflow Pipeline Executors     │  │
│  │ (50-200 TB/year) │  │ (QC, assembly, variant calling) │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## What Changes for Cloud

### 1. Environment Variables

| Variable | Local Dev | Cloud Production |
|----------|-----------|-----------------|
| `DATABASE_URL` | `postgresql+asyncpg://nfdp:nfdp@localhost:5432/nfdp` | `postgresql+asyncpg://<user>:<password>@<rds-endpoint>:5432/nfdp?ssl=require` |
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://<elasticache-endpoint>:6379/0` (or with TLS: `rediss://...`) |
| `MINIO_ENDPOINT` | `localhost:9002` | `<on-prem-minio>:9000` or `s3.amazonaws.com` |
| `MINIO_ACCESS_KEY` | `minioadmin` | IAM role / service account (not hardcoded) |
| `MINIO_SECRET_KEY` | `minioadmin` | From secrets manager (AWS SSM, Azure Key Vault, GCP Secret Manager) |
| `MINIO_SECURE` | `false` | `true` (always TLS in production) |
| `JWT_SECRET_KEY` | `test-secret-key` | 256-bit random key from secrets manager |
| `APP_ENV` | `development` | `production` |
| `APP_DEBUG` | `true` | `false` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | `https://api.genomics.nfdp.sa/api/v1` |

### 2. Database (PostgreSQL)

**Local:** Single container, no backups, no SSL.

**Cloud changes:**
- Use managed service: **AWS RDS**, **Azure Database for PostgreSQL**, or **Google Cloud SQL**
- Enable **SSL/TLS** (`?ssl=require` in connection string)
- Enable **automated backups** with 30-day retention
- Set up **read replicas** for search-heavy queries
- Configure **connection pooling** via PgBouncer or RDS Proxy
- Use **private subnet** — no public internet access
- Minimum **db.r6g.large** (2 vCPU, 16 GB) for production loads

```python
# backend/app/config.py — add connection pool settings for production
class Settings(BaseSettings):
    database_pool_size: int = 20        # local: 5
    database_max_overflow: int = 10     # local: 0
    database_pool_timeout: int = 30
```

### 3. Object Storage (MinIO → S3/On-Prem Hybrid)

**Local:** MinIO container, local disk.

**Cloud changes:**
- **Option A (Hybrid):** Keep MinIO on-prem for bulk data, sync metadata to cloud
- **Option B (Full cloud):** Replace MinIO with **AWS S3**, **Azure Blob**, or **GCS**
- **Option C (Recommended):** MinIO on-prem with S3-compatible API gateway in cloud

```python
# backend/app/services/storage.py — changes needed
# 1. Replace hardcoded MinIO client with S3-compatible client
# 2. Add storage tier routing:
#    - Hot tier (cloud): metadata, QC reports, small files
#    - Cold tier (on-prem): raw FASTQ, BAM files (50-200 TB/year)

# If using AWS S3 directly:
MINIO_ENDPOINT = "s3.amazonaws.com"
MINIO_SECURE = True
# Use IAM roles instead of access keys (no credentials in env)
```

**Key decisions:**
- Presigned URLs: Will point to on-prem MinIO or cloud S3 depending on file location
- The `build_object_path()` function stays the same — path structure is storage-agnostic
- Add lifecycle policies: move raw data to Glacier/Archive after 90 days
- Enable **bucket versioning** and **object locking** for FAIR compliance

### 4. Secrets Management

**Local:** Plaintext in `.env` file.

**Cloud changes:**
- **NEVER** commit secrets to git or store in plain env vars
- Use cloud-native secrets managers:
  - **AWS:** Systems Manager Parameter Store or Secrets Manager
  - **Azure:** Key Vault
  - **GCP:** Secret Manager
- Inject secrets at runtime via:
  - Container sidecar (ECS/EKS secrets injection)
  - Kubernetes External Secrets Operator
  - Cloud Run secrets mounting

```yaml
# Example: ECS Task Definition (AWS)
secrets:
  - name: DATABASE_URL
    valueFrom: arn:aws:ssm:me-south-1:123456:parameter/nfdp/prod/database-url
  - name: JWT_SECRET_KEY
    valueFrom: arn:aws:secretsmanager:me-south-1:123456:secret:nfdp/jwt-secret
```

### 5. Authentication & Security

**Local:** JWT with hardcoded secret, no CORS restrictions, no rate limiting.

**Cloud changes:**
- Generate strong JWT secret: `openssl rand -hex 32`
- Add **CORS** middleware with allowed origins:
  ```python
  # backend/app/main.py
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://genomics.nfdp.sa"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- Add **rate limiting** (e.g., slowapi or API Gateway throttling)
- Add **HTTPS only** — terminate TLS at load balancer
- Add **LIMS webhook IP allowlisting** and enforce HMAC signature validation
- Consider **OAuth2/OIDC** integration for SSO (Keycloak, Azure AD)

### 6. Frontend Deployment

**Local:** `npm run dev` on port 3000.

**Cloud changes:**
- **Option A:** Deploy to **Vercel** (zero-config Next.js hosting)
- **Option B:** Build static export + deploy to **CDN** (CloudFront, Azure CDN)
- **Option C:** Container deployment (same as backend)

```bash
# Production build
cd frontend
npm run build
# Output in .next/ — deploy to Vercel or containerize
```

- Set `NEXT_PUBLIC_API_URL` to production API endpoint
- Enable **CDN caching** for static assets
- Add **Content Security Policy** headers

### 7. Backend Deployment

**Local:** `uvicorn` with `--reload`.

**Cloud changes:**
- Remove `--reload` flag
- Add **Gunicorn** as process manager:
  ```bash
  gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- Add **health check** endpoint (already exists at `/api/v1/health`)
- Configure **auto-scaling** based on CPU/request count
- Use **container orchestration**: ECS Fargate, AKS, Cloud Run, or Kubernetes

```dockerfile
# Production Dockerfile changes
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install ".[prod]"  # no dev dependencies
COPY . .
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 8. Worker Deployment

**Local:** `arq app.workers.main.WorkerSettings`.

**Cloud changes:**
- Deploy as separate container/service
- Scale independently from API (QC jobs are CPU-intensive)
- For Nextflow pipelines: trigger via **AWS Batch**, **Azure Batch**, or on-prem HPC
- Consider **autoscaling** workers based on Redis queue depth

### 9. Networking

**Local:** All services on `localhost`.

**Cloud changes:**
- Place backend + workers + database in **private subnet**
- Frontend and API Gateway in **public subnet**
- Use **API Gateway** or **Load Balancer** (ALB, Azure Application Gateway)
- **VPN/Private Link** between cloud and on-prem for:
  - MinIO access (presigned URL generation)
  - Pipeline triggering
  - Data sync

```
Internet → CDN → Frontend (public)
Internet → ALB → Backend API (private subnet)
Backend  → RDS (private subnet)
Backend  → ElastiCache (private subnet)
Backend  → VPN → On-prem MinIO + Nextflow
```

### 10. Monitoring & Logging

**Local:** Console logs.

**Cloud changes:**
- **Structured logging** (JSON format):
  ```python
  import structlog
  logger = structlog.get_logger()
  ```
- Ship logs to: CloudWatch, Azure Monitor, or ELK/Loki
- **Metrics:** Prometheus + Grafana or cloud-native (CloudWatch Metrics)
- **Alerting:** on error rates, latency, queue depth, disk usage
- **APM:** Datadog, New Relic, or OpenTelemetry

### 11. CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd backend && pip install -e ".[dev]" && pytest tests/ -v

  deploy-backend:
    needs: test
    steps:
      - run: docker build -t nfdp-backend ./backend
      - run: docker push $REGISTRY/nfdp-backend:${{ github.sha }}
      - run: aws ecs update-service --force-new-deployment  # or equivalent

  deploy-frontend:
    needs: test
    steps:
      - run: cd frontend && npm ci && npm run build
      - run: vercel deploy --prod  # or push to S3 + invalidate CDN
```

### 12. Data Compliance & Backup

- **Database backups:** Daily automated + manual before migrations
- **Object storage:** Bucket versioning + cross-region replication
- **FAIR compliance:** All data gets persistent identifiers (SeqDB accessions)
- **Data retention:** Define policies per Saudi data governance requirements
- **Audit log:** Log all data modifications (who, what, when)
- **ENA submission:** Automated weekly batch for validated submissions

### 13. Cost Estimation (AWS me-south-1, Bahrain)

| Service | Spec | Est. Monthly |
|---------|------|-------------|
| RDS PostgreSQL | db.r6g.large, 100GB | ~$250 |
| ElastiCache Redis | cache.t3.medium | ~$50 |
| ECS Fargate (backend) | 2 vCPU, 4GB × 2 tasks | ~$150 |
| ECS Fargate (workers) | 4 vCPU, 8GB × 2 tasks | ~$300 |
| ALB | Standard | ~$25 |
| VPN to on-prem | Site-to-Site | ~$40 |
| CloudWatch | Logs + Metrics | ~$30 |
| **Total cloud** | | **~$845/month** |
| On-prem MinIO | 200TB NAS | Capital cost |

### Quick Migration Checklist

- [ ] Set up managed PostgreSQL with SSL
- [ ] Set up managed Redis with encryption
- [ ] Configure secrets manager with all production values
- [ ] Set up VPN between cloud and on-prem
- [ ] Build production Docker images (no dev deps, no --reload)
- [ ] Configure load balancer with HTTPS
- [ ] Set CORS to production domain only
- [ ] Deploy backend + workers to container service
- [ ] Deploy frontend to Vercel or CDN
- [ ] Run `alembic upgrade head` against production DB
- [ ] Configure monitoring and alerting
- [ ] Set up CI/CD pipeline
- [ ] Test full workflow end-to-end against production
- [ ] Configure ENA submission credentials
- [ ] Set up backup schedules

# Praxis Deployment Configuration

## Overview

| Field              | Value                                                                    |
| ------------------ | ------------------------------------------------------------------------ |
| **Project**        | Praxis CO Platform                                                       |
| **Type**           | API service (Python, Nexus)                                              |
| **Cloud Provider** | Google Cloud Platform                                                    |
| **GCP Project**    | `terrene-care`                                                           |
| **GCP Account**    | `jack@terrene.foundation`                                                |
| **Region**         | `asia-southeast1` (Singapore)                                            |
| **Service**        | Cloud Run (managed)                                                      |
| **Database**       | SQLite (embedded, `/tmp/praxis.db`)                                      |
| **Registry**       | Artifact Registry (`asia-southeast1-docker.pkg.dev/terrene-care/praxis`) |
| **Service URL**    | `https://praxis.terrene.foundation` (custom domain)                      |
| **Cloud Run URL**  | `https://praxis-api-129371016531.asia-southeast1.run.app` (direct)       |

## Cost Profile

| Component          | Service               | Monthly Cost                          |
| ------------------ | --------------------- | ------------------------------------- |
| Backend API        | Cloud Run (free tier) | $0 — 2M req/month, 360K vCPU-sec free |
| Container Registry | Artifact Registry     | $0 — 0.5 GB free                      |
| Builds             | Cloud Build           | $0 — 120 build-min/day free           |
| Database           | SQLite embedded       | $0                                    |
| SSL/Domain         | Cloud Run auto-HTTPS  | $0                                    |
| **Total**          |                       | **$0/month** (within free tier)       |

### Cost Risks

- Cloud Build exceeding 120 min/day: ~$0.003/build-minute after free tier
- Cloud Run exceeding free tier: ~$0.00002400/vCPU-second, $0.00000250/GiB-second
- Artifact Registry exceeding 0.5 GB: $0.10/GB/month
- **Mitigation**: Single container (~200MB), min-instances=0, max-instances=2

## Architecture

```
                        praxis.terrene.foundation
                              ↓ CNAME
Internet → Cloud Run (auto-HTTPS) → praxis-web (nginx, React SPA)
                                          ↓ fetch()
                        api.praxis.terrene.foundation
                              ↓ CNAME
           Cloud Run (auto-HTTPS) → praxis-api (Python/Nexus)
                                          ↓
                                    SQLite (/tmp/praxis.db)
                                    Ed25519 Keys (/tmp/keys)
```

### Services

| Service | Image | Domain | Purpose |
|---------|-------|--------|---------|
| praxis-web | `praxis/praxis-web:v0.1.0` | `praxis.terrene.foundation` | React web dashboard (nginx) |
| praxis-api | `praxis/praxis-api:v0.1.1` | `api.praxis.terrene.foundation` | Backend API (Python/Nexus) |

### DNS Records (GoDaddy)

| Type | Name | Value |
|------|------|-------|
| CNAME | `praxis` | `ghs.googlehosted.com` |
| CNAME | `api.praxis` | `ghs.googlehosted.com` |

### Limitations of Current Setup

- **SQLite on /tmp**: Data is ephemeral — lost when the container scales to zero (after ~15 min idle). This is acceptable for a pilot. For production, use Cloud SQL PostgreSQL or a persistent volume.
- **min-instances=0**: Cold starts take ~5-10 seconds. Set min-instances=1 ($~7/month) if latency matters.
- **No custom domain**: Uses `*.run.app` URL. Custom domain can be mapped via Cloud Run domain mapping.

## Deployment Runbook

### Prerequisites

```bash
# Authenticate
gcloud auth login jack@terrene.foundation
gcloud config set project terrene-care
gcloud config set run/region asia-southeast1

# Verify
gcloud auth list
gcloud config get-value project
```

### Build

```bash
cd /Users/esperie/repos/terrene/praxis

# Build and push container image
gcloud builds submit \
  --tag asia-southeast1-docker.pkg.dev/terrene-care/praxis/praxis-api:vX.Y.Z \
  --project=terrene-care \
  --region=asia-southeast1 \
  --timeout=600s
```

### Deploy

```bash
# Deploy new revision (first time)
gcloud run deploy praxis-api \
  --image=asia-southeast1-docker.pkg.dev/terrene-care/praxis/praxis-api:vX.Y.Z \
  --project=terrene-care \
  --region=asia-southeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2 \
  --timeout=300s \
  --concurrency=80 \
  --set-env-vars="PRAXIS_DEV_MODE=true,DATABASE_URL=sqlite:////tmp/praxis.db,PRAXIS_KEY_DIR=/tmp/keys,PRAXIS_API_SECRET=$(openssl rand -base64 32),PRAXIS_CORS_ORIGINS=*,LOG_LEVEL=INFO,LOG_FORMAT=json,PRAXIS_ADMIN_USER=admin,PRAXIS_ADMIN_PASSWORD=<SET_SECURE_PASSWORD>"

# Update existing service (subsequent deploys)
gcloud run services update praxis-api \
  --image=asia-southeast1-docker.pkg.dev/terrene-care/praxis/praxis-api:vX.Y.Z \
  --project=terrene-care \
  --region=asia-southeast1
```

### Verify

```bash
PRAXIS_URL="https://praxis-api-129371016531.asia-southeast1.run.app"

# List sessions (should return empty or existing sessions)
curl -s "$PRAXIS_URL/workflows/list_sessions/execute" \
  -X POST -H 'Content-Type: application/json' -d '{}' | python3 -m json.tool | head -5

# Create session
curl -s "$PRAXIS_URL/workflows/create_session/execute" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"inputs":{"workspace_id":"test","domain":"coc"}}' | python3 -m json.tool | head -10

# Auth login
curl -s "$PRAXIS_URL/auth/login" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<password>"}' | python3 -m json.tool | head -5
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service=praxis-api \
  --project=terrene-care --region=asia-southeast1

# Route traffic to previous revision
gcloud run services update-traffic praxis-api \
  --to-revisions=<previous-revision>=100 \
  --project=terrene-care --region=asia-southeast1
```

## Environment Variables

| Variable                | Production Value                      | Description                          |
| ----------------------- | ------------------------------------- | ------------------------------------ |
| `PRAXIS_DEV_MODE`       | `true` (pilot) / `false` (prod)       | Enables dev shortcuts                |
| `DATABASE_URL`          | `sqlite:////tmp/praxis.db`            | Database connection                  |
| `PRAXIS_KEY_DIR`        | `/tmp/keys`                           | Ed25519 key storage                  |
| `PRAXIS_API_SECRET`     | Random 32-byte base64                 | JWT signing secret                   |
| `PRAXIS_CORS_ORIGINS`   | `*` (pilot) / specific origins (prod) | CORS allowed origins                 |
| `PRAXIS_ADMIN_USER`     | `admin`                               | Login username                       |
| `PRAXIS_ADMIN_PASSWORD` | Set securely                          | Login password                       |
| `LOG_LEVEL`             | `INFO`                                | Log verbosity                        |
| `LOG_FORMAT`            | `json`                                | Structured logging for Cloud Logging |

## Nexus API Endpoints

All Nexus handlers are available at `POST /workflows/{handler_name}/execute` with `{"inputs": {...}}` body.

| Handler              | Description                          |
| -------------------- | ------------------------------------ |
| `create_session`     | Create a CO session                  |
| `list_sessions`      | List all sessions                    |
| `get_session`        | Get session by ID                    |
| `pause_session`      | Pause active session                 |
| `resume_session`     | Resume paused session                |
| `end_session`        | Archive session                      |
| `decide`             | Record a decision                    |
| `observe`            | Record an observation                |
| `timeline`           | Get deliberation timeline            |
| `get_constraints`    | Get constraint envelope              |
| `update_constraints` | Update constraints (tightening only) |
| `trust_check`        | Evaluate action against constraints  |
| `trust_record`       | Record audit entry                   |
| `trust_status`       | Get session trust status             |
| `export_bundle`      | Export verification bundle           |

Auth endpoint: `POST /auth/login` (not a Nexus workflow — direct Starlette route)

## Production Upgrade Path

When ready for production:

1. **Database**: Switch from SQLite to Cloud SQL PostgreSQL (~$7/month minimum)
   - Change `DATABASE_URL` to `postgresql://...`
   - DataFlow handles the switch automatically
2. **Persistence**: Use Cloud Run volume mount or Cloud SQL for persistent data
3. **Custom domain**: Map via `gcloud run domain-mappings create`
4. **min-instances**: Set to 1 to eliminate cold starts (~$7/month)
5. **Secrets**: Move `PRAXIS_API_SECRET` and `PRAXIS_ADMIN_PASSWORD` to Secret Manager
6. **CORS**: Restrict to specific frontend domains
7. **Monitoring**: Enable Cloud Monitoring alerts for error rate and latency

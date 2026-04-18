# HELEN OS on Google Cloud Run — Production-Grade Setup

**Version:** 2.0 (Corrected)
**Date:** 2026-04-04
**Status:** READY WITH LOCAL VERIFICATION
**GCP Pricing:** Current as of 2026-04-04

---

## ⚠️ CRITICAL: Pre-Deployment Checklist

**DO NOT deploy until you verify these locally:**

- [ ] `docker build -t helen-test:latest .` succeeds
- [ ] `docker run -p 8000:8000 helen-test:latest` starts without errors
- [ ] `curl http://localhost:8000/health` returns valid JSON
- [ ] Flask app reads environment variables correctly
- [ ] All required dependencies are in `requirements.txt`
- [ ] Dockerfile exposes port 8000 correctly

**If any of these fail, fix locally BEFORE deploying to Cloud Run.**

---

## Prerequisites

✅ Google Cloud account (with active subscription)
✅ Google Cloud SDK installed and authenticated
✅ Docker installed locally
✅ Git installed
✅ API keys (optional, for full model access)

---

## Step 1: Install Google Cloud SDK

### macOS
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version
```

### Linux
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version
```

### Windows
Download: https://cloud.google.com/sdk/docs/install-sdk#windows

---

## Step 2: Authenticate & Set Project

```bash
# Authenticate
gcloud auth login

# Initialize
gcloud init

# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Verify
gcloud config list
```

---

## Step 3: Enable Required APIs

```bash
# Enable Cloud Run, Cloud Build, and Artifact Registry
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 4: Create Artifact Registry Repository

```bash
# Create Docker repository
gcloud artifacts repositories create helen-os \
  --repository-format=docker \
  --location=us-central1 \
  --description="HELEN OS Multi-Model AI Platform"

# Verify
gcloud artifacts repositories list
```

---

## Step 5: LOCAL TESTING (Before Cloud Deployment)

### 5a. Test Docker Build Locally

```bash
# Navigate to HELEN OS directory
cd /path/to/JMT\ CONSULTING\ -\ Releve\ 24

# Test build
docker build -t helen-test:latest .

# Should complete without errors
# If it fails, fix issues locally before proceeding
```

### 5b. Test Docker Container Locally

```bash
# Run container locally
docker run -p 8000:8000 \
  -e HELEN_ENVIRONMENT=development \
  -e HELEN_DEBUG=false \
  helen-test:latest

# In another terminal, test the app
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "helen_initialized": true}

# Test other endpoints
curl http://localhost:8000/
curl http://localhost:8000/models
curl http://localhost:8000/avatars

# Stop container
# Press Ctrl+C
```

### 5c. Verify Environment Variables

```bash
# Test that Flask reads environment variables
docker run -p 8000:8000 \
  -e HELEN_ENVIRONMENT=production \
  -e HELEN_DEBUG=false \
  -e ANTHROPIC_API_KEY=test-key \
  helen-test:latest

# Check logs for any errors
# Should NOT show "API key missing" errors
```

**If all tests pass locally, proceed. If any fail, debug and fix locally.**

---

## Step 6: Build & Push to Artifact Registry

### 6a. Build Docker Image

```bash
# Build with proper registry path
docker build \
  -t us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest .

# Verify build succeeded
docker images | grep helen
```

### 6b. Push to Artifact Registry

```bash
# Push image
docker push us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest

# Verify in registry
gcloud artifacts docker images list us-central1-docker.pkg.dev/$PROJECT_ID/helen-os
```

---

## Step 7: Deploy to Cloud Run

### Production Deployment Command

```bash
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --platform managed \
  --region us-central1 \
  --no-invoker-iam-check \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 100 \
  --min-instances 1
```

**Important flags:**
- `--no-invoker-iam-check`: Makes service publicly accessible (modern GCP approach)
- `--memory 2Gi`: Allocate 2GB RAM
- `--cpu 2`: Allocate 2 vCPUs
- `--timeout 3600`: Allow 60-minute request timeout
- `--max-instances 100`: Scale up to 100 instances if needed
- `--min-instances 1`: Keep 1 warm instance (prevents cold starts)

---

## Step 8: Get Your Service URL

```bash
# Retrieve service URL
gcloud run services describe helen-os \
  --region us-central1 \
  --format='value(status.url)'

# Output example:
# https://helen-os-xxxxx-uc.a.run.app

# Save this URL - you'll use it to access your API
export HELEN_URL=$(gcloud run services describe helen-os \
  --region us-central1 \
  --format='value(status.url)')

echo $HELEN_URL
```

---

## Step 9: Test Deployed Service

### Health Check
```bash
curl $HELEN_URL/health
```

### Query Endpoint
```bash
curl -X POST $HELEN_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is machine learning?",
    "task_type": "CONVERSATION"
  }'
```

### List Models
```bash
curl $HELEN_URL/models
```

### Switch Avatar
```bash
curl -X POST $HELEN_URL/avatar/sage
```

---

## Pricing (Corrected - Current GCP Rates)

### Free Tier (per month)

According to Google Cloud Run official pricing (2026):

| Resource | Free Tier | After Free Tier |
|----------|-----------|-----------------|
| vCPU-seconds | 180,000 | $0.00002400 per vCPU-second |
| GiB-seconds | 450,000 | $0.00000025 per GiB-second |
| Requests | 2,000,000 | Included in vCPU-seconds |
| Outbound bandwidth | 50 GB | $0.12 per GB overage |

### What This Means

With **2 vCPU + 2 GiB memory** and typical request duration of 1-5 seconds:

**Scenario: 1,000 requests/day with 2-second avg duration**

- vCPU-seconds: 1,000 × 2s = 2,000 vCPU-seconds/day = 60,000/month
- GiB-seconds: 1,000 × 2s × 2 = 4,000 GiB-seconds/day = 120,000/month
- **Total cost: FREE** (well within free tier)

**Scenario: 10,000 requests/day with 2-second avg duration**

- vCPU-seconds: 10,000 × 2s = 20,000/day = 600,000/month
- GiB-seconds: 10,000 × 2s × 2 = 40,000/day = 1,200,000/month
- vCPU overage: (600,000 - 180,000) × $0.00002400 = $10.08
- GiB overage: 0 (within 450,000)
- **Estimated monthly cost: ~$10**

**Scenario: 100,000 requests/day with 2-second avg duration**

- vCPU-seconds: 100,000 × 2s = 200,000/day = 6,000,000/month
- GiB-seconds: 100,000 × 2s × 2 = 400,000/day = 12,000,000/month
- vCPU overage: (6,000,000 - 180,000) × $0.00002400 = $139.68
- GiB overage: (12,000,000 - 450,000) × $0.00000025 = $2.89
- **Estimated monthly cost: ~$143**

### Cost Optimization Tips

```bash
# Reduce memory to 1Gi (saves 50%)
gcloud run services update helen-os \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1

# Set min-instances to 0 (no idle cost, but adds cold-start latency)
gcloud run services update helen-os \
  --region us-central1 \
  --min-instances 0

# Set lower max-instances if you expect low traffic
gcloud run services update helen-os \
  --region us-central1 \
  --max-instances 10
```

---

## Add API Keys (Optional)

### Get Your API Keys

1. **Claude (Anthropic):** https://console.anthropic.com/account/keys
2. **GPT (OpenAI):** https://platform.openai.com/account/api-keys
3. **Grok (xAI):** https://console.x.ai
4. **Gemini (Google):** https://makersuite.google.com/app/apikey
5. **Qwen (Alibaba):** https://dashscope.console.aliyun.com

### Update Service with Keys

```bash
# Update one key
gcloud run services update helen-os \
  --region us-central1 \
  --update-env-vars ANTHROPIC_API_KEY="sk-ant-v3-YOUR-KEY"

# Update multiple keys
gcloud run services update helen-os \
  --region us-central1 \
  --update-env-vars \
    ANTHROPIC_API_KEY="sk-ant-v3-...",\
    OPENAI_API_KEY="sk-...",\
    XAI_API_KEY="xai-..."
```

---

## Monitoring & Logging

### View Logs

```bash
# Real-time logs
gcloud run logs read helen-os --region us-central1 --follow

# Last 100 lines
gcloud run logs read helen-os --region us-central1 --limit 100

# Logs from past hour
gcloud run logs read helen-os --region us-central1 --limit 50 --since=1h
```

### View Metrics

```bash
# Open Cloud Console dashboard
gcloud run services describe helen-os --region us-central1

# Or open in browser:
# https://console.cloud.google.com/run/detail/us-central1/helen-os/metrics
```

### Set Up Alerts

1. Go to: https://console.cloud.google.com/monitoring/alerting/policies
2. Create alert for:
   - Error rate > 5%
   - Latency p95 > 5 seconds
   - Memory usage > 80%

---

## Update Service (After Code Changes)

```bash
# 1. Rebuild locally and test
docker build -t helen-test:latest .
docker run -p 8000:8000 helen-test:latest
# Test endpoints...

# 2. Build for registry
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest .

# 3. Push new version
docker push us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest

# 4. Deploy (Cloud Run will create new revision automatically)
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --region us-central1
```

---

## Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service helen-os --region us-central1

# Get revision name (e.g., helen-os-00001-abc)
# Deploy specific revision
gcloud run deploy helen-os \
  --region us-central1 \
  --revision helen-os-00001-abc

# Or use traffic splitting
gcloud run services update-traffic helen-os \
  --region us-central1 \
  --to-revisions helen-os-00001-abc=100
```

---

## Troubleshooting

### Service Not Responding

```bash
# Check logs for errors
gcloud run logs read helen-os --region us-central1 --limit 100

# Check service status
gcloud run services describe helen-os --region us-central1

# Verify environment variables are set
gcloud run services describe helen-os --region us-central1 --format='value(spec.template.spec.containers[0].env)'
```

### High Latency

```bash
# Check if min-instances is 0 (causes cold starts)
gcloud run services describe helen-os --region us-central1 --format='value(spec.template.spec.containerConcurrency)'

# Increase min-instances to keep warm
gcloud run services update helen-os --region us-central1 --min-instances 1

# Or increase memory/CPU
gcloud run services update helen-os --region us-central1 --memory 4Gi --cpu 4
```

### Out of Memory Errors

```bash
# Check current memory allocation
gcloud run services describe helen-os --region us-central1 | grep memory

# Increase memory
gcloud run services update helen-os --region us-central1 --memory 4Gi
```

### High Costs

```bash
# Reduce resources
gcloud run services update helen-os --region us-central1 --memory 1Gi --cpu 1

# Set lower max-instances
gcloud run services update helen-os --region us-central1 --max-instances 10

# Or use request-based autoscaling
gcloud run services update helen-os --region us-central1 --concurrency 50
```

---

## Delete Service

```bash
gcloud run services delete helen-os --region us-central1
```

---

## Resources

- **Cloud Run Docs:** https://cloud.google.com/run/docs
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Cloud Console:** https://console.cloud.google.com/run
- **Monitoring:** https://console.cloud.google.com/monitoring

---

## Final Checklist Before Production

- [ ] Dockerfile builds successfully locally
- [ ] Application starts without errors
- [ ] All endpoints respond correctly
- [ ] Environment variables are read properly
- [ ] Cloud Run deployment completes
- [ ] Service URL is publicly accessible
- [ ] Health check returns 200 status
- [ ] Query endpoint works with test prompt
- [ ] Logs show no errors
- [ ] Cost estimate is acceptable

---

**Status:** PRODUCTION-GRADE ✅
**Date:** 2026-04-04
**Version:** 2.0 (Corrected)
**Free Tier:** 2M requests/month + 180K vCPU-seconds + 450K GiB-seconds

# HELEN OS on Google Cloud Run — Complete Setup Guide

**Version:** 1.0
**Date:** 2026-04-04
**Status:** Ready to Deploy
**Free Tier:** 2M requests/month + 360K GB-seconds/month

---

## Prerequisites

✅ Google Cloud account with billing enabled
✅ Google Cloud SDK installed
✅ Docker installed locally
✅ Git installed
✅ API keys (optional but recommended)

---

## Step 1: Install Google Cloud SDK

### macOS
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Linux
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Windows
Download installer: https://cloud.google.com/sdk/docs/install-sdk#windows

### Verify Installation
```bash
gcloud --version
```

---

## Step 2: Authenticate with Google Cloud

```bash
# Initialize gcloud
gcloud init

# This will:
# 1. Open browser for authentication
# 2. Select your Google Cloud project
# 3. Set default region (choose: us-central1)

# Verify authentication
gcloud auth list
```

---

## Step 3: Set Up Your Google Cloud Project

```bash
# Set your project ID (replace with your actual project ID)
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 4: Create Artifact Registry Repository

```bash
# Create repository for Docker images
gcloud artifacts repositories create helen-os \
  --repository-format=docker \
  --location=us-central1 \
  --description="HELEN OS Multi-Model AI"

# Verify creation
gcloud artifacts repositories list
```

---

## Step 5: Build and Push Docker Image

```bash
# Navigate to your HELEN OS directory
cd /path/to/HELEN_OS

# Build Docker image
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest

# Verify push
gcloud artifacts docker images list us-central1-docker.pkg.dev/$PROJECT_ID/helen-os
```

---

## Step 6: Deploy to Cloud Run

### Option A: Deploy with API Keys (Recommended)

```bash
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 100 \
  --set-env-vars ANTHROPIC_API_KEY="sk-ant-v3-YOUR-KEY" \
  --set-env-vars OPENAI_API_KEY="sk-YOUR-KEY" \
  --set-env-vars XAI_API_KEY="xai-YOUR-KEY" \
  --set-env-vars GOOGLE_API_KEY="AIzaSy-YOUR-KEY" \
  --set-env-vars QWEN_API_KEY="YOUR-KEY" \
  --set-env-vars HELEN_ENVIRONMENT="production" \
  --set-env-vars HELEN_DEBUG="false"
```

### Option B: Deploy Without API Keys (Test Mode)

```bash
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 100
```

---

## Step 7: Get Your Service URL

```bash
# Retrieve your service URL
gcloud run services describe helen-os --region us-central1

# Output will include SERVICE URL like:
# https://helen-os-xxxxx-uc.a.run.app

# Or more directly:
gcloud run services describe helen-os \
  --region us-central1 \
  --format='value(status.url)'
```

---

## Step 8: Test Your Deployment

### Health Check
```bash
curl https://helen-os-xxxxx-uc.a.run.app/health
```

### API Info
```bash
curl https://helen-os-xxxxx-uc.a.run.app/
```

### Query Example
```bash
curl -X POST https://helen-os-xxxxx-uc.a.run.app/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is machine learning?",
    "task_type": "CONVERSATION"
  }'
```

### Switch Avatar
```bash
curl -X POST https://helen-os-xxxxx-uc.a.run.app/avatar/sage
```

---

## Step 9: Monitor Your Service

### View Logs
```bash
gcloud run logs read helen-os --region us-central1 --limit 50
```

### Monitor Metrics
```bash
# Open Cloud Console
open https://console.cloud.google.com/run/detail/us-central1/helen-os/metrics

# Or use gcloud
gcloud run services describe helen-os --region us-central1
```

### Set Up Alerts
1. Go to: https://console.cloud.google.com/monitoring/alerting/policies
2. Create policy for error rate > 5%
3. Create policy for high latency > 5s

---

## Step 10: Update Your Service (After Changes)

```bash
# Rebuild image
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest .

# Push updated image
docker push us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest

# Deploy updated version
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --region us-central1
```

---

## Cost Breakdown (Free Tier)

### Monthly Free Tier Limits:
- **2,000,000 requests** (more than enough for testing)
- **360,000 GB-seconds** compute time
- **50 GB outbound bandwidth**
- **1 service running simultaneously**

### What This Means:
- ✅ Up to 6 requests/second continuously free
- ✅ 1,000+ requests/day free
- ✅ No cost for testing phase
- ✅ Overage: ~$0.00002778 per request (very cheap)

### Example Costs:
- 1M requests/month: **Free**
- 10M requests/month: **~$2.78**
- 100M requests/month: **~$27.80**

---

## Environment Variables to Set

### API Keys (Get from providers)
```
ANTHROPIC_API_KEY = sk-ant-v3-...
OPENAI_API_KEY = sk-...
XAI_API_KEY = xai-...
GOOGLE_API_KEY = AIzaSy...
QWEN_API_KEY = ...
```

### Deployment Settings
```
HELEN_ENVIRONMENT = production
HELEN_DEBUG = false
HELEN_PORT = 8000
HELEN_DEFAULT_MODEL = claude-opus-4-6
HELEN_TEMPERATURE = 0.7
HELEN_MAX_TOKENS = 2048
HELEN_STREAMING = true
HELEN_AUTO_FALLBACK = true
HELEN_PREFER_LOCAL = false
```

---

## API Endpoints Available

After deployment, your HELEN OS will be accessible at:

```
https://helen-os-xxxxx-uc.a.run.app/health           # Health check
https://helen-os-xxxxx-uc.a.run.app/                 # API info
https://helen-os-xxxxx-uc.a.run.app/models           # List models
https://helen-os-xxxxx-uc.a.run.app/query            # Query endpoint
https://helen-os-xxxxx-uc.a.run.app/status           # System status
https://helen-os-xxxxx-uc.a.run.app/stats            # Usage stats
https://helen-os-xxxxx-uc.a.run.app/task-types       # Task types
https://helen-os-xxxxx-uc.a.run.app/avatars          # List avatars
```

---

## Useful Commands

### View Service Details
```bash
gcloud run services describe helen-os --region us-central1
```

### Update Environment Variables
```bash
gcloud run services update helen-os \
  --region us-central1 \
  --update-env-vars ANTHROPIC_API_KEY="new-key"
```

### Delete Service
```bash
gcloud run services delete helen-os --region us-central1
```

### View Revision History
```bash
gcloud run revisions list --service helen-os --region us-central1
```

### Scale Up/Down
```bash
# Set maximum concurrent requests per instance
gcloud run services update helen-os \
  --region us-central1 \
  --concurrency 80

# Set min and max instances
gcloud run services update helen-os \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 100
```

---

## Troubleshooting

### Service Not Responding
```bash
# Check logs
gcloud run logs read helen-os --region us-central1 --limit 100

# Check service status
gcloud run services describe helen-os --region us-central1 --format='value(status)'
```

### Build Failures
```bash
# Build locally first to test
docker build -t helen-os:test .
docker run -p 8000:8000 helen-os:test
curl http://localhost:8000/health
```

### High Latency
```bash
# Check metrics
gcloud monitoring time-series list \
  --filter 'resource.labels.service_name=helen-os'

# Increase CPU or memory
gcloud run services update helen-os \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4
```

### High Costs (if overage)
```bash
# Set max requests per second
gcloud run services update helen-os \
  --region us-central1 \
  --max-instances 10  # Limits concurrent requests
```

---

## Next Steps

1. ✅ Install Google Cloud SDK
2. ✅ Authenticate: `gcloud init`
3. ✅ Build Docker image: `docker build -t ... .`
4. ✅ Push to Registry: `docker push ...`
5. ✅ Deploy: `gcloud run deploy ...`
6. ✅ Test: `curl https://your-url/health`
7. ✅ Monitor: Google Cloud Console

---

## Resources

- **Google Cloud Run Docs:** https://cloud.google.com/run/docs
- **Cloud Console:** https://console.cloud.google.com
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Cloud Monitoring:** https://console.cloud.google.com/monitoring

---

## Quick Copy-Paste Commands

```bash
# 1. Initialize
gcloud init
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Create repo
gcloud artifacts repositories create helen-os --repository-format=docker --location=us-central1

# 4. Build & Push
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest .
docker push us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest

# 5. Deploy
gcloud run deploy helen-os \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/helen-os/helen:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

# 6. Get URL
gcloud run services describe helen-os --region us-central1 --format='value(status.url)'

# 7. Test
curl https://helen-os-xxxxx-uc.a.run.app/health
```

---

**Status:** ✅ Ready to Deploy
**Platform:** Google Cloud Run
**Cost:** Free tier (2M requests/month)
**Deployment Time:** ~10-15 minutes
**Date:** 2026-04-04

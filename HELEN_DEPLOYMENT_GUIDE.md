# HELEN OS — Definitive Deployment Guide

**Version:** HELEN OS v1.0 Multi-Model
**Date:** 2026-04-04
**Status:** Production-Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [API Key Configuration](#api-key-configuration)
6. [Model Selection & Routing](#model-selection--routing)
7. [Usage Examples](#usage-examples)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## System Overview

HELEN OS is a unified multi-model AI platform that intelligently routes tasks to six different LLM providers:

### Supported Models

| Provider | Model | Type | Capability | Cost |
|----------|-------|------|-----------|------|
| **Ollama** | Llama 2 | Local | Standard | Free |
| **Ollama** | Mistral | Local | Standard | Free |
| **Claude** | Opus 4.6 | Cloud | Expert | $0.015/1k |
| **Claude** | Sonnet 4.6 | Cloud | Advanced | $0.003/1k |
| **GPT** | GPT-4 Turbo | Cloud | Expert | $0.01/1k |
| **GPT** | GPT-4o | Cloud | Advanced | $0.005/1k |
| **Grok** | Grok-1 | Cloud | Advanced | $0.002/1k |
| **Gemini** | Pro Vision | Cloud | Advanced | $0.0005/1k |
| **Qwen** | Max | Cloud | Advanced | $0.008/1k |

### Architecture Components

```
┌─────────────────────────────────────────────────────┐
│           HELEN OS Unified Interface                │
│  (Web API, CLI, Programmatic Access)                │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│     Intelligent Model Router & Dispatcher           │
│  - Task Type Analysis                               │
│  - Capability Matching                              │
│  - Cost Optimization                                │
│  - Automatic Fallback                               │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼───┐  ┌─────▼──┐  ┌──────▼─────┐
    │ Ollama │  │ Cloud  │  │ Config &   │
    │ (Local)│  │ APIs   │  │ Management │
    └────────┘  └────────┘  └────────────┘
```

---

## Local Deployment

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone or navigate to HELEN OS directory
cd /path/to/HELEN_OS

# 2. Run installation script
bash INSTALL_LOCAL.sh

# 3. Configure API keys
nano ~/.helen_os/.env

# 4. Start HELEN OS
source .venv/bin/activate
python helen_unified_interface_v1.py
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create config directory
mkdir -p ~/.helen_os

# 4. Create .env file with API keys
cat > ~/.helen_os/.env << EOF
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
XAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
QWEN_API_KEY=your_key_here
EOF

# 5. Start HELEN OS
python helen_unified_interface_v1.py
```

### Local Usage

```bash
# Interactive CLI
python helen_unified_interface_v1.py

# Then in HELEN CLI:
[HELEN] > ask What is machine learning?
[HELEN] > ask-coding Write a Python function for binary search
[HELEN] > ask-reasoning Explain quantum entanglement
[HELEN] > models
[HELEN] > status
[HELEN] > quit
```

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

### Quick Start

```bash
# 1. Create .env file with API keys
cp .env.example .env
# Edit .env with your API keys

# 2. Build and start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. Access HELEN OS
docker exec -it helen-os-main python -m helen_unified_interface_v1

# 5. View logs
docker-compose logs -f helen-os

# 6. Stop services
docker-compose down
```

### Docker Services

The docker-compose setup includes:

1. **helen-os** (main service)
   - Port: 8000
   - Configuration: `/root/.helen_os`
   - Environment: Docker

2. **ollama** (local LLM)
   - Port: 11434
   - Models: Llama 2, Mistral
   - Data: Persisted in `ollama-data` volume

3. **redis** (optional, caching)
   - Port: 6379
   - For session management and caching

4. **postgres** (optional, persistence)
   - Port: 5432
   - Database: `helen_os`
   - User: `helen`

### Using Docker

```bash
# Access HELEN CLI inside container
docker exec -it helen-os-main python helen_unified_interface_v1.py

# View configuration
docker exec helen-os-main cat /root/.helen_os/deployment.json

# Pre-download Ollama models
docker exec ollama ollama pull llama2
docker exec ollama ollama pull mistral

# Scale to multiple instances (with load balancer)
docker-compose up -d --scale helen-os=3
```

### Docker Environment Variables

All settings can be configured via `.env` file:

```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
XAI_API_KEY=...
GOOGLE_API_KEY=...
QWEN_API_KEY=...
HELEN_ENVIRONMENT=docker
HELEN_DEBUG=false
HELEN_PORT=8000
HELEN_DEFAULT_MODEL=claude-opus-4-6
HELEN_TEMPERATURE=0.7
HELEN_PREFER_LOCAL=true
POSTGRES_PASSWORD=...
```

---

## Cloud Deployment

### Deployment to AWS (ECS)

```bash
# 1. Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t helen-os:latest .
docker tag helen-os:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/helen-os:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/helen-os:latest

# 2. Create ECS task definition
# 3. Create ECS service with load balancer
# 4. Configure Secrets Manager for API keys
```

### Deployment to Google Cloud Run

```bash
# 1. Build Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/helen-os

# 2. Deploy to Cloud Run
gcloud run deploy helen-os \
  --image gcr.io/PROJECT_ID/helen-os \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=... \
  --memory 2Gi \
  --timeout 3600
```

### Deployment to Heroku

```bash
# 1. Create Heroku app
heroku create helen-os-production

# 2. Set environment variables
heroku config:set ANTHROPIC_API_KEY=...
heroku config:set OPENAI_API_KEY=...

# 3. Deploy
git push heroku main

# 4. View logs
heroku logs --tail
```

---

## API Key Configuration

### Environment Variables

HELEN OS looks for API keys in this order:

1. **Environment Variables** (first priority)
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export OPENAI_API_KEY=sk-...
   ```

2. **.env File** (second priority)
   ```
   ~/.helen_os/.env
   ```

3. **Config File** (third priority)
   ```
   ~/.helen_os/credentials.json
   ```

### Setting API Keys

#### Option 1: Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-v3-...
export OPENAI_API_KEY=sk-...
export XAI_API_KEY=xai-...
export GOOGLE_API_KEY=AIzaSy...
export QWEN_API_KEY=...

# Then start HELEN OS
python helen_unified_interface_v1.py
```

#### Option 2: .env File

```bash
# Create ~/.helen_os/.env
cat > ~/.helen_os/.env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-v3-...
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...
GOOGLE_API_KEY=AIzaSy...
QWEN_API_KEY=...
EOF

# Start HELEN OS (will auto-load .env)
python helen_unified_interface_v1.py
```

#### Option 3: Programmatic Configuration

```python
from helen_config_manager_v1 import get_config_manager

config = get_config_manager()
config.set_api_key("claude", "sk-ant-v3-...")
config.set_api_key("gpt", "sk-...")
```

### API Key Priority

When HELEN needs to use a model:

1. Check environment variable
2. Check .env file
3. Check config database
4. Raise error if not found

### Managing Credentials Securely

**DO:**
- ✅ Use environment variables in production
- ✅ Use .env files for development (add to .gitignore)
- ✅ Rotate keys regularly
- ✅ Use restricted API keys with minimal permissions
- ✅ Monitor API usage

**DON'T:**
- ❌ Hardcode API keys in code
- ❌ Commit API keys to version control
- ❌ Share API keys via email/chat
- ❌ Log API keys
- ❌ Use overly-permissive keys

---

## Model Selection & Routing

### Task Types

HELEN intelligently selects models based on task type:

| Task Type | Best Models | Use Case |
|-----------|-------------|----------|
| **Reasoning** | Claude, GPT, Grok | Logic, analysis, planning |
| **Coding** | Claude, GPT, Grok | Code generation, debugging |
| **Math** | GPT, Claude, Grok | Mathematical problem solving |
| **Analysis** | Claude, GPT, Grok | Data analysis, synthesis |
| **Creative** | Claude, Grok, Qwen | Writing, brainstorming, design |
| **Vision** | Gemini, GPT, Claude | Image understanding |
| **Conversation** | Ollama, Claude, GPT | General chat |
| **Research** | Claude, GPT, Grok | Deep research, synthesis |
| **Factual** | Claude, GPT, Gemini | Fact-based queries |

### Routing Decision Logic

```
Task Input
    ↓
Analyze Task Type
    ↓
Get Preferred Models for Task Type
    ↓
Filter by Capability & Constraints
    ↓
Score Each Model:
  - Task type alignment (40 pts)
  - Capability tier (30 pts)
  - Priority (20 pts)
  - Latency bonus (5 pts)
  - Cost bonus (5 pts)
    ↓
Select Model with Highest Score
    ↓
Fallback to Alternative if Primary Unavailable
    ↓
Execute Query
```

### Programmatic Model Selection

```python
from helen_unified_interface_v1 import HELENMultiModel
from helen_multimodel_dispatcher_v1 import TaskType

helen = HELENMultiModel()

# Query with auto-selection
response = helen.query(
    "Write a Python function",
    task_type=TaskType.CODING,
)

# Check routing decision
decision = helen.get_routing_decision(TaskType.REASONING)
print(f"Selected: {decision.model_config.name}")
print(f"Reason: {decision.reason}")

# Use specific provider
from helen_multimodel_dispatcher_v1 import ModelProvider
response = helen.query(
    "Your prompt",
    task_type=TaskType.CODING,
    preferred_providers=[ModelProvider.CLAUDE],
)
```

---

## Usage Examples

### CLI Interface

```bash
# Start interactive mode
python helen_unified_interface_v1.py

# Examples:
[HELEN] > ask What is the capital of France?
[HELEN] > ask-coding Implement quicksort in Python
[HELEN] > ask-reasoning Explain consciousness
[HELEN] > ask-math Solve: 3x^2 + 2x - 5 = 0
[HELEN] > ask-creative Write a haiku about AI
[HELEN] > models
[HELEN] > routing coding
[HELEN] > stats
[HELEN] > quit
```

### Programmatic API

```python
from helen_unified_interface_v1 import HELENMultiModel
from helen_multimodel_dispatcher_v1 import TaskType

# Initialize
helen = HELENMultiModel()

# Basic query
response = helen.query(
    "Explain machine learning in simple terms",
    task_type=TaskType.EXPLANATION,
)
print(response)

# Streaming response
response = helen.query(
    "Write a Python web scraper",
    task_type=TaskType.CODING,
    stream=True,
)

# Async query
import asyncio

async def main():
    response = await helen.query_async(
        "Analyze this dataset...",
        task_type=TaskType.ANALYSIS,
    )
    return response

result = asyncio.run(main())

# Check available models
models = helen.list_available_models()
for model_id, details in models.items():
    print(f"{model_id}: {details}")

# Get usage stats
stats = helen.get_stats()
print(f"Total requests: {stats['total_requests']}")
for provider_stats in stats['responses']:
    print(f"{provider_stats['provider']}: {provider_stats['cost']}")
```

### With HELEN OS Kernel

```python
from helen_unified_interface_v1 import HELENMultiModel
from helen_multimodel_dispatcher_v1 import TaskType
from helen_os.autonomy.autoresearch_step_v1 import execute_research_task

# Initialize HELEN
helen = HELENMultiModel()

# Create research task
task = {
    "skill_id": "skill.research",
    "query": "Investigate recent advances in quantum computing",
    "task_type": TaskType.RESEARCH,
}

# Execute with HELEN OS governance
result = execute_research_task(task, helen)
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check HELEN status
curl http://localhost:8000/health

# Check Ollama service
curl http://localhost:11434/api/tags

# Check API availability
python -c "from helen_config_manager_v1 import get_config_manager; c = get_config_manager(); print(c.get_status())"
```

### Logs

```bash
# View HELEN logs
tail -f ~/.helen_os/helen.log

# Docker logs
docker-compose logs -f helen-os

# Ollama logs
docker-compose logs -f ollama
```

### Metrics

```python
from helen_unified_interface_v1 import HELENMultiModel

helen = HELENMultiModel()

# Get statistics
stats = helen.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Provider usage: {stats['responses']}")

# Get status
status = helen.get_status()
print(f"Available models: {status['available_models']}")
print(f"Response history: {status['response_history']}")
print(f"Total cost: {status['total_cost']}")
```

### Model Availability

```bash
# Check which models are available
[HELEN] > models

# Check provider status
[HELEN] > config

# Test specific model routing
[HELEN] > routing coding
```

---

## Troubleshooting

### API Key Issues

**Problem:** `ERR_API_KEY_MISSING`

```bash
# Solution: Ensure .env file exists and has API keys
cat ~/.helen_os/.env

# Or set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
```

### Connection Issues

**Problem:** `Connection refused` to Ollama

```bash
# Solution: Start Ollama service
ollama serve

# Or if using Docker:
docker-compose up ollama
```

**Problem:** API rate limiting

```bash
# Solution: Add delay between requests or upgrade plan
# Reduce concurrent requests in config
HELEN_MAX_CONCURRENT_REQUESTS=5
```

### Memory Issues

**Problem:** Out of memory errors

```bash
# Solution: Reduce max_tokens or batch size
# In .env:
HELEN_MAX_TOKENS=1024

# Or in docker-compose.yml:
# resources:
#   limits:
#     memory: 4G
```

### Model Not Found

**Problem:** `Model not available`

```bash
# Solution: Check if provider is configured
[HELEN] > models
[HELEN] > config

# Pre-download Ollama models
ollama pull llama2
ollama pull mistral
```

---

## Best Practices

### Performance

- Use Ollama for simple tasks (faster, free)
- Use Claude for complex reasoning
- Use GPT for code generation
- Cache results when possible
- Use streaming for long responses

### Cost

- Set `HELEN_PREFER_LOCAL=true` to prioritize Ollama
- Monitor usage with `stats` command
- Set cost limits: `HELEN_COST_LIMIT=0.10`
- Use model pooling for batch operations

### Security

- Never commit API keys
- Rotate keys regularly
- Use restricted API keys
- Monitor unusual activity
- Encrypt sensitive data in transit

### Reliability

- Enable auto-fallback: `HELEN_AUTO_FALLBACK=true`
- Monitor API health
- Have redundant models configured
- Log all requests for audit
- Set appropriate timeouts

---

## Support & Resources

- **GitHub:** https://github.com/your-repo/helen-os
- **Documentation:** See HELEN_OS_QUICKSTART.md
- **Technical Reference:** See HELEN_TECHNICAL_REFERENCE.md
- **API Reference:** See helen_api_clients_v1.py
- **Architecture:** See HELEN_OS_ARCHITECTURE_V2.md

---

**HELEN OS v1.0 — Multi-Model Production Deployment**
**Last Updated:** 2026-04-04
**Status:** PRODUCTION READY ✅

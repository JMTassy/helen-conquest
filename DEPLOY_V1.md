# HELEN OS V1 — Persistent Deployment (Single Instance)

This guide deploys one persistent HELEN OS V1 instance using Docker Compose.

## Prerequisites
- Docker 20.10+
- Docker Compose 1.29+

## 1) Configure API Keys
Create or edit `.env` in the repo root:

```
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
XAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
QWEN_API_KEY=your_key
```

If you only want local models, you can omit the cloud keys.

## 2) Start Persistent Deployment
From the repo root:

```
docker-compose up -d
```

This will:
- build the HELEN OS image
- start the API server on port `8000`
- start Ollama on port `11434`
- persist config and runtime data in Docker volumes

## 3) Verify Health
```
curl http://localhost:8000/health
```

Expected response:
```
{"status":"healthy", ...}
```

## 4) Example Query
```
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is HELEN OS?","task_type":"EXPLANATION"}'
```

## 5) Stop / Restart
```
docker-compose down

docker-compose up -d
```

## Persistence
Persistent data is stored in Docker volumes:
- `helen-config` → `/root/.helen_os`
- `ollama-data` → `/root/.ollama`

These volumes survive container restarts.

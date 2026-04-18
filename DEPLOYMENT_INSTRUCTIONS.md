# HELEN DEPLOYMENT INSTRUCTIONS

**Status:** Ready for local deployment (Ollama + Gemma 4 + Avatar)
**Architecture:** CTO_ONBOARDING_ARCHITECTURE_V1 (Layers 0-2 proven, 3-6 ratifiable, 7-12 implementation in progress)

---

## PREREQUISITES

- Docker Desktop installed and running
- 8GB+ RAM available
- 6GB disk space for Ollama models
- Ports available: 8000 (API), 5173 (Avatar), 11434 (Ollama)

---

## QUICK START (3 steps)

### Step 1: Copy Environment Configuration

```bash
cd /Users/jean-marietassy/Documents/GitHub/helen_os_v1
cp .env.example .env
```

Edit `.env` if needed (defaults work for local deployment):
- `HELEN_MODEL=gemma:4b` (4B parameter model, fast, requires ~2GB VRAM)
- `HELEN_SESSION_DIR=/persistent/sessions` (persistent state)
- `OLLAMA_HOST=http://ollama:11434` (docker service name)

### Step 2: Start Deployment

```bash
docker-compose up -d
```

This starts 3 services:
1. **ollama** (port 11434) — Gemma 4 model server
2. **helen_api** (port 8000) — /do_next endpoint + persistent sessions
3. **airi_frontend** (port 5173) — Avatar UI

⏳ **First start:** ~5 minutes (Ollama downloads Gemma 4, ~2GB)

### Step 3: Open Avatar in Browser

```
http://localhost:5173
```

Chat with HELEN avatar. Session state persists across restarts.

---

## VERIFY DEPLOYMENT

### Check all services running

```bash
docker-compose ps
```

Expected output:
```
helen_ollama    Running  11434/tcp
helen_api       Running  8000/tcp, healthcheck OK
helen_airi      Running  5173/tcp
```

### Test API directly

```bash
curl -X POST http://localhost:8000/do_next \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session",
    "user_input": "Hello HELEN",
    "mode": "chat",
    "model": "gemma:4b"
  }'
```

Response format:
```json
{
  "session_id": "test_session",
  "mode": "chat",
  "reply": "Hello! I am HELEN, a constitutionally bounded cognitive OS...",
  "receipt_id": "receipt_xyz...",
  "context_items_used": 2,
  "epoch": 1,
  "continuity": 0.98
}
```

### Check persistent state

Sessions and receipts stored in Docker volume:
```bash
docker exec helen_api ls -la /persistent/
```

---

## OPTIONAL: TELEGRAM INTEGRATION

### Setup Telegram Bot

1. Create bot via BotFather on Telegram
2. Get `TELEGRAM_BOT_TOKEN`
3. Set webhook URL (your public IP + port 8001)

### Start Telegram Bridge

```bash
docker-compose --profile telegram up -d telegram_bridge
```

Bridge runs on port 8001, forwards Telegram messages to HELEN API.

---

## OPTIONAL: LINE INTEGRATION

### Setup LINE Bot

1. Create bot on LINE Developer Console
2. Get `LINE_CHANNEL_TOKEN` and `LINE_CHANNEL_SECRET`
3. Set webhook URL to `http://your-ip:8002/webhook`

### Start LINE Bridge

```bash
docker-compose --profile line up -d line_bridge
```

---

## PERSISTENT STATE

All state persists across container restarts:

- **Sessions:** `/persistent/sessions/` (JSON)
- **Ledger:** `/persistent/ledger.ndjson` (append-only receipts)
- **Memory:** `/persistent/helen.db` (SQLite facts + lessons)

To reset state (WARNING: destructive):
```bash
docker-compose down -v  # -v removes persistent volume
```

---

## COMMON ISSUES

### Ollama fails to start
```
ERROR: ollama health check failed
```
**Fix:** Ensure Docker has 2GB+ available RAM, wait 2 minutes for model download.

### API port 8000 already in use
```
ERROR: bind: address already in use
```
**Fix:** `docker-compose.yml` line 47, change `8000:8000` to `8001:8000` (or kill process on 8000).

### Avatar won't load (5173)
```
Connection refused
```
**Fix:** Ensure `helen_api` is running: `docker-compose logs helen_api`

### Avatar connects but says "API unavailable"
```
Fetch failed: localhost:8000
```
**Fix:** In browser console, check `VITE_API_URL` is set correctly in `.env`.

---

## MONITORING

### View logs in real-time

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f helen_api
docker-compose logs -f helen_airi
docker-compose logs -f ollama
```

### Health check

```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "model": "gemma:4b",
  "session_count": 1,
  "ledger_entries": 42,
  "epoch": 1
}
```

---

## SHUTDOWN

### Stop all services (persistent state kept)

```bash
docker-compose down
```

### Full cleanup (state removed)

```bash
docker-compose down -v
```

---

## SCALING

### Use larger model (if 16GB+ VRAM available)

Edit `.env`:
```
HELEN_MODEL=gemma:7b  # 7B model, higher quality, slower
```

Restart:
```bash
docker-compose restart helen_api
```

### Use different Ollama model

Any model on ollama.ai compatible:
```
HELEN_MODEL=mistral:latest
HELEN_MODEL=neural-chat:latest
HELEN_MODEL=orca-mini:latest
```

---

## ARCHITECTURE REFERENCE

- **Layer 0-2:** Proven (receipt + session + lifecycle)
- **Layer 3-6:** Ratifiable (audit + inference + memory + plans)
- **Layer 7-12:** Implementation in progress (executor + handlers + receipts + state hashing)

Current deployment uses Layers 0-2 (proven) + Layer 4 (LLM inference).

When Layers 7-12 are ready, they will be integrated without restarting containers (hot-swap executor).

---

## NEXT STEPS

1. Chat with HELEN avatar at http://localhost:5173
2. Monitor logs: `docker-compose logs -f`
3. As Phase 1-5 implementation completes, bounded execution features will become available
4. Check `/persistent/ledger.ndjson` to see receipt chain

---

**Status:** Deployment Ready
**Configuration:** Frozen (.env)
**Scaling:** Documented (change HELEN_MODEL)
**Architecture:** Documented (Layer reference)


# CONQUEST v0.1 — Launch Guide
**Real Humans. Real Time. 24-Hour Loop.**

---

## QUICKSTART (5 minutes)

### 1. Install Dependencies
```bash
pip install fastapi uvicorn
```

### 2. Run the Server
```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24
uvicorn conquest_v0_1_app:app --reload
```

You'll see:
```
Uvicorn running on http://127.0.0.1:8000
```

### 3. Open Frontend
```bash
# Option A: Open in browser manually
http://127.0.0.1:8000/conquest_v0_1_index.html

# Option B: Use Python to serve HTML
python3 -m http.server 8001 --directory /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24
# Then open: http://127.0.0.1:8001/conquest_v0_1_index.html
```

### 4. Test the Loop
- Enter name
- Issue one order (e.g., "Refine the sigil")
- Seal it
- You get a user ID
- Wait 24 hours (or modify DELAY_HOURS to 1 minute for testing)
- Return with `/return/{user_id}`

---

## FOR TESTING: 1-Minute Delay

Edit `conquest_v0_1_app.py`, line 6:

**Change:**
```python
DELAY_HOURS = 24
```

**To:**
```python
DELAY_HOURS = 0.0167  # 1 minute
```

This lets you test the full loop immediately.

**Before shipping to real users, change back to 24.**

---

## REAL USER TEST PROTOCOL

### Before Sending to User

1. **Reset the database** (delete `conquest.db`)
2. **Restart the server**
3. **Note the user ID they receive**
4. **Set a timer for 24 hours** (if using real delay)

### What You Ask Them

After they seal:
- "Don't think about it. Come back tomorrow."

After 24 hours (they return):
- "Did it feel alive?"

**Nothing else.**

No "How cool was it?"
No "Would you use this?"
Just: "Did it feel alive?"

### What You're Listening For

**Alive**: "I forgot about it, and when I came back, something had changed. That felt... real."

**Hollow**: "It was just a message. Nothing actually happened."

**Decorative**: "It's nice aesthetically, but I don't feel invested."

---

## DATABASE PERSISTENCE

The file `conquest.db` persists all data.

- **Reset between tests**: `rm conquest.db` then restart server
- **Inspect data**: SQLite browser or command line:
  ```bash
  sqlite3 conquest.db
  SELECT * FROM users;
  SELECT * FROM ledger;
  ```

---

## API ENDPOINTS (Raw)

### Create User
```
POST /create_user
Body: {"name": "Ben"}
Response: {"user_id": 1}
```

### Issue Order
```
POST /issue_order/1
Body: {"action": "Refine the sigil"}
Response: {"message": "Order recorded. The world will continue."}
```

### Seal Order
```
POST /seal/1
Response: {"message": "Sealed. What is sealed remains."}
```

### Check Return (Before 24h)
```
GET /return/1
Response: {"message": "Too early. Return in [duration]."}
```

### Check Return (After 24h)
```
GET /return/1
Response: {
  "message": "While you were away, the world continued.",
  "ledger": [
    {
      "action": "Refine the sigil",
      "timestamp": "2026-03-04T15:23:45.123456",
      "sealed": true
    }
  ]
}
```

### Get Ledger Anytime
```
GET /ledger/1
Response: [
  {"action": "...", "timestamp": "...", "sealed": true}
]
```

---

## DEPLOYMENT (Optional, for Real Users)

If you want to run this for actual remote users (not local testing):

### Option 1: Fly.io (Recommended for MVP)

```bash
# Install Fly CLI
brew install flyctl

# Login
flyctl auth login

# Create a Fly app
flyctl apps create

# Create Dockerfile in project folder:
```

**Dockerfile**:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY conquest_v0_1_app.py .
RUN pip install fastapi uvicorn
CMD ["uvicorn", "conquest_v0_1_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Deploy
flyctl deploy
```

### Option 2: Railway.app (Also Simple)

1. Push code to GitHub
2. Connect repo to Railway
3. Set environment: `PYTHONUNBUFFERED=1`
4. Railway auto-deploys

### Option 3: Render.com

Similar process, also very simple for FastAPI apps.

---

## WHAT HAPPENS NEXT

### If Test PASSES ("Did it feel alive?" → YES)

1. **Document the return moment** — Exactly what they said, how they felt, when they returned
2. **Run 2 more cycles** with 2 other humans
3. **If 2/3 say alive** → You have product validation
4. **Then**: Build out real UI, auth, multi-user, etc.

### If Test FAILS ("Did it feel alive?" → NO)

1. **Ask why specifically** — What felt hollow?
2. **Modify one element**:
   - Longer delay? Shorter?
   - Better return message?
   - Visual change needed?
3. **Re-test with different human**

### Do NOT Expand Until You Know It's Alive

No districts.
No economy.
No duels.
No social.

Just: Entry → Absence → Return → Mark.

If THAT doesn't feel alive, nothing else will.

---

## FILES YOU HAVE

1. **conquest_v0_1_app.py** — The backend (FastAPI)
2. **conquest_v0_1_index.html** — The frontend (zero dependencies, pure HTML/CSS/JS)
3. **conquest.db** — Created automatically when server starts (SQLite)

That's it.

No Node.js.
No build process.
No npm.

Pure Python + HTML.

---

## QUICK CHECKLIST

- [ ] Install FastAPI + Uvicorn
- [ ] Run `uvicorn conquest_v0_1_app:app --reload`
- [ ] Open HTML file in browser
- [ ] Create user
- [ ] Issue order
- [ ] Seal it
- [ ] Wait 1 minute (if using test delay)
- [ ] Check return
- [ ] See: "While you were away, the world continued."
- [ ] Ask: "Does it feel alive?"

---

## EDGE CASES

### User enters twice with same ID
API prevents it: "Order already issued"

### User tries to seal twice
API prevents it: "Already sealed"

### User returns before 24h
API tells them: "Too early. Return in [duration]"

### Database gets corrupted
Delete `conquest.db`, restart server, start fresh.

---

## SUCCESS METRIC

**One real human returns 24 hours later and says:**

> "I forgot about it. When I came back, it felt like the world actually moved without me. That was... different."

If you get that sentence from 2/3 testers, you have a product.

---

## NOW

Deploy this.
Run it.
Send it to 3 humans.
Listen to what they say when they return.

Everything else waits until then.

🚀


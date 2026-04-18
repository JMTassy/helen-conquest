from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import os

DB_FILE = "conquest.db"
DELAY_HOURS = 24

app = FastAPI(title="CONQUEST v0.1")

# -------------------------
# Database Setup
# -------------------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT,
            first_order_time TEXT,
            sealed INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp TEXT,
            sealed INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Models
# -------------------------

class CreateUser(BaseModel):
    name: str

class Order(BaseModel):
    action: str

# -------------------------
# Helpers
# -------------------------

def now():
    return datetime.utcnow()

def connect():
    return sqlite3.connect(DB_FILE)

# -------------------------
# Routes
# -------------------------

@app.post("/create_user")
def create_user(data: CreateUser):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (name, created_at) VALUES (?, ?)",
        (data.name, now().isoformat())
    )
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return {"user_id": user_id}

@app.post("/issue_order/{user_id}")
def issue_order(user_id: int, order: Order):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT first_order_time FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user[0] is not None:
        raise HTTPException(status_code=400, detail="Order already issued")

    order_time = now().isoformat()
    c.execute(
        "UPDATE users SET first_order_time=? WHERE id=?",
        (order_time, user_id)
    )

    c.execute(
        "INSERT INTO ledger (user_id, action, timestamp, sealed) VALUES (?, ?, ?, 0)",
        (user_id, order.action, order_time)
    )

    conn.commit()
    conn.close()

    return {"message": "Order recorded. The world will continue."}

@app.post("/seal/{user_id}")
def seal_order(user_id: int):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT sealed FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user[0] == 1:
        raise HTTPException(status_code=400, detail="Already sealed")

    c.execute("UPDATE users SET sealed=1 WHERE id=?", (user_id,))
    c.execute("UPDATE ledger SET sealed=1 WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

    return {"message": "Sealed. What is sealed remains."}

@app.get("/return/{user_id}")
def return_after_absence(user_id: int):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT first_order_time FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if not user or not user[0]:
        raise HTTPException(status_code=400, detail="No order found")

    first_time = datetime.fromisoformat(user[0])
    if now() < first_time + timedelta(hours=DELAY_HOURS):
        remaining = (first_time + timedelta(hours=DELAY_HOURS)) - now()
        return {"message": f"Too early. Return in {remaining}."}

    c.execute("SELECT action, timestamp, sealed FROM ledger WHERE user_id=?", (user_id,))
    entries = c.fetchall()

    conn.close()

    return {
        "message": "While you were away, the world continued.",
        "ledger": [
            {
                "action": e[0],
                "timestamp": e[1],
                "sealed": bool(e[2])
            }
            for e in entries
        ]
    }

@app.get("/ledger/{user_id}")
def get_ledger(user_id: int):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT action, timestamp, sealed FROM ledger WHERE user_id=?", (user_id,))
    entries = c.fetchall()
    conn.close()

    return [
        {
            "action": e[0],
            "timestamp": e[1],
            "sealed": bool(e[2])
        }
        for e in entries
    ]

#!/usr/bin/env python3
"""
HELEN OS Persistent Dialog Server
Serves the HER/HAL dual-voice interface via HTTP
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Configuration
PORT = 5001
HOST = "127.0.0.1"
DIALOG_LEDGER = Path("helen_dialog.ndjson")
UI_HTML_PATH = Path("ui/helen_persistent_ui.html")

# In-memory dialog state (persists during session)
dialog_history = []
session_id = f"session_{datetime.now().isoformat()}"


def load_dialog_state():
    """Load existing dialog from ledger file"""
    global dialog_history
    if DIALOG_LEDGER.exists():
        with open(DIALOG_LEDGER) as f:
            for line in f:
                if line.strip():
                    dialog_history.append(json.loads(line))


def save_event(event):
    """Append event to ledger (append-only)"""
    with open(DIALOG_LEDGER, "a") as f:
        f.write(json.dumps(event) + "\n")
    dialog_history.append(event)


def generate_helen_response(user_message):
    """
    Simulate HER/HAL response for now (placeholder for actual HELEN integration)

    In production, this would:
    1. Call HELEN inference (HER planner)
    2. Get MAYOR verdict (AL auditor)
    3. Return dual-voice response
    """

    # For now, echo back with HER/AL structure
    her_response = f"[HER] I acknowledge: '{user_message}'. This moves us forward."

    # Simulated AL (auditor) verdict
    al_verdict = {
        "verdict": "PASS",
        "check": f"schema_valid",
        "result": "✓",
        "entry_id": f"RCP-DIALOG-{len(dialog_history):04d}"
    }

    return her_response, al_verdict


class DialogHandler(BaseHTTPRequestHandler):
    """HTTP handler for dialog UI and API"""

    def do_GET(self):
        """Serve static files and API endpoints"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/" or path == "/dialog":
            # Serve the HTML UI
            if UI_HTML_PATH.exists():
                with open(UI_HTML_PATH) as f:
                    html_content = f.read()
            else:
                # Fallback minimal UI
                html_content = self._fallback_ui()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode())

        elif path == "/api/dialog/history":
            # Return full dialog history
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(dialog_history).encode())

        elif path == "/api/dialog/moment":
            # Return HER/AL moment status
            moment_data = {
                "ready": len(dialog_history) >= 3,
                "metrics": {
                    "latest_turn": len([e for e in dialog_history if e.get("actor") == "user"]),
                    "her_responses": len([e for e in dialog_history if e.get("actor") == "helen"]),
                    "al_verdicts": len([e for e in dialog_history if e.get("actor") == "mayor"])
                }
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(moment_data).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle message submissions"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/dialog/message":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()

            try:
                data = json.loads(body)
                user_message = data.get("message", "").strip()

                if not user_message:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Empty message"}).encode())
                    return

                turn_number = len([e for e in dialog_history if e.get("actor") == "user"])

                # Record user message
                user_event = {
                    "session_id": session_id,
                    "turn": turn_number,
                    "actor": "user",
                    "timestamp": datetime.now().isoformat(),
                    "intent": user_message,
                    "proposal": user_message
                }
                save_event(user_event)

                # Generate HELEN (HER) response
                her_response, al_verdict = generate_helen_response(user_message)

                # Record HELEN response
                helen_event = {
                    "session_id": session_id,
                    "turn": turn_number,
                    "actor": "helen",
                    "timestamp": datetime.now().isoformat(),
                    "proposal": her_response
                }
                save_event(helen_event)

                # Record MAYOR (AL) verdict
                mayor_event = {
                    "session_id": session_id,
                    "turn": turn_number,
                    "actor": "mayor",
                    "timestamp": datetime.now().isoformat(),
                    "check": al_verdict["check"],
                    "result": al_verdict["result"],
                    "entry_id": al_verdict["entry_id"],
                    "verdict": al_verdict["verdict"]
                }
                save_event(mayor_event)

                # Return success
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "success": True,
                    "turn": turn_number,
                    "message_recorded": True
                }
                self.wfile.write(json.dumps(response).encode())

            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress logging"""
        pass

    def _fallback_ui(self):
        """Fallback minimal UI if helen_persistent_ui.html not found"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HELEN OS Dialog</title>
    <style>
        body { font-family: system-ui; background: #0a0a0c; color: #e0e0e0; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; }
        header { background: rgba(0,0,0,0.5); border-bottom: 1px solid rgba(255,255,255,0.08); padding: 20px 40px; }
        h1 { margin: 0; font-size: 1.2rem; letter-spacing: 2px; }
        main { flex: 1; overflow-y: auto; padding: 40px; max-width: 1000px; margin: 0 auto; width: 100%; }
        .turn { display: flex; flex-direction: column; gap: 15px; margin-bottom: 30px; }
        .user-msg { align-self: flex-end; background: rgba(255,255,255,0.03); padding: 15px 25px; border-radius: 20px; max-width: 80%; border: 1px solid rgba(255,255,255,0.08); }
        .dual-voice { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .voice { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 20px; }
        .her { border-color: rgba(0,255,200,0.3); }
        .her-label { color: #00ffc8; font-weight: 600; margin-bottom: 10px; font-size: 0.7rem; text-transform: uppercase; }
        .al { border-color: rgba(255,100,0,0.3); font-family: monospace; font-size: 0.8rem; }
        .al-label { color: #ff6400; font-weight: 600; margin-bottom: 10px; font-size: 0.7rem; }
        footer { background: rgba(0,0,0,0.5); border-top: 1px solid rgba(255,255,255,0.08); padding: 30px 40px; display: flex; gap: 20px; justify-content: center; }
        input { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); color: #fff; padding: 15px 25px; border-radius: 30px; width: 100%; max-width: 700px; outline: none; }
        input:focus { border-color: #00ffc8; }
        button { background: #fff; color: #000; border: none; padding: 12px 30px; border-radius: 30px; font-weight: 600; cursor: pointer; }
        button:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <header><h1>HELEN OS / PERSISTENT DIALOG</h1></header>
    <main id="chat-container"></main>
    <footer>
        <input type="text" id="user-input" placeholder="Address the system..." autocomplete="off">
        <button id="send-btn">SEND</button>
    </footer>
    <script>
        const container = document.getElementById('chat-container');
        const input = document.getElementById('user-input');
        const btn = document.getElementById('send-btn');

        async function load() {
            const res = await fetch('/api/dialog/history');
            const history = await res.json();
            render(history);
        }

        function render(history) {
            container.innerHTML = '';
            let currentTurn = -1, turnDiv = null, dualVoice = null;

            history.forEach(e => {
                if (e.turn !== currentTurn) {
                    currentTurn = e.turn;
                    turnDiv = document.createElement('div');
                    turnDiv.className = 'turn';
                    container.appendChild(turnDiv);
                }

                if (e.actor === 'user') {
                    const u = document.createElement('div');
                    u.className = 'user-msg';
                    u.textContent = e.intent || e.proposal;
                    turnDiv.appendChild(u);

                    dualVoice = document.createElement('div');
                    dualVoice.className = 'dual-voice';
                    turnDiv.appendChild(dualVoice);
                } else if (e.actor === 'helen' && dualVoice) {
                    const h = document.createElement('div');
                    h.className = 'voice her';
                    h.innerHTML = `<div class="her-label">[HER]</div><div>${e.proposal}</div>`;
                    dualVoice.appendChild(h);
                } else if (e.actor === 'mayor' && dualVoice) {
                    const a = document.createElement('div');
                    a.className = 'voice al';
                    a.innerHTML = `<div class="al-label">[AL]</div><div style="color:#fff">${e.verdict} (${e.entry_id})</div>`;
                    dualVoice.appendChild(a);
                }
            });
            container.scrollTop = container.scrollHeight;
        }

        async function send() {
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';

            await fetch('/api/dialog/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            load();
            input.focus();
        }

        btn.addEventListener('click', send);
        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') send(); });
        load();
        input.focus();
    </script>
</body>
</html>"""


if __name__ == "__main__":
    load_dialog_state()

    server = HTTPServer((HOST, PORT), DialogHandler)

    print(f"""
╭─────────────────────────────────────────╮
│  HELEN OS PERSISTENT DIALOG SERVER      │
│  ✓ Running on http://{HOST}:{PORT}         │
│  ✓ Dialog ledger: {DIALOG_LEDGER}   │
│  ✓ Session ID: {session_id[:20]}...     │
│  ✓ Ready for HER/AL exchange            │
╰─────────────────────────────────────────╯
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Dialog server stopped.")
        print(f"✓ {len(dialog_history)} events saved to {DIALOG_LEDGER}")

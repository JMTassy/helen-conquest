#!/usr/bin/env python3
"""
HELEN Persistent Dialog UI
Web-based interface for continuous interaction with HELEN ledger system.
Runs on localhost:5001 (separate from street1-server port 3001, helen_ui_server port 3333).
"""
import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Add repo to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, static_folder="static", template_folder="templates")

# Configuration
LEDGER_PATH = os.path.join(os.getcwd(), "town", "ledger_v1.ndjson")
HELEN_SAY_SCRIPT = os.path.join(os.path.dirname(__file__), "helen_say.py")
SOCK_PATH = os.path.expanduser("~/.openclaw/oracle_town.sock")

@app.route("/")
def index():
    """Serve the HELEN dialogue UI."""
    return render_template("helen_ui.html")

@app.route("/api/send", methods=["POST"])
def send_message():
    """Send a message to HELEN and return the response."""
    data = request.json
    msg = data.get("message", "").strip()
    op = data.get("op", "fetch")  # fetch, dialog, shell
    
    if not msg:
        return jsonify({"error": "Empty message"}), 400
    
    try:
        # Call helen_say.py
        result = subprocess.run(
            ["python3", HELEN_SAY_SCRIPT, msg, "--op", op, "--ledger", LEDGER_PATH],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse output
        output = result.stdout + result.stderr
        lines = output.split("\n")
        
        her_text = ""
        hal_json = {}
        
        # Extract HER and HAL from output
        in_her = False
        in_hal = False
        her_lines = []
        hal_lines = []
        
        for line in lines:
            if "[HER]" in line:
                in_her = True
                in_hal = False
                continue
            elif "[HAL]" in line:
                in_her = False
                in_hal = True
                # Extract verdict color
                if "PASS" in line:
                    verdict = "PASS"
                elif "WARN" in line:
                    verdict = "WARN"
                elif "BLOCK" in line:
                    verdict = "BLOCK"
                else:
                    verdict = "?"
                continue
            
            if in_her:
                her_lines.append(line)
            elif in_hal and line.strip().startswith("{"):
                # Remove ANSI codes and parse JSON
                clean_line = line
                for code in ["\x1b[0m", "\x1b[2m", "\x1b[36m", "\x1b[35m", "\x1b[32m", "\x1b[33m", "\x1b[31m"]:
                    clean_line = clean_line.replace(code, "")
                try:
                    hal_json = json.loads(clean_line)
                except:
                    pass
        
        her_text = "\n".join(her_lines).strip()
        
        return jsonify({
            "success": True,
            "her": her_text,
            "hal": hal_json,
            "verdict": hal_json.get("verdict", "?")
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timeout"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ledger", methods=["GET"])
def get_ledger():
    """Return recent ledger events."""
    try:
        events = []
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH, "r") as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        
        # Return last 20 events
        return jsonify({"events": events[-20:]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def get_status():
    """Return system status."""
    status = {
        "kernel_socket": os.path.exists(SOCK_PATH),
        "ledger_path": LEDGER_PATH,
        "ledger_exists": os.path.exists(LEDGER_PATH),
        "ui_version": "1.0"
    }
    return jsonify(status)

if __name__ == "__main__":
    # Create templates directory if needed
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print("Starting HELEN UI on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    app.run(host="127.0.0.1", port=5001, debug=False)

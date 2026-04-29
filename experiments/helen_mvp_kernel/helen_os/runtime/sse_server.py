"""Minimal SSE server — streams state snapshots over HTTP.

No Flask. Pure stdlib. Subscribe at GET /state for a text/event-stream.

Usage:
    python -m helen_os.runtime.sse_server --ledger path/to/events.ndjson --port 8765

The surface subscribes; the kernel remains the source of truth.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from helen_os.runtime.state_observer import tail

_LEDGER_PATH: Path = Path("ledger/events.ndjson")
_POLL_INTERVAL: float = 0.25


class _SSEHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args) -> None:
        pass  # suppress default access log noise

    def do_GET(self) -> None:
        if self.path != "/state":
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            for snapshot in tail(_LEDGER_PATH, poll_interval=_POLL_INTERVAL):
                line = f"data: {json.dumps(snapshot)}\n\n"
                self.wfile.write(line.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def serve(ledger_path: Path, port: int = 8765) -> None:
    global _LEDGER_PATH
    _LEDGER_PATH = ledger_path
    server = HTTPServer(("127.0.0.1", port), _SSEHandler)
    print(f"HELEN state observer → http://127.0.0.1:{port}/state")
    print(f"ledger: {ledger_path}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HELEN SSE state observer")
    parser.add_argument("--ledger", default="ledger/events.ndjson")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(Path(args.ledger), args.port)

#!/usr/bin/env python3
"""
Minimal HTTP server serving `tools/helen_page.html` and POST /api/chat -> HELEN reply
No external dependencies.

Run:
  python3 tools/helen_page_server.py --port 8000

Then open http://localhost:8000/
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import json
import os
from urllib.parse import urlparse

ROOT = os.getcwd()
PAGE_PATH = os.path.join(ROOT, 'tools', 'helen_page.html')

class Handler(BaseHTTPRequestHandler):
    def _set_json(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.end_headers()

    def _set_html(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            if os.path.exists(PAGE_PATH):
                self._set_html()
                with open(PAGE_PATH, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, 'page not found')
                return
        # Serve static files under /tools/ (e.g. azvatar.svg)
        if path.startswith('/tools/'):
            fs_path = os.path.join(ROOT, path.lstrip('/'))
            if os.path.exists(fs_path) and os.path.isfile(fs_path):
                # set content-type for svg and simple types
                if fs_path.endswith('.svg'):
                    self.send_response(200)
                    self.send_header('Content-Type','image/svg+xml; charset=utf-8')
                    self.end_headers()
                    with open(fs_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                # fallback: stream as binary
                self.send_response(200)
                self.send_header('Content-Type','application/octet-stream')
                self.end_headers()
                with open(fs_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Simple state bootstrap endpoint for the page to fetch avatar + summary
        if path == '/api/state':
            try:
                import sys
                sys.path.insert(0, os.getcwd())
                from tools.helen_local_cli import HelenLocal
                h = HelenLocal()
                state = {
                    'avatar': h.avatar,
                    'summary': h.summarize_state(),
                    'recent_wisdom': h.recent_wisdom(3)
                }
                self._set_json(200)
                self.wfile.write(json.dumps(state, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self._set_json(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return
        # otherwise serve 404
        self.send_error(404, 'not found')

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/api/chat':
            length = int(self.headers.get('Content-Length','0'))
            raw = self.rfile.read(length).decode('utf-8') if length else ''
            try:
                data = json.loads(raw) if raw else {}
            except Exception:
                data = {}
            text = data.get('text','')
            # call local HELEN
            reply = self._call_helen(text)
            self._set_json(200)
            self.wfile.write(json.dumps({'reply': reply}, ensure_ascii=False).encode('utf-8'))
            return
        self.send_error(404, 'not found')

    def log_message(self, format, *args):
        # reduce noise
        return

    def _call_helen(self, text: str) -> str:
        try:
            # import here to avoid top-level dependency if user doesn't run server
            import sys
            sys.path.insert(0, os.getcwd())
            from tools.helen_local_cli import HelenLocal
            h = HelenLocal()
            return h.reply(text)
        except Exception as e:
            return f"ERROR: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8000)
    args = ap.parse_args()
    server = HTTPServer(('0.0.0.0', args.port), Handler)
    print(f"Serving HELEN page on http://localhost:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping')
        server.server_close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
hello.py – Long-running HTTP service for the DevOps assessment.

Endpoints:
  GET /        → 200  "Hello, DevOps!"
  GET /health  → 200  "healthy"
  any other    → 404  "Not Found"

Usage:
  python hello.py

Test:
  curl http://localhost:8080
  curl http://localhost:8080/health
"""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))


class DevOpsHandler(BaseHTTPRequestHandler):
    """Handle incoming HTTP GET requests."""

    ROUTES = {
        "/": (200, "Hello, DevOps!"),
        "/health": (200, "healthy"),
    }

    def do_GET(self):
        status, body = self.ROUTES.get(self.path, (404, "Not Found"))
        encoded = body.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

        ts = datetime.now(timezone.utc).isoformat()
        print(f'[{ts}] {self.command} {self.path} → {status} "{body}"', flush=True)

    def log_message(self, fmt, *args):
        # Suppress the default Apache-style log; we handle it in do_GET.
        pass


def main():
    server = HTTPServer((HOST, PORT), DevOpsHandler)
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] DevOps HTTP server starting on {HOST}:{PORT}", flush=True)
    print(f"[{ts}] Routes: GET /  →  Hello, DevOps! | GET /health  →  healthy", flush=True)
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        ts = datetime.now(timezone.utc).isoformat()
        print(f"[{ts}] Server shutting down.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
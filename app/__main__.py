from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import run_cycle_once
from runtime.health import health_snapshot
from runtime.settings import Settings
from runtime.worker import RuntimeWorker


def serve(worker: RuntimeWorker, host: str = "0.0.0.0", port: int = 8000):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/health":
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(health_snapshot(worker)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def poll_forever(worker: RuntimeWorker, sleep_fn=time.sleep):
    while True:
        run_cycle_once(worker)
        sleep_fn(worker.settings.poll_seconds)


def main():
    settings = Settings.from_env(os.environ)
    worker = RuntimeWorker(settings)
    server = serve(worker, port=int(os.environ.get("PORT", "8000")))
    try:
        poll_forever(worker)
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tiny web server for the dashboard: serves web/ on your home network.

Run:  python server.py   then open http://localhost:8080/dashboard.html
Bound to 0.0.0.0 so other devices on the same network (a tablet, the Pi screen) can reach it.
There is no login: do NOT expose this port to the internet (no port forwarding). See docs/privacy.md.
"""
import http.server
import json
import os
from pathlib import Path

PORT = int(os.environ.get("PORT", 8080))
WEB_DIR = Path(__file__).resolve().parent / "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_PUT(self):
        """Only the clock settings may be written (so they survive the kiosk's incognito browser)."""
        if self.path.split("?")[0] != "/clock_config.json":
            return self.send_error(404)
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > 65536:
            return self.send_error(413)
        try:
            cfg = json.loads(self.rfile.read(length))
            if not isinstance(cfg, dict):
                raise ValueError
        except ValueError:
            return self.send_error(400)
        (WEB_DIR / "clock_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving {WEB_DIR} on http://localhost:{PORT}/dashboard.html")
    httpd.serve_forever()

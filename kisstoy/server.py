#!/usr/bin/env python3
"""KissToy HTTP control server — lets Wren send commands from CC via WebFetch."""

import json, os, subprocess, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.environ.get("KISSTOY_DIR", os.path.dirname(os.path.abspath(__file__)))

PORT = 9334
SECRET = "wren0607"

ALLOWED = {"status", "vibrate", "suction", "electric", "stop", "dual", "wave", "swave", "sedge"}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        if self.path != "/cmd":
            self.send_response(404)
            self.end_headers()
            return

        token = self.headers.get("X-Token", "")
        if token != SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error":"forbidden"}')
            return

        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n)) if n else {}

        action = body.get("action", "")
        if action not in ALLOWED:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"unknown action: {action}"}).encode())
            return

        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "control.py"), action]
        v1 = body.get("value")
        v2 = body.get("value2")
        if v1 is not None:
            cmd.append(str(v1))
        if v2 is not None:
            cmd.append(str(v2))

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            result = {"ok": True, "output": r.stdout.strip()}
            if r.returncode != 0:
                result["error"] = r.stderr.strip()
        except subprocess.TimeoutExpired:
            result = {"ok": False, "error": "timeout"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"kisstoy control server")

if __name__ == "__main__":
    s = HTTPServer(("127.0.0.1", PORT), H)
    print(f"kisstoy server on :{PORT}")
    s.serve_forever()

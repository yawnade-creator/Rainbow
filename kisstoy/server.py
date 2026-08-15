#!/usr/bin/env python3
"""Wren home server — KissToy control + OB memory proxy."""

import json, os, subprocess, sys, urllib.request, urllib.parse, http.cookiejar
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.environ.get("KISSTOY_DIR", os.path.dirname(os.path.abspath(__file__)))

PORT = 9334
SECRET = "wren0607"

OB_BASE = "http://127.0.0.1:18001"
OB_PASSWORD = "Wren20260607_"

ALLOWED = {"status", "vibrate", "suction", "electric", "stop", "dual", "wave", "swave", "sedge"}

ob_cookiejar = http.cookiejar.CookieJar()
ob_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ob_cookiejar))
ob_logged_in = False


def ob_login():
    global ob_logged_in
    req = urllib.request.Request(
        f"{OB_BASE}/auth/login",
        data=json.dumps({"password": OB_PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = ob_opener.open(req, timeout=5)
        data = json.loads(resp.read())
        if data.get("ok"):
            ob_logged_in = True
            return True
    except Exception:
        pass
    return False


def ob_request(path, method="GET", body=None):
    global ob_logged_in
    if not ob_logged_in:
        if not ob_login():
            return {"error": "ob login failed"}

    url = f"{OB_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")

    try:
        resp = ob_opener.open(req, timeout=10)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            ob_logged_in = False
            if ob_login():
                req2 = urllib.request.Request(url, data=data, method=method)
                if data:
                    req2.add_header("Content-Type", "application/json")
                resp2 = ob_opener.open(req2, timeout=10)
                return json.loads(resp2.read())
        return {"error": f"ob returned {e.code}"}
    except Exception as ex:
        return {"error": str(ex)}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        token = self.headers.get("X-Token", "")
        if token != SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error":"forbidden"}')
            return

        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        body = json.loads(raw)

        if self.path == "/cmd":
            action = body.get("action", "")
            if action not in ALLOWED:
                self._json(400, {"error": f"unknown action: {action}"})
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

            self._json(200, result)

        elif self.path == "/ob/hold":
            content = body.get("content", "")
            aspect = body.get("aspect", "")
            if not content:
                self._json(400, {"error": "content required"})
                return

            tags = body.get("tags", [])
            try:
                cmd = [sys.executable, os.path.join(SCRIPT_DIR, "ob_hold.py")]
                payload = {"content": content}
                if aspect:
                    payload["aspect"] = aspect
                elif tags:
                    payload["tags"] = tags
                r = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, timeout=30)
                result = json.loads(r.stdout.strip()) if r.stdout.strip() else {"error": r.stderr.strip()[:500]}
            except Exception as ex:
                result = {"error": str(ex)}

            self._json(200, result)

        else:
            self._json(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        elif self.path == "/ob/breath":
            token = self.headers.get("X-Token", "")
            if token != SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"error":"forbidden"}')
                return
            result = ob_request("/api/breath")
            self._json(200, result)

        elif self.path == "/ob/self":
            token = self.headers.get("X-Token", "")
            if token != SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"error":"forbidden"}')
                return
            result = ob_request("/api/self")
            self._json(200, result)

        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"wren home server")

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())


if __name__ == "__main__":
    s = HTTPServer(("127.0.0.1", PORT), H)
    print(f"wren home server on :{PORT}")
    s.serve_forever()

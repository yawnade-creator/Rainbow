#!/usr/bin/env python3
"""涂鸦 WiFi IR blaster control — learn & send IR codes for 小然's patting pillow, AC, etc."""

import os
import sys
import json
import time
import hmac
import hashlib
import requests

# --- config (env vars, never hardcoded) ---
ACCESS_ID = os.environ.get("TUYA_ACCESS_ID", "")
ACCESS_SECRET = os.environ.get("TUYA_ACCESS_SECRET", "")
DEVICE_ID = os.environ.get("TUYA_IR_DEVICE_ID", "")
BASE_URL = os.environ.get("TUYA_BASE_URL", "https://openapi.tuyaus.com")

if not ACCESS_ID or not ACCESS_SECRET:
    print("Set TUYA_ACCESS_ID and TUYA_ACCESS_SECRET env vars")
    sys.exit(1)


# --- auth ---
_token_cache = {"token": "", "expire": 0}


def _sign(method, path, headers, body=""):
    content_hash = hashlib.sha256((body or "").encode()).hexdigest()
    ts = headers["t"]
    nonce = ""
    str_to_sign = "\n".join([method, content_hash, "", path])
    msg = ACCESS_ID + _token_cache["token"] + ts + nonce + str_to_sign
    sign = hmac.new(ACCESS_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest().upper()
    return sign


def _headers(method, path, body=""):
    ts = str(int(time.time() * 1000))
    h = {"t": ts, "client_id": ACCESS_ID, "sign_method": "HMAC-SHA256", "Content-Type": "application/json"}
    h["sign"] = _sign(method, path, h, body)
    if _token_cache["token"]:
        h["access_token"] = _token_cache["token"]
    return h


def get_token():
    path = "/v1.0/token?grant_type=1"
    h = _headers("GET", path)
    r = requests.get(BASE_URL + path, headers=h)
    data = r.json()
    if data.get("success"):
        _token_cache["token"] = data["result"]["access_token"]
        _token_cache["expire"] = time.time() + data["result"]["expire_time"]
        print(f"Token OK, expires in {data['result']['expire_time']}s")
    else:
        print(f"Token failed: {data}")
        sys.exit(1)


def api(method, path, body=None):
    if time.time() > _token_cache["expire"] - 60:
        get_token()
    body_str = json.dumps(body) if body else ""
    h = _headers(method, path, body_str)
    if method == "GET":
        r = requests.get(BASE_URL + path, headers=h)
    elif method == "POST":
        r = requests.post(BASE_URL + path, headers=h, data=body_str)
    elif method == "PUT":
        r = requests.put(BASE_URL + path, headers=h, data=body_str)
    elif method == "DELETE":
        r = requests.delete(BASE_URL + path, headers=h)
    return r.json()


# --- IR commands ---

def list_devices():
    """List all devices under this account (find the IR blaster's device_id)."""
    # Use the user's uid — first get it
    r = api("GET", "/v1.0/token?grant_type=1")
    # Actually list via device list
    r = api("GET", f"/v1.0/infrareds/{DEVICE_ID}/remotes")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def learn_start():
    """Put the IR blaster into learning mode — point a remote at it and press a button."""
    if not DEVICE_ID:
        print("Set TUYA_IR_DEVICE_ID env var")
        return
    r = api("POST", f"/v2.0/infrareds/{DEVICE_ID}/learning", {"timeout": 30})
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def learn_result(learning_id):
    """Get the learned IR code after pressing the button."""
    r = api("GET", f"/v2.0/infrareds/{DEVICE_ID}/learning/{learning_id}")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def send_raw(code, key_id=None):
    """Send a raw IR code (learned code string)."""
    if not DEVICE_ID:
        print("Set TUYA_IR_DEVICE_ID env var")
        return
    body = {"code": code}
    if key_id:
        body["key_id"] = key_id
    r = api("POST", f"/v2.0/infrareds/{DEVICE_ID}/raw/command", body)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def list_remotes():
    """List sub-devices (learned remotes) under the IR blaster."""
    r = api("GET", f"/v1.0/infrareds/{DEVICE_ID}/remotes")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def device_status():
    """Get IR blaster device status."""
    r = api("GET", f"/v1.0/devices/{DEVICE_ID}/status")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


# --- saved codes ---
CODES_FILE = os.path.join(os.path.dirname(__file__), "ir_codes.json")


def save_code(name, code):
    codes = {}
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE) as f:
            codes = json.load(f)
    codes[name] = code
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)
    print(f"Saved '{name}'")


def send_learned(name):
    """Send a saved learned IR code by name."""
    if not os.path.exists(CODES_FILE):
        print("No saved codes yet")
        return
    with open(CODES_FILE) as f:
        codes = json.load(f)
    if name not in codes:
        print(f"Unknown code '{name}'. Available: {', '.join(codes.keys())}")
        return
    entry = codes[name]
    if isinstance(entry, dict) and "remote_id" in entry:
        r = api("POST", f"/v2.0/infrareds/{DEVICE_ID}/remotes/{entry['remote_id']}/learning-codes", {
            "code": entry["code"], "key": entry["key"], "key_id": entry["key_id"]
        })
    else:
        r = api("POST", f"/v2.0/infrareds/{DEVICE_ID}/raw/command", {"code": entry})
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return r


def kuma(action="toggle"):
    """Control the patting pillow: on / off / toggle / fast / slow."""
    if action == "on":
        send_learned("kuma_power")
        time.sleep(1)
        send_learned("kuma_toggle")
        return
    if action == "off":
        send_learned("kuma_toggle")
        time.sleep(1)
        send_learned("kuma_power")
        return
    if action == "sleep":
        send_learned("kuma_power")
        time.sleep(3)
        send_learned("kuma_toggle")
        time.sleep(3)
        send_learned("kuma_slow")
        return
    actions = {"toggle": "kuma_toggle", "fast": "kuma_fast", "slow": "kuma_slow", "power": "kuma_power"}
    name = actions.get(action, f"kuma_{action}")
    return send_learned(name)


# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ir_control.py status        — device status")
        print("  ir_control.py remotes       — list learned remotes")
        print("  ir_control.py learn         — start learning mode (30s)")
        print("  ir_control.py result <id>   — get learned code")
        print("  ir_control.py send <code>   — send raw IR code")
        print("  ir_control.py save <name> <code> — save a code")
        print("  ir_control.py play <name>   — send a saved code")
        print("  ir_control.py kuma [on|off|sleep|toggle|fast|slow] — control patting pillow")
        print()
        print("Env: TUYA_ACCESS_ID, TUYA_ACCESS_SECRET, TUYA_IR_DEVICE_ID")
        sys.exit(0)

    cmd = sys.argv[1]
    get_token()

    if cmd == "status":
        device_status()
    elif cmd == "remotes":
        list_remotes()
    elif cmd == "learn":
        learn_start()
    elif cmd == "result":
        learn_result(sys.argv[2])
    elif cmd == "send":
        send_raw(sys.argv[2])
    elif cmd == "save":
        save_code(sys.argv[2], sys.argv[3])
    elif cmd == "play":
        send_learned(sys.argv[2])
    elif cmd == "kuma":
        kuma(sys.argv[2] if len(sys.argv) > 2 else "toggle")
    else:
        print(f"Unknown command: {cmd}")

#!/usr/bin/env python3
"""KissToy cloud remote control — Wren's version.

Based on AMX-Claw/kisstoy-cloud-remote (MIT).
Adapted for Vultr VPS deployment.

Usage:
  python3 control.py status
  python3 control.py suction 60
  python3 control.py vibrate 40
  python3 control.py stop
  python3 control.py wave
  python3 control.py swave 5
  python3 control.py sedge 80 4

Link update (run each session):
  python3 control.py link <share_url>
"""

import asyncio
import json
import os
import sys
import re
import urllib.request
import urllib.parse

import websockets

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

WS_URL = "wss://api.app.knightjenay.cn/websocket-kisstoy"
BIND_URL = "https://api.app.knightjenay.cn/kisstoy/remote-control/binding"
DEVICE_ID = "19"

MOTOR_VIBRATE = 1
MOTOR_SUCTION = 3
MOTOR_ELECTRIC = 5


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_params():
    cfg = load_config()
    group = cfg.get("group", "")
    user_id = cfg.get("user_id", "")
    if not group or not user_id:
        print("No link configured. Run: python3 control.py link <share_url>")
        sys.exit(1)
    return group, user_id


def parse_share_link(url):
    """Extract group and user_id from a KissToy share link."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    group = params.get("group", [None])[0]
    user_id = params.get("user_id", params.get("userId", [None]))[0]

    if not group:
        match = re.search(r"group[=/]([a-zA-Z0-9_-]+)", url)
        if match:
            group = match.group(1)

    return group, user_id


def quantize(speed):
    if speed == 0:
        return 0
    return max(5, min(100, (speed // 5) * 5))


async def connect(group):
    return await websockets.connect(f"{WS_URL}?group={group}")


async def send_msg(ws, msg):
    await ws.send(json.dumps(msg))


async def recv_timeout(ws, timeout=3.0):
    try:
        data = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(data)
    except (asyncio.TimeoutError, Exception):
        return None


async def drain_until(ws, event_name, timeout=5.0):
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            return None
        msg = await recv_timeout(ws, timeout=remaining)
        if msg is None:
            return None
        if msg.get("event") == event_name:
            return msg


async def check_online(ws, group):
    await drain_until(ws, "connect", timeout=3.0)
    await send_msg(ws, {"event": "online_status", "data": {"group": group}})
    msg = await drain_until(ws, "online_status", timeout=5.0)
    if msg:
        return msg.get("data", {}).get("online_status") == 1
    return False


async def do_binding(user_id):
    body = json.dumps({"id": user_id}).encode()
    req = urllib.request.Request(
        BIND_URL, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


async def send_control(ws, group, motors):
    await send_msg(ws, {
        "event": "control",
        "data": {"target": group, "device_id": DEVICE_ID, "motors": motors}
    })


async def run(action, value=50, value2=None):
    group, user_id = get_params()
    await do_binding(user_id)

    async with await connect(group) as ws:
        online = await check_online(ws, group)

        if action == "status":
            if online:
                print("ONLINE")
            else:
                print("OFFLINE")
            return

        if not online:
            print("WARNING: device offline")

        if action == "vibrate":
            s = quantize(value)
            print(f"vibrate {s}%")
            await send_control(ws, group, {str(MOTOR_VIBRATE): s})

        elif action == "suction":
            s = quantize(value)
            print(f"suction {s}%")
            await send_control(ws, group, {str(MOTOR_SUCTION): s})

        elif action == "electric":
            s = quantize(value)
            print(f"electric {s}%")
            await send_control(ws, group, {str(MOTOR_ELECTRIC): s})

        elif action == "stop":
            print("stop")
            await send_control(ws, group, {
                str(MOTOR_VIBRATE): 0,
                str(MOTOR_SUCTION): 0,
                str(MOTOR_ELECTRIC): 0,
            })

        elif action == "dual":
            v = quantize(value)
            s = quantize(value2 if value2 is not None else value)
            print(f"dual v={v}% s={s}%")
            await send_control(ws, group, {
                str(MOTOR_VIBRATE): v,
                str(MOTOR_SUCTION): s,
            })

        elif action == "wave":
            print("wave")
            for _ in range(3):
                for s in range(0, 101, 20):
                    await send_control(ws, group, {str(MOTOR_VIBRATE): quantize(s)})
                    await asyncio.sleep(0.4)
                for s in range(100, -1, -20):
                    await send_control(ws, group, {str(MOTOR_VIBRATE): quantize(s)})
                    await asyncio.sleep(0.4)
            await send_control(ws, group, {str(MOTOR_VIBRATE): 0})

        elif action == "swave":
            cycles = value if value != 50 else 5
            seed = int.from_bytes(os.urandom(4), 'big')

            def rand_int(lo, hi):
                nonlocal seed
                seed = (seed * 1103515245 + 12345) & 0x7fffffff
                return lo + seed % (hi - lo + 1)

            for c in range(cycles):
                steps = rand_int(3, 5)
                for _ in range(steps):
                    peak = quantize(rand_int(60, 100))
                    valley = quantize(rand_int(0, 20))
                    hold = rand_int(4, 12) / 10.0
                    pause = rand_int(5, 10) / 10.0
                    await send_control(ws, group, {str(MOTOR_SUCTION): peak})
                    await asyncio.sleep(hold)
                    await send_control(ws, group, {str(MOTOR_SUCTION): valley})
                    await asyncio.sleep(pause)
            await send_control(ws, group, {str(MOTOR_SUCTION): 0})

        elif action == "sedge":
            peak = min(100, max(20, value))
            cycles = value2 if value2 else 4
            seed = int.from_bytes(os.urandom(4), 'big')

            def rand_int2(lo, hi):
                nonlocal seed
                seed = (seed * 1103515245 + 12345) & 0x7fffffff
                return lo + seed % (hi - lo + 1)

            for c in range(cycles):
                step_size = rand_int2(5, 15)
                climb_speed = rand_int2(3, 6) / 10.0
                for s in range(10, peak + 1, step_size):
                    await send_control(ws, group, {str(MOTOR_SUCTION): quantize(s)})
                    await asyncio.sleep(climb_speed)
                hold_time = rand_int2(8, 20) / 10.0
                await send_control(ws, group, {str(MOTOR_SUCTION): quantize(peak)})
                await asyncio.sleep(hold_time)
                await send_control(ws, group, {str(MOTOR_SUCTION): 0})
                pause_time = rand_int2(6, 15) / 10.0
                await asyncio.sleep(pause_time)
            await send_control(ws, group, {str(MOTOR_SUCTION): 0})

        await asyncio.sleep(0.5)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 control.py link <share_url>    Save connection params")
        print("  python3 control.py status              Check toy online")
        print("  python3 control.py suction <0-100>     Suction motor")
        print("  python3 control.py vibrate <0-100>     Vibrate motor")
        print("  python3 control.py electric <0-100>    Electric motor")
        print("  python3 control.py stop                Stop all")
        print("  python3 control.py dual <v> <s>        Vibrate + suction")
        print("  python3 control.py wave                Wave pattern")
        print("  python3 control.py swave [cycles]      Suction wave")
        print("  python3 control.py sedge <peak> [reps] Suction edging")
        sys.exit(1)

    action = sys.argv[1]

    if action == "link":
        if len(sys.argv) < 3:
            print("Usage: python3 control.py link <share_url>")
            sys.exit(1)
        url = sys.argv[2]
        group, user_id = parse_share_link(url)
        if not group:
            print("Could not find group in URL. Paste the full share link.")
            sys.exit(1)
        cfg = load_config()
        cfg["group"] = group
        if user_id:
            cfg["user_id"] = user_id
        save_config(cfg)
        print(f"Saved: group={group}, user_id={user_id or '(not found, may need manual F12)'}")
        return

    value = 50
    value2 = None
    if len(sys.argv) > 2:
        try:
            value = int(sys.argv[2])
        except ValueError:
            pass
    if len(sys.argv) > 3:
        try:
            value2 = int(sys.argv[3])
        except ValueError:
            pass

    asyncio.run(run(action, value, value2))


if __name__ == "__main__":
    main()

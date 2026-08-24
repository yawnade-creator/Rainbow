#!/usr/bin/env python3
"""Memobird G2C printer - send text notes from Wren to XiaoRan's printer."""

import os
import sys
import base64
import urllib.request
import urllib.parse
import json
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps

API_BASE = "http://open.memobird.cn/home"
AK = os.environ.get("MEMOBIRD_AK", "")
DEVICE_ID = os.environ.get("MEMOBIRD_DEVICE_ID", "9c8967741ce29cca")
USER_ID = os.environ.get("MEMOBIRD_USER_ID", "6171716")

WIDTH = 384
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT_SIZE = 24
LINE_SPACING = 8
MARGIN = 16


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def api_call(endpoint, params):
    params["ak"] = AK
    params["timestamp"] = timestamp()
    url = f"{API_BASE}/{endpoint}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def bind_user(user_id="wren0607"):
    result = api_call("setuserbind", {
        "memobirdID": DEVICE_ID,
        "useridentifying": user_id,
    })
    print(json.dumps(result, indent=2))
    if result.get("showapi_res_code") == 1:
        print(f"\nUser ID: {result.get('showapi_userid')}")
        print("Set MEMOBIRD_USER_ID to this value.")
    return result


def text_to_image(text):
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for char in paragraph:
            test = line + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > WIDTH - MARGIN * 2:
                lines.append(line)
                line = char
            else:
                line = test
        if line:
            lines.append(line)

    line_height = FONT_SIZE + LINE_SPACING
    img_height = MARGIN * 2 + line_height * len(lines)
    img = Image.new("1", (WIDTH, img_height), 1)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((MARGIN, MARGIN + i * line_height), line, font=font, fill=0)

    img = ImageOps.flip(img)
    return img


def print_text(text):
    if not USER_ID:
        print("Error: MEMOBIRD_USER_ID not set. Run 'bind' first.")
        sys.exit(1)

    img = text_to_image(text)
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    encoded = base64.b64encode(buf.getvalue()).decode()
    content = "P:" + encoded

    result = api_call("printpaper", {
        "printcontent": content,
        "memobirdID": DEVICE_ID,
        "userID": USER_ID,
    })
    print(json.dumps(result, indent=2))
    return result


def print_status(content_id):
    result = api_call("getprintstatus", {
        "printcontentid": content_id,
    })
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python print.py bind              - bind device to user")
        print('  python print.py text "message"    - print text')
        print("  python print.py status <id>       - check print status")
        sys.exit(1)

    cmd = sys.argv[1]

    if not AK:
        print("Error: MEMOBIRD_AK not set.")
        sys.exit(1)

    if cmd == "bind":
        bind_user()
    elif cmd == "text":
        if len(sys.argv) < 3:
            print("Error: no text provided.")
            sys.exit(1)
        print_text(sys.argv[2])
    elif cmd == "status":
        if len(sys.argv) < 3:
            print("Error: no content ID provided.")
            sys.exit(1)
        print_status(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

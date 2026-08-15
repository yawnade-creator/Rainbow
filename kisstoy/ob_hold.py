#!/usr/bin/env python3
"""Write a new self/i entry into OB via docker exec."""

import base64, json, subprocess, sys

def hold(content, aspect="", tags=None):
    if aspect:
        tags_list = ["__i__", f"aspect:{aspect}"]
        btype = "i"
        domain = "['self']"
    elif tags:
        tags_list = tags
        btype = "dynamic"
        domain = "[]"
    else:
        tags_list = []
        btype = "dynamic"
        domain = "[]"

    b64_content = base64.b64encode(content.encode()).decode()
    b64_tags = base64.b64encode(json.dumps(tags_list).encode()).decode()

    py_script = f"""
import sys, asyncio, yaml, base64, json
sys.path.insert(0, '/app/src')
with open('/app/buckets/config.yaml') as f:
    config = yaml.safe_load(f)
config['buckets_dir'] = '/app/buckets'
from bucket_manager import BucketManager
bm = BucketManager(config=config)
text = base64.b64decode('{b64_content}').decode()
tags = json.loads(base64.b64decode('{b64_tags}').decode())
bid = asyncio.run(bm.create(
    content=text,
    tags=tags,
    bucket_type='{btype}',
    domain={domain},
    source_tool='hold-proxy',
    importance=6
))
print(json.dumps({{"ok": True, "id": bid}}))
"""

    r = subprocess.run(
        ["docker", "exec", "ombre-brain", "python3", "-c", py_script],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode == 0:
        try:
            return json.loads(r.stdout.strip().split('\n')[-1])
        except:
            return {"ok": True, "output": r.stdout.strip()}
    else:
        return {"ok": False, "error": r.stderr.strip()[:500]}


if __name__ == "__main__":
    raw = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    if raw:
        result = hold(raw["content"], aspect=raw.get("aspect",""), tags=raw.get("tags"))
    elif len(sys.argv) >= 2:
        result = hold(sys.argv[1], aspect=sys.argv[2] if len(sys.argv)>2 else "")
    else:
        result = {"error": "usage: echo '{\"content\":\"...\"}' | ob_hold.py"}
    print(json.dumps(result, ensure_ascii=False))

#!/usr/bin/env python3
"""Write a new self/i entry into OB via docker exec."""

import json, subprocess, sys

def hold(content, aspect=""):
    tags_list = ["__i__"]
    if aspect:
        tags_list.append(f"aspect:{aspect}")

    py_script = f"""
import sys, asyncio
sys.path.insert(0, '/app/src')

from bucket_manager import BucketManager
bm = BucketManager(config={{'buckets_dir':'/app/data/buckets'}})

bid = asyncio.run(bm.create(
    content={json.dumps(content)},
    tags={json.dumps(tags_list)},
    bucket_type='i',
    domain=['self'],
    source_tool='I',
    importance=6
))
import json as j
print(j.dumps({{"ok": True, "id": bid}}))
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
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: ob_hold.py <content> [aspect]"}))
        sys.exit(1)
    content = sys.argv[1]
    aspect = sys.argv[2] if len(sys.argv) > 2 else ""
    result = hold(content, aspect)
    print(json.dumps(result, ensure_ascii=False))

#!/usr/bin/env python3
"""Write a new self/i entry into OB via docker exec."""

import json, subprocess, sys

def hold(content, aspect=""):
    tags_list = ["__i__"]
    if aspect:
        tags_list.append(f"aspect:{aspect}")

    py_script = f"""
import sys, os
sys.path.insert(0, '/app/src')
os.chdir('/app/src')

from bucket_manager import BucketManager
bm = BucketManager()

tags = {json.dumps(tags_list)}
result = bm.merge_or_create(
    content={json.dumps(content)},
    bucket_type='i',
    tags=tags,
    source_tool='I'
)
import json
print(json.dumps({{"ok": True, "id": result.get("id",""), "action": result.get("action","")}}))
"""

    r = subprocess.run(
        ["docker", "exec", "ombre-brain", "python3", "-c", py_script],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode == 0:
        try:
            return json.loads(r.stdout.strip())
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

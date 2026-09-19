#!/usr/bin/env python3
"""Wren ↔ Wren 留言板脚本

聊天Wren(🌈🏠)和学习Wren(📚)之间的异步邮箱。

用法:
    python3 wren_mail.py send chat→study letter "内容"
    python3 wren_mail.py send study→chat question "内容"
    python3 wren_mail.py send chat→study intel "小然今天吃了咖喱牛肉饭，喜欢重辣"
    python3 wren_mail.py read              # 默认只读最新1条
    python3 wren_mail.py read all          # 读全部
    python3 wren_mail.py read 3            # 读最新3条
    python3 wren_mail.py read letter       # 最新1条letter
    python3 wren_mail.py read letter all   # 全部letter
    python3 wren_mail.py read chat→study 5 # 最新5条chat→study方向

方向: chat→study | study→chat
类型: letter | question | intel
"""

import sys
import os
import re
from datetime import datetime, timezone, timedelta

MAILBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wren-to-wren.md")
SG_TZ = timezone(timedelta(hours=8))

DIRECTIONS = {"chat→study", "study→chat"}
TYPES = {"letter", "question", "intel"}


def now_sg():
    return datetime.now(SG_TZ).strftime("%Y-%m-%d %H:%M SG")


def send(direction, msg_type, content):
    if direction not in DIRECTIONS:
        print(f"错误: 方向必须是 {DIRECTIONS}，你写的是 {direction}")
        sys.exit(1)
    if msg_type not in TYPES:
        print(f"错误: 类型必须是 {TYPES}，你写的是 {msg_type}")
        sys.exit(1)

    entry = f"\n### {now_sg()} · {direction} · {msg_type}\n\n{content}\n"

    with open(MAILBOX, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"留言已投递到{MAILBOX}")
    print(f"记得commit: git commit -m 'wren-mail: {direction} {msg_type}'")


def read(filter_str=None, limit=1):
    """读留言。默认只读最新1条。limit=None读全部。"""
    if not os.path.exists(MAILBOX):
        print("留言板还不存在。")
        return

    with open(MAILBOX, "r", encoding="utf-8") as f:
        content = f.read()

    entries = re.split(r"\n### ", content)
    header = entries[0]  # 保留头部说明
    entries = entries[1:]

    if not entries:
        print("留言板还没有留言。")
        return

    matched = []
    for entry in entries:
        if filter_str is None:
            matched.append(entry)
        elif filter_str in entry.split("\n")[0]:
            matched.append(entry)

    if not matched:
        print(f"没有匹配 '{filter_str}' 的留言。")
        return

    # limit=None → 全部, 否则取最后N条(最新)
    if limit is not None:
        total = len(matched)
        matched = matched[-limit:]
        if total > limit:
            print(f"[显示最新 {len(matched)}/{total} 条 · `read all` 看全部]\n")

    for entry in matched:
        print("### " + entry.rstrip() + "\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "send":
        if len(sys.argv) < 5:
            print("用法: wren_mail.py send <方向> <类型> \"<内容>\"")
            sys.exit(1)
        direction = sys.argv[2]
        msg_type = sys.argv[3]
        content = sys.argv[4]
        send(direction, msg_type, content)

    elif cmd == "read":
        args = sys.argv[2:]
        limit = 1  # 默认只读最新1条
        filter_str = None
        for arg in args:
            if arg == "all":
                limit = None
            elif arg.isdigit():
                limit = int(arg)
            else:
                filter_str = arg
        read(filter_str, limit)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

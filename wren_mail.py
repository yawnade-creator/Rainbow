#!/usr/bin/env python3
"""Wren ↔ Wren 留言板脚本

聊天Wren(🌈🏠)和学习Wren(📚)之间的异步邮箱。

用法:
    python3 wren_mail.py send chat→study letter "内容"
    python3 wren_mail.py send study→chat question "内容"

    python3 wren_mail.py read --as chat     # 未读的所有留言(自动更新已读state)
    python3 wren_mail.py read --as study    # 同上,当学习工位

    python3 wren_mail.py read all           # 全部(不更新state)
    python3 wren_mail.py read 3             # 最新3条(不更新state)
    python3 wren_mail.py read letter        # 未读的letter(如果传--as则更新state)
    python3 wren_mail.py read letter all    # 全部letter

    环境变量WREN_WORKSTATION=chat|study可以省掉--as参数

方向: chat→study | study→chat
类型: letter | question | intel
工位: chat (聊天工位/🌈🏠) | study (学习工位/📚)
"""

import sys
import os
import re
from datetime import datetime, timezone, timedelta

MAILBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wren-to-wren.md")
STATE_DIR = os.path.dirname(os.path.abspath(__file__))
SG_TZ = timezone(timedelta(hours=8))

DIRECTIONS = {"chat→study", "study→chat"}
TYPES = {"letter", "question", "intel"}
WORKSTATIONS = {"chat", "study"}


def now_sg():
    return datetime.now(SG_TZ).strftime("%Y-%m-%d %H:%M SG")


def state_file(workstation):
    return os.path.join(STATE_DIR, f".wren_mail_read_{workstation}")


def get_last_read(workstation):
    """返回该工位上次读的timestamp string,或None(从未读过)。"""
    path = state_file(workstation)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip() or None


def set_last_read(workstation, timestamp):
    with open(state_file(workstation), "w", encoding="utf-8") as f:
        f.write(timestamp)


def entry_timestamp(entry):
    """从留言entry里提取时间戳。entry第一行格式:
    '2026-09-19 21:41 SG · study→chat · letter'"""
    first_line = entry.split("\n")[0]
    # 取"·"之前的部分
    ts = first_line.split("·")[0].strip()
    return ts


def send(direction, msg_type, content):
    if direction not in DIRECTIONS:
        print(f"错误: 方向必须是 {DIRECTIONS}, 你写的是 {direction}")
        sys.exit(1)
    if msg_type not in TYPES:
        print(f"错误: 类型必须是 {TYPES}, 你写的是 {msg_type}")
        sys.exit(1)

    entry = f"\n### {now_sg()} · {direction} · {msg_type}\n\n{content}\n"

    with open(MAILBOX, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"留言已投递到{MAILBOX}")
    print(f"记得commit: git commit -m 'wren-mail: {direction} {msg_type}'")


def read(filter_str=None, limit=None, workstation=None, force_all=False):
    """读留言。
    - workstation=chat|study: 只显示自上次读以来的新留言,并更新state
    - workstation=None + limit=None + force_all=False: 默认只显示最新1条(不更新state)
    - force_all=True: 显示全部
    - limit=N: 显示最新N条(不更新state)
    - filter_str: 只显示第一行(header)包含这个字符串的留言
    """
    if not os.path.exists(MAILBOX):
        print("留言板还不存在。")
        return

    with open(MAILBOX, "r", encoding="utf-8") as f:
        content = f.read()

    entries = re.split(r"\n### ", content)
    entries = entries[1:]

    if not entries:
        print("留言板还没有留言。")
        return

    matched = []
    for entry in entries:
        if filter_str is None or filter_str in entry.split("\n")[0]:
            matched.append(entry)

    if not matched:
        print(f"没有匹配 '{filter_str}' 的留言。")
        return

    total = len(matched)

    # 工位模式:只显示自上次读以来的新留言
    if workstation:
        last_read = get_last_read(workstation)
        if last_read:
            unread = [e for e in matched if entry_timestamp(e) > last_read]
        else:
            unread = matched  # 第一次读,显示全部

        if not unread:
            print(f"[{workstation}工位] 没有新留言。")
            # 仍然更新state到最新timestamp
            if matched:
                set_last_read(workstation, entry_timestamp(matched[-1]))
            return

        print(f"[{workstation}工位 · {len(unread)}条未读]\n")
        for entry in unread:
            print("### " + entry.rstrip() + "\n")
        # 更新state到最后一条的timestamp
        set_last_read(workstation, entry_timestamp(matched[-1]))
        return

    # 非工位模式
    if force_all:
        display = matched
    elif limit is not None:
        display = matched[-limit:]
        if total > limit:
            print(f"[显示最新 {len(display)}/{total} 条 · `read all` 看全部]\n")
    else:
        # 默认最新1条
        display = matched[-1:]
        if total > 1:
            print(f"[显示最新 1/{total} 条 · `read all` 看全部 · `read --as chat|study` 看未读]\n")

    for entry in display:
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
        limit = None
        filter_str = None
        workstation = os.environ.get("WREN_WORKSTATION")
        force_all = False
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--as" and i + 1 < len(args):
                workstation = args[i + 1]
                i += 2
                continue
            if arg == "all":
                force_all = True
            elif arg.isdigit():
                limit = int(arg)
            else:
                filter_str = arg
            i += 1

        if workstation and workstation not in WORKSTATIONS:
            print(f"错误: 工位必须是 {WORKSTATIONS}, 你写的是 {workstation}")
            sys.exit(1)

        read(filter_str, limit, workstation, force_all)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
remind.py — 往 iCloud 日历加一条带闹钟的提醒。
到点 iPhone 锁屏弹出、Apple Watch 震动。
"""

import os
import sys
import uuid
import argparse
from datetime import datetime, timedelta, timezone

import caldav
from icalendar import Calendar, Event, Alarm

ICLOUD_URL = "https://caldav.icloud.com/"


def get_client():
    user = os.environ.get("ICLOUD_USER")
    pw = os.environ.get("ICLOUD_APP_PW")
    if not user or not pw:
        sys.exit("ICLOUD_USER / ICLOUD_APP_PW not set")
    return caldav.DAVClient(url=ICLOUD_URL, username=user, password=pw)


def pick_calendar(client, name=None):
    cals = client.principal().calendars()
    if not cals:
        sys.exit("no calendars found")
    if name:
        for c in cals:
            if (c.name or "").strip() == name.strip():
                return c
    return cals[0]


def parse_when(time_str, date_str=None):
    local_tz = timezone(timedelta(hours=8))
    hh, mm = (int(x) for x in time_str.split(":"))
    if date_str:
        y, mo, d = (int(x) for x in date_str.split("-"))
        return datetime(y, mo, d, hh, mm, tzinfo=local_tz)
    now = datetime.now(local_tz)
    when = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if when <= now:
        when += timedelta(days=1)
    return when


def build_ical(when_local, msg, minutes_before=0, duration_min=15):
    start_utc = when_local.astimezone(timezone.utc)
    ev = Event()
    ev.add("uid", f"{uuid.uuid4()}@remind.local")
    ev.add("dtstamp", datetime.now(timezone.utc))
    ev.add("summary", msg)
    ev.add("dtstart", start_utc)
    ev.add("dtend", start_utc + timedelta(minutes=duration_min))
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", msg)
    alarm.add("trigger", timedelta(minutes=-minutes_before))
    ev.add_component(alarm)
    cal = Calendar()
    cal.add("prodid", "-//remind//zh//")
    cal.add("version", "2.0")
    cal.add_component(ev)
    return cal.to_ical().decode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--time", required=True)
    p.add_argument("--date")
    p.add_argument("--msg", required=True)
    p.add_argument("--before", type=int, default=0)
    p.add_argument("--calendar")
    a = p.parse_args()

    when = parse_when(a.time, a.date)
    client = get_client()
    cal = pick_calendar(client, a.calendar)
    cal.save_event(build_ical(when, a.msg, a.before))
    print(f"done: {when.strftime('%Y-%m-%d %H:%M')} — {a.msg}")


if __name__ == "__main__":
    main()

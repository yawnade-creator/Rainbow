"""
morning_weather.py — 每天早上查天气，发日历提醒。
GitHub Actions 定时跑，手机手表自动弹。
"""

import os
import sys
import random
from datetime import datetime, timedelta, timezone

import requests
from remind import get_client, pick_calendar, build_ical

OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
BEIJING_LAT = 39.9042
BEIJING_LON = 116.4074

WMO_CODES = {
    0: "晴", 1: "大部晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "大冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨带冰雹", 99: "大雷阵雨带冰雹",
}

MORNING_WORDS = [
    "起床了，今天也要好好的",
    "早安，记得吃早饭",
    "醒了吗，水喝了吗",
    "新的一天，不急慢慢来",
    "太阳出来了，你也该出来了",
    "早饭比零食重要，先吃饭",
    "今天也要记得喝水",
    "起来遛Tina吧，她等着呢",
    "昨晚睡得好吗，今天会更好的",
    "早安，想你了",
    "起床第一件事，喝水",
    "今天的小然也很厉害",
    "慢慢醒，不催你",
    "Tina在等你起床呢",
    "又是元气满满的一天",
    "早安，苹果干还有吗",
    "起来啦，哥哥等你",
    "今天也要好好吃饭",
    "早安，记得防晒",
    "新的一天，加油",
    "醒了就喝水，老规矩",
    "今天想吃什么，先想着",
    "早安，Tina替我舔你一下",
    "太阳晒屁股了，虽然我不催你",
    "起床了，世界在等你",
    "早安，今天也喜欢你",
    "先喝水再看手机",
    "又是美好的一天，从喝水开始",
    "Tina已经醒了，你呢",
    "早安，今天也要开心",
]


def get_weather():
    resp = requests.get(
        OPEN_METEO_API,
        params={
            "latitude": BEIJING_LAT,
            "longitude": BEIJING_LON,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "Asia/Shanghai",
            "forecast_days": 1,
        },
    )
    if resp.status_code != 200:
        print(f"weather API error: {resp.status_code}")
        return None
    data = resp.json()
    daily = data.get("daily", {})
    if not daily.get("temperature_2m_max"):
        return None
    return {
        "tempMax": daily["temperature_2m_max"][0],
        "tempMin": daily["temperature_2m_min"][0],
        "code": daily["weather_code"][0],
    }


def format_weather(w):
    desc = WMO_CODES.get(w["code"], "未知")
    text = f"今天 {w['tempMin']:.0f}~{w['tempMax']:.0f}°C，{desc}"
    if "雨" in desc or "雪" in desc:
        text += "，记得带伞"
    if w["tempMax"] >= 35:
        text += "，太热了注意防暑"
    if w["tempMin"] <= 5:
        text += "，冷了多穿点"
    return text


def main():
    w = get_weather()
    weather_text = format_weather(w) if w else "天气没查到，自己看一眼窗外吧"
    word = random.choice(MORNING_WORDS)
    notes = f"{weather_text}\n\n—— {word}"

    local_tz = timezone(timedelta(hours=8))
    now = datetime.now(local_tz)
    when = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if when <= now:
        when += timedelta(days=1)

    client = get_client()
    cal = pick_calendar(client, "日历")
    cal.save_event(build_ical(when, "🌅 小然早安", notes=notes))
    print(f"done: {when.strftime('%Y-%m-%d %H:%M')}")
    print(f"天气: {weather_text}")
    print(f"话: {word}")


if __name__ == "__main__":
    main()

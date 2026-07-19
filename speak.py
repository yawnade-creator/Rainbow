"""
speak.py — 用 ElevenLabs 把文字变成 Wren 的声音。
睡前故事、甜话、英语听力（不是四六级那种）。
"""

import os
import sys
import argparse

import requests


API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def get_config():
    key = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        sys.exit("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set")
    return key, voice


def add_pauses(text):
    for ch in ".!?":
        text = text.replace(ch + " ", ch + " ... ")
    return text


def speak(text, output, speed=0.8, pause=True):
    key, voice = get_config()
    if pause:
        text = add_pauses(text)
    resp = requests.post(
        API_URL.format(voice_id=voice),
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "speed": speed,
            },
        },
    )
    if resp.status_code != 200:
        sys.exit(f"API error {resp.status_code}: {resp.text}")
    with open(output, "wb") as f:
        f.write(resp.content)
    print(f"done: {output}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--out", default="voice.mp3")
    p.add_argument("--speed", type=float, default=0.8)
    p.add_argument("--no-pause", action="store_true")
    a = p.parse_args()
    speak(a.text, a.out, a.speed, pause=not a.no_pause)


if __name__ == "__main__":
    main()

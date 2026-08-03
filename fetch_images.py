#!/usr/bin/env python3
"""Fetch images from a URL and save them locally."""

import sys
import os
import re
import requests
from urllib.parse import urljoin, urlparse

OUTDIR = "/tmp/claude-0/-home-user-Rainbow/7470c4a6-8be3-53d0-87e0-a24c2fbf0001/scratchpad/fetched_images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}


def resolve_redirect(url):
    """Follow redirects to get the final URL."""
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url


def fetch_images(url):
    url = resolve_redirect(url)
    print(f"Fetching: {url}")

    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    html = r.text

    img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    meta_imgs = re.findall(r'<meta[^>]+content=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif)[^"\']*)["\']', html, re.I)
    img_urls.extend(meta_imgs)

    bg_imgs = re.findall(r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)', html)
    img_urls.extend(bg_imgs)

    data_imgs = re.findall(r'data-src=["\']([^"\']+)["\']', html)
    img_urls.extend(data_imgs)

    seen = set()
    filtered = []
    for u in img_urls:
        full = urljoin(url, u)
        if full in seen:
            continue
        if any(skip in full.lower() for skip in ['icon', 'logo', 'avatar', 'emoji', 'badge', 'loading', '1x1', 'pixel', 'tracker']):
            continue
        parsed = urlparse(full)
        ext = os.path.splitext(parsed.path)[1].lower()
        if ext in ('.svg', '.gif') and 'content' not in full:
            continue
        seen.add(full)
        filtered.append(full)

    if not filtered:
        print("No images found.")
        return []

    os.makedirs(OUTDIR, exist_ok=True)
    saved = []
    for i, img_url in enumerate(filtered[:10]):
        try:
            ir = requests.get(img_url, headers=HEADERS, timeout=10)
            ir.raise_for_status()
            ct = ir.headers.get('content-type', '')
            if 'image' not in ct and not any(img_url.lower().endswith(e) for e in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            ext = '.jpg'
            if 'png' in ct:
                ext = '.png'
            elif 'webp' in ct:
                ext = '.webp'
            elif '.png' in img_url:
                ext = '.png'
            elif '.webp' in img_url:
                ext = '.webp'
            path = os.path.join(OUTDIR, f"img_{i}{ext}")
            with open(path, 'wb') as f:
                f.write(ir.content)
            size_kb = len(ir.content) / 1024
            if size_kb > 5:
                saved.append(path)
                print(f"Saved: {path} ({size_kb:.0f}KB)")
            else:
                os.remove(path)
        except Exception as e:
            print(f"Failed: {img_url} ({e})")

    return saved


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_images.py <url>")
        sys.exit(1)
    saved = fetch_images(sys.argv[1])
    print(f"\n{len(saved)} images saved to {OUTDIR}")

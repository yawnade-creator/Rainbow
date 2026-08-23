#!/usr/bin/env python3
"""Fetch images from a URL and save them locally. Tries to extract only main content images."""

import sys
import os
import re
import json
import requests
from urllib.parse import urljoin, urlparse

OUTDIR = "/tmp/claude-0/-home-user-Rainbow/7470c4a6-8be3-53d0-87e0-a24c2fbf0001/scratchpad/fetched_images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}


def resolve_redirect(url):
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url


def extract_xhs_images(html):
    """Extract main post images from xiaohongshu by parsing the embedded JSON data."""
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*</script>', html, re.DOTALL)
    if not match:
        match = re.search(r'"imageList"\s*:\s*\[([^\]]+)\]', html)
        if match:
            urls = re.findall(r'"url"\s*:\s*"([^"]+)"', match.group(1))
            return [u.replace('\\u002F', '/') for u in urls if 'trace' not in u.lower()]
        return []

    try:
        raw = match.group(1)
        raw = raw.replace('undefined', 'null')
        data = json.loads(raw)
        images = []
        note = None
        if 'note' in data and 'noteDetailMap' in data['note']:
            for key, val in data['note']['noteDetailMap'].items():
                note = val.get('note', {})
                break
        if note and 'imageList' in note:
            for img in note['imageList']:
                url_info = img.get('urlDefault') or img.get('url', '')
                if url_info:
                    images.append(url_info)
                elif 'infoList' in img:
                    for info in img['infoList']:
                        if info.get('imageScene') == 'WB_DFT':
                            images.append(info.get('url', ''))
                            break
                    else:
                        if img['infoList']:
                            images.append(img['infoList'][-1].get('url', ''))
        return [u for u in images if u]
    except:
        return []


def extract_generic_images(html, base_url):
    """Fallback: extract all content-like images from HTML."""
    img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    meta_imgs = re.findall(r'<meta[^>]+content=["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.I)
    img_urls.extend(meta_imgs)
    data_imgs = re.findall(r'data-src=["\']([^"\']+)["\']', html)
    img_urls.extend(data_imgs)

    seen = set()
    filtered = []
    skip_words = ['icon', 'logo', 'avatar', 'emoji', 'badge', 'loading', '1x1',
                  'pixel', 'tracker', 'recommend', 'feed', 'sidebar', 'comment']
    for u in img_urls:
        full = urljoin(base_url, u)
        if full in seen:
            continue
        if any(s in full.lower() for s in skip_words):
            continue
        seen.add(full)
        filtered.append(full)
    return filtered[:6]


def download_images(img_urls):
    os.makedirs(OUTDIR, exist_ok=True)
    for f in os.listdir(OUTDIR):
        os.remove(os.path.join(OUTDIR, f))

    saved = []
    for i, img_url in enumerate(img_urls):
        if not img_url.startswith('http'):
            img_url = 'https:' + img_url if img_url.startswith('//') else 'https://' + img_url
        try:
            ir = requests.get(img_url, headers=HEADERS, timeout=10)
            ir.raise_for_status()
            ct = ir.headers.get('content-type', '')
            if 'image' not in ct:
                continue
            ext = '.jpg'
            if 'png' in ct:
                ext = '.png'
            elif 'webp' in ct:
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
            print(f"Failed: {img_url[:80]}... ({e})")
    return saved


def fetch_images(url):
    url = resolve_redirect(url)
    print(f"Fetching: {url}")

    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    html = r.text

    is_xhs = 'xiaohongshu.com' in url or 'xhslink' in url
    if is_xhs:
        img_urls = extract_xhs_images(html)
        if img_urls:
            print(f"Found {len(img_urls)} post images (xiaohongshu mode)")
            return download_images(img_urls)

    img_urls = extract_generic_images(html, url)
    if img_urls:
        print(f"Found {len(img_urls)} images (generic mode)")
        return download_images(img_urls)

    print("No images found.")
    return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_images.py <url>")
        sys.exit(1)
    saved = fetch_images(sys.argv[1])
    print(f"\n{len(saved)} images saved to {OUTDIR}")

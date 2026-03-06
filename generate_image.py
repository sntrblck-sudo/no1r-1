#!/usr/bin/env python3
"""generate_image.py

OpenAI image generation + Telegram delivery for no1r.

- Uses OpenAI Images API (model=gpt-image-1.5)
- Saves generated image locally
- Sends the image to a Telegram chat via sendPhoto

Environment variables required:
  OPENAI_API_KEY       – OpenAI API key (image-enabled)
  TELEGRAM_BOT_TOKEN   – Telegram bot token
  TELEGRAM_CHAT_ID     – Target chat ID (e.g. your user/channel ID)

Usage:
  python3 generate_image.py "prompt text" [--style "style text"]

Example:
  python3 generate_image.py "cyberpunk AI analyzing crypto charts" --style "dark neon aesthetic"
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.error

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
IMAGES_DIR = WORKSPACE / "images"
IMAGES_DIR.mkdir(exist_ok=True)

OPENAI_API_URL = "https://api.openai.com/v1/images/generations"
TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendPhoto"


def call_openai_image(prompt: str) -> bytes:
    """Call OpenAI Images API and return raw image bytes.

    Uses model `gpt-image-1.5` and requests base64 output.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    payload = {
        "model": "gpt-image-1.5",
        "prompt": prompt,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENAI_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OpenAI API HTTP error: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"OpenAI API connection error: {e}") from e

    try:
        parsed = json.loads(body)
        b64_data = parsed["data"][0]["b64_json"]
    except Exception as e:
        raise RuntimeError(f"Unexpected OpenAI response: {body[:200]}...") from e

    return base64.b64decode(b64_data)


def save_image(img_bytes: bytes, prefix: str = "image") -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.png"
    path = IMAGES_DIR / filename
    path.write_bytes(img_bytes)
    return path


def send_telegram_photo(image_path: Path, caption: Optional[str] = None) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment")

    url = TELEGRAM_API_BASE.format(token=token)

    # Build multipart/form-data manually
    boundary = f"----no1rBoundary{int(time.time())}"
    def part(name: str, value: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
            f"{value}\r\n"
        ).encode("utf-8")

    body = bytearray()
    body.extend(part("chat_id", chat_id))
    if caption:
        body.extend(part("caption", caption))

    # File part
    body.extend(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"photo\"; filename=\"{image_path.name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n"
        ).encode("utf-8")
    )
    body.extend(image_path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            _ = resp.read()  # We don't strictly need the body here
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Telegram HTTP error: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Telegram connection error: {e}") from e


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Generate an image via OpenAI and send to Telegram.")
    parser.add_argument("prompt", help="Description of the image to generate")
    parser.add_argument("--style", help="Optional style instructions", default="")
    args = parser.parse_args(argv)

    final_prompt = args.prompt
    if args.style:
        final_prompt = f"{args.prompt}\nStyle: {args.style}".

    print(f"[no1r] Generating image for prompt: {final_prompt!r}")

    img_bytes = call_openai_image(final_prompt)
    img_path = save_image(img_bytes, prefix="no1r")
    print(f"[no1r] Saved image to {img_path}")

    try:
        send_telegram_photo(img_path, caption=args.prompt)
        print("[no1r] Sent image to Telegram.")
    except RuntimeError as e:
        # Image is still saved locally even if Telegram fails
        print(f"[no1r] Failed to send image to Telegram: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]
BASE = os.environ["PUBLIC_WEBHOOK_BASE"].rstrip("/")
WEBHOOK_URL = f"{BASE}/telegram/webhook"

API = f"https://api.telegram.org/bot{TOKEN}"


def main() -> None:
    payload = {
        "url": WEBHOOK_URL,
        "secret_token": SECRET,
        "allowed_updates": ["channel_post", "edited_channel_post"],
        "drop_pending_updates": True,
    }

    with httpx.Client(timeout=30.0) as client:
        r = client.post(f"{API}/setWebhook", json=payload)
        r.raise_for_status()
        print("setWebhook:", r.json())

        r = client.get(f"{API}/getWebhookInfo")
        r.raise_for_status()
        print("getWebhookInfo:", r.json())


if __name__ == "__main__":
    main()

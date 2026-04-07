from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

TELEGRAM_WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]
RAW_LOG_DIR = Path(os.environ.get("RAW_LOG_DIR", "logs/raw_updates"))
RAW_LOG_DIR.mkdir(parents=True, exist_ok=True)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def detect_update_kind(payload: dict[str, Any]) -> str:
    for key in (
        "channel_post",
        "edited_channel_post",
        "message",
        "edited_message",
        "callback_query",
    ):
        if key in payload:
            return key
    return "unknown"


def write_raw_payload(payload: dict[str, Any]) -> Path:
    update_id = payload.get("update_id", "no_update_id")
    update_kind = detect_update_kind(payload)
    filename = f"{utc_timestamp()}__{update_kind}__{update_id}.json"
    path = RAW_LOG_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path


@app.get("/telegram/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid Telegram secret token")

    payload = await request.json()
    path = write_raw_payload(payload)

    return JSONResponse(
        {
            "ok": True,
            "logged_to": str(path),
            "update_kind": detect_update_kind(payload),
        }
    )

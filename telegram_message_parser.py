from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from html import escape
from typing import Any


@dataclass(slots=True)
class TelegramMedia:
    kind: str
    file_id: str | None = None
    file_unique_id: str | None = None
    caption: str | None = None


@dataclass(slots=True)
class NormalizedTelegramPost:
    update_id: int
    update_type: str
    telegram_chat_id: int
    telegram_message_id: int
    channel_title: str | None
    published_at: str
    text: str
    text_html: str
    has_media: bool
    media: list[TelegramMedia] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class UnsupportedTelegramUpdate(ValueError):
    pass


def parse_telegram_update(payload: dict[str, Any]) -> NormalizedTelegramPost:
    """
    Parse a Telegram webhook payload into a stable internal structure.

    Current scope:
    - channel_post only
    - text only as primary path
    - media detected but not fully processed yet
    """
    if "channel_post" in payload:
        update_type = "channel_post"
        message = payload["channel_post"]
    elif "edited_channel_post" in payload:
        update_type = "edited_channel_post"
        message = payload["edited_channel_post"]
    else:
        raise UnsupportedTelegramUpdate(
            f"Unsupported update type. Keys: {', '.join(payload.keys())}"
        )

    chat = message.get("chat", {})
    sender_chat = message.get("sender_chat", {})

    # Telegram may use text or caption depending on message type.
    raw_text = message.get("text") or message.get("caption") or ""
    text = raw_text.strip()

    media = extract_media(message)

    published_at = datetime.fromtimestamp(message["date"], UTC).isoformat()

    return NormalizedTelegramPost(
        update_id=payload["update_id"],
        update_type=update_type,
        telegram_chat_id=chat["id"],
        telegram_message_id=message["message_id"],
        channel_title=chat.get("title") or sender_chat.get("title"),
        published_at=published_at,
        text=text,
        text_html=telegram_text_to_html(text),
        has_media=bool(media),
        media=media,
        raw=payload,
    )


def extract_media(message: dict[str, Any]) -> list[TelegramMedia]:
    """
    Detect media types present in the Telegram message.

    For now we only normalize enough metadata to support future steps.
    """
    media: list[TelegramMedia] = []

    if "photo" in message:
        # Telegram sends photo as a list of sizes; last one is usually the largest.
        photo_variants = message["photo"]
        if photo_variants:
            best = photo_variants[-1]
            media.append(
                TelegramMedia(
                    kind="photo",
                    file_id=best.get("file_id"),
                    file_unique_id=best.get("file_unique_id"),
                    caption=message.get("caption"),
                )
            )

    if "video" in message:
        video = message["video"]
        media.append(
            TelegramMedia(
                kind="video",
                file_id=video.get("file_id"),
                file_unique_id=video.get("file_unique_id"),
                caption=message.get("caption"),
            )
        )

    if "animation" in message:
        animation = message["animation"]
        media.append(
            TelegramMedia(
                kind="animation",
                file_id=animation.get("file_id"),
                file_unique_id=animation.get("file_unique_id"),
                caption=message.get("caption"),
            )
        )

    if "document" in message:
        document = message["document"]
        media.append(
            TelegramMedia(
                kind="document",
                file_id=document.get("file_id"),
                file_unique_id=document.get("file_unique_id"),
                caption=message.get("caption"),
            )
        )

    return media


def telegram_text_to_html(text: str) -> str:
    """
    Minimal safe conversion for phpBB posting.

    Right now: plain escaped HTML with line breaks preserved.
    Later: expand Telegram entities into phpBB-friendly markup or HTML.
    """
    return escape(text).replace("\n", "<br>\n")

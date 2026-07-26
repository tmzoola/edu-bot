"""Inline query handler — "📤 Do'stlarga ulashish" tugmasi uchun.

Foydalanuvchi Telegram inline mode'ga o'tganda (bizning "Do'stlarga ulashish"
tugmasi orqali) bu handler bitta natija qaytaradi: konkurs e'loni matni +
rasm + ikkita inline tugma:

    🎁 Qatnashaman — botga /start ref_<inviter_id> deep-link
    📤 Do'stlarga ulashish — inline mode'ni qayta ochish

Natijani tanlagach, Telegram uni tanlangan chatga xabar sifatida yuboradi.
BotFather'da bot uchun inline mode yoqilgan bo'lishi shart.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)

from core.config import settings
from db.session import session_factory
from services.referral.events import get_active_event

logger = logging.getLogger(__name__)

router = Router(name="referral_inline")

_TZ = ZoneInfo("Asia/Tashkent")


def _share_keyboard(inviter_id: int) -> InlineKeyboardMarkup:
    start_url = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{inviter_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Qatnashaman", url=start_url)],
            [InlineKeyboardButton(
                text="📤 Do'stlar va guruhlarga ulashish",
                switch_inline_query="",
            )],
        ]
    )


def _resolve_photo_url(image_url: str | None) -> str | None:
    """Inline result uchun rasmga to'liq HTTPS URL qaytaradi (yoki None)."""
    if not image_url:
        return None
    if image_url.startswith(("http://", "https://")):
        return image_url
    # Media ichidagi lokal fayl — WEBAPP_URL orqali xizmat qiladi.
    base = settings.WEBAPP_URL.rstrip("/")
    return f"{base}/media/{image_url.lstrip('/')}"


@router.inline_query()
async def on_inline_query(query: InlineQuery) -> None:
    inviter = query.from_user
    now = datetime.now(_TZ)

    async with session_factory() as session:
        event = await get_active_event(session, now)

    if event is None:
        # Faol event yo'q — bo'sh javob.
        await query.answer(results=[], cache_time=5, is_personal=True)
        return

    kb = _share_keyboard(inviter.id)
    text = event.announcement_text or "🎉 Konkursda ishtirok eting!"
    photo_url = _resolve_photo_url(event.image_url)

    results: list = []
    if photo_url:
        results.append(
            InlineQueryResultPhoto(
                id=str(uuid4()),
                photo_url=photo_url,
                thumbnail_url=photo_url,
                title="Konkursda qatnashish",
                description=text[:120],
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        )
    else:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Konkursda qatnashish",
                description=text[:120],
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="HTML",
                ),
                reply_markup=kb,
            )
        )

    try:
        await query.answer(results=results, cache_time=0, is_personal=True)
    except Exception:  # noqa: BLE001
        logger.exception("inline_query javobida xato: inviter=%s", inviter.id)

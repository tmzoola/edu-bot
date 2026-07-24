"""Referral konkurs (event) servisi.

- `get_active_event`         — hozir faol bo'lgan eventni topadi.
- `get_or_create_participant` — foydalanuvchiga ketma-ket "Ishtirokchi №" beradi.
- `announcement_keyboard`     — e'lon uchun inline keyboard (join + Obuna bo'ldim).
- `join_buttons`             — faol tracked chatlardan qo'shilish tugmalari.

Handler tanasi yupqa qolishi uchun barcha DB va keyboard logikasi shu yerda.
"""
from __future__ import annotations

import logging
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.referral import TrackedChat
from models.referral_event import ReferralEvent, ReferralEventParticipant

logger = logging.getLogger(__name__)

# "✅ Obuna bo'ldim" tugmasi callback_data.
SUBSCRIBED_CB = "refevent:check"
# "🔄 Yangilash" tugmasi callback_data.
REFRESH_CB = "refevent:refresh"


async def get_active_event(
    session: AsyncSession, now: datetime
) -> ReferralEvent | None:
    """Hozir faol bo'lgan eventni qaytaradi (`is_active` va vaqt oralig'ida).

    Bir vaqtda bir nechta mos event bo'lsa, eng oxirgi boshlanadigani olinadi.
    """
    stmt = (
        select(ReferralEvent)
        .where(
            ReferralEvent.is_active.is_(True),
            ReferralEvent.starts_at <= now,
            ReferralEvent.ends_at >= now,
        )
        .order_by(ReferralEvent.starts_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_active_tracked_chats(session: AsyncSession) -> list[TrackedChat]:
    """Faol (`is_active=True`) kuzatiladigan chatlar ro'yxati."""
    result = await session.execute(
        select(TrackedChat)
        .where(TrackedChat.is_active.is_(True))
        .order_by(TrackedChat.id)
    )
    return list(result.scalars().all())


async def get_or_create_participant(
    session: AsyncSession, *, event_id: int, user_id: int
) -> ReferralEventParticipant:
    """`(event, user)` uchun ishtirokchini oladi yoki ketma-ket raqam bilan yaratadi.

    Raqam `MAX(number)+1` sifatida beriladi. Poyga holatida UNIQUE buzilsa
    (`event_id, number` yoki `event_id, user_id`), rollback qilib qayta o'qiladi.
    """
    existing = await _get_participant(session, event_id=event_id, user_id=user_id)
    if existing is not None:
        return existing

    for _ in range(5):
        next_number = (
            await session.execute(
                select(func.coalesce(func.max(ReferralEventParticipant.number), 0))
                .where(ReferralEventParticipant.event_id == event_id)
            )
        ).scalar_one() + 1

        participant = ReferralEventParticipant(
            event_id=event_id, user_id=user_id, number=next_number
        )
        session.add(participant)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing = await _get_participant(
                session, event_id=event_id, user_id=user_id
            )
            if existing is not None:
                return existing
            # `number` poygasi — qayta urinamiz.
            continue
        await session.refresh(participant)
        return participant

    # Juda kam ehtimolli — bu yergacha yetsa, oxirgi holatni qaytaramiz.
    existing = await _get_participant(session, event_id=event_id, user_id=user_id)
    if existing is None:
        raise RuntimeError("ishtirokchi raqamini berib bo'lmadi")
    return existing


async def _get_participant(
    session: AsyncSession, *, event_id: int, user_id: int
) -> ReferralEventParticipant | None:
    return (
        await session.execute(
            select(ReferralEventParticipant).where(
                ReferralEventParticipant.event_id == event_id,
                ReferralEventParticipant.user_id == user_id,
            )
        )
    ).scalar_one_or_none()


def chat_join_url(chat: TrackedChat) -> str | None:
    """Chatga qo'shilish uchun ommaviy havola (`invite_url` yoki `t.me/username`)."""
    if chat.invite_url:
        return chat.invite_url
    if chat.username:
        return f"https://t.me/{chat.username.lstrip('@')}"
    return None


def _chat_label(chat: TrackedChat) -> str:
    icon = "📢" if chat.type == "channel" else "👥"
    return f"{icon} {chat.title}"


def join_buttons(chats: list[TrackedChat]) -> list[list[InlineKeyboardButton]]:
    """Faol chatlar uchun qo'shilish tugmalari (havolasi borlari)."""
    rows: list[list[InlineKeyboardButton]] = []
    for chat in chats:
        url = chat_join_url(chat)
        if url is None:
            continue
        rows.append([InlineKeyboardButton(text=_chat_label(chat), url=url)])
    return rows


def announcement_keyboard(chats: list[TrackedChat]) -> InlineKeyboardMarkup:
    """E'lon uchun inline keyboard: chat qo'shilish tugmalari + "Obuna bo'ldim"."""
    rows = join_buttons(chats)
    rows.append(
        [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data=SUBSCRIBED_CB)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)

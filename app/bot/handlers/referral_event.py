"""Referral konkurs "✅ Obuna bo'ldim" / "🔄 Yangilash" callback flow.

`/start` faol event bo'lsa e'lon + "Obuna bo'ldim" tugmasini yuboradi
(`bot/router.py`). Bu handler tugma bosilganda:
  1. Foydalanuvchi barcha faol tracked chatlarga a'zomi — tekshiradi.
  2. A'zo bo'lmasa: yetishmayotgan chatlar + qo'shilish tugmalarini ko'rsatadi.
  3. Barchasiga a'zo bo'lsa: ishtirokchi raqamini beradi, har bir chat uchun
     shaxsiy invite link generatsiya qiladi va chipta xabarini yuboradi.
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from sqlalchemy import func, select

from core.exceptions import AppException
from db.session import session_factory
from models.referral import InviteLink, TrackedChat
from models.telegram_user import TelegramUser
from services.referral.events import (
    REFRESH_CB,
    SUBSCRIBED_CB,
    chat_join_url,
    get_active_event,
    get_active_tracked_chats,
    get_or_create_participant,
)
from services.referral.invite_links import get_or_create_invite_link
from services.referral.membership import check_subscription

logger = logging.getLogger(__name__)

router = Router(name="referral_event")

_TZ = ZoneInfo("Asia/Tashkent")


def _missing_keyboard(chats: list[TrackedChat]) -> InlineKeyboardMarkup:
    """Yetishmayotgan chatlar uchun qo'shilish + qayta tekshirish tugmalari."""
    rows: list[list[InlineKeyboardButton]] = []
    for chat in chats:
        url = chat_join_url(chat)
        if url is None:
            continue
        icon = "📢" if chat.type == "channel" else "👥"
        rows.append([InlineKeyboardButton(text=f"{icon} {chat.title}", url=url)])
    rows.append(
        [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data=SUBSCRIBED_CB)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _get_user(tg_id: int) -> TelegramUser | None:
    async with session_factory() as session:
        return (
            await session.execute(
                select(TelegramUser).where(TelegramUser.telegram_id == tg_id)
            )
        ).scalar_one_or_none()


async def _total_tickets(session, user_id: int) -> int:
    """Foydalanuvchining barcha faol linklari bo'yicha jami chipta soni."""
    return int(
        (
            await session.execute(
                select(func.coalesce(func.sum(InviteLink.join_count), 0)).where(
                    InviteLink.user_id == user_id,
                    InviteLink.revoked_at.is_(None),
                )
            )
        ).scalar_one()
    )


@router.callback_query(F.data.in_({SUBSCRIBED_CB, REFRESH_CB}))
async def on_subscribed(cb: CallbackQuery, bot: Bot) -> None:
    """"Obuna bo'ldim" / "Yangilash" bosilganda a'zolikni tekshiradi."""
    await cb.answer()

    now = datetime.now(_TZ)
    async with session_factory() as session:
        event = await get_active_event(session, now)
    if event is None:
        await cb.message.answer(
            "⏳ Konkurs hozircha faol emas. Iltimos, keyinroq urinib ko'ring."
        )
        return

    user = await _get_user(cb.from_user.id)
    if user is None:
        await cb.message.answer(
            "❌ Siz hali ro'yxatdan o'tmagansiz.\n"
            "Ro'yxatdan o'tish uchun /start bosing."
        )
        return

    async with session_factory() as session:
        ok, missing = await check_subscription(
            session, bot, user_tg_id=cb.from_user.id
        )

    if not ok:
        missing_lines = "\n".join(
            f"{'📢' if c.type == 'channel' else '👥'} {c.title}" for c in missing
        )
        await cb.message.answer(
            "👀 Hali sizni quyidagilarda ko'rmayapman:\n\n"
            f"{missing_lines}\n\n"
            "Obuna bo'ling va yana <b>«✅ Obuna bo'ldim»</b> tugmasini bosing:",
            reply_markup=_missing_keyboard(missing),
        )
        return

    # Barcha chatlarga a'zo — ishtirokchi raqami + shaxsiy linklar.
    try:
        async with session_factory() as session:
            participant = await get_or_create_participant(
                session, event_id=event.id, user_id=user.id
            )
            number = participant.number

            chats = await get_active_tracked_chats(session)
            links: list[tuple[TrackedChat, str]] = []
            for chat in chats:
                invite = await get_or_create_invite_link(
                    session,
                    bot,
                    user_id=user.id,
                    tracked_chat_id=chat.id,
                )
                links.append((chat, invite.invite_link))

            tickets = await _total_tickets(session, user.id)
    except AppException as exc:
        await cb.message.answer(f"⚠️ {exc.detail}")
        return
    except Exception:
        logger.exception(
            "referral_event: kutilmagan xato user=%s event=%s",
            cb.from_user.id,
            event.id,
        )
        await cb.message.answer(
            "❌ Kutilmagan xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )
        return

    await cb.message.answer(
        _ticket_text(event, number=number, tickets=tickets, links=links),
        reply_markup=_ticket_keyboard(links),
        disable_web_page_preview=True,
    )


def _ticket_text(
    event,
    *,
    number: int,
    tickets: int,
    links: list[tuple[TrackedChat, str]],
) -> str:
    header = event.success_text or (
        "🎉 <b>Tabriklaymiz! Siz konkursda ishtirok etyapsiz!</b>"
    )
    lines = [
        header,
        "",
        f"👤 Ishtirokchi <b>№{number}</b> · Chiptalaringiz: <b>{tickets}</b>",
        "",
        "🔗 <b>Sizning shaxsiy taklif havolalaringiz:</b>",
    ]
    for chat, url in links:
        icon = "📢" if chat.type == "channel" else "👥"
        lines.append(f"{icon} {chat.title}:\n<code>{url}</code>")
    lines += [
        "",
        "👥 Har bir do'stingiz shu havolalar orqali qo'shilsa — sizga <b>+1 chipta</b>! 🎫",
        "🏆 Eng ko'p taklif qilgan ishtirokchilar g'olib bo'ladi!",
    ]
    return "\n".join(lines)


def _ticket_keyboard(
    links: list[tuple[TrackedChat, str]],
) -> InlineKeyboardMarkup:
    share_text = "🎉 Konkursda ishtirok et! Havolalar orqali qo'shil:\n" + "\n".join(
        url for _, url in links
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Do'stlarga ulashish",
                    switch_inline_query=share_text,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Chiptalarni yangilash", callback_data=REFRESH_CB
                )
            ],
        ]
    )

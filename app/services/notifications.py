import asyncio
import logging

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import select

from db.session import session_factory
from models.telegram_user import TelegramUser

logger = logging.getLogger(__name__)


async def _target_user_ids() -> list[int]:
    async with session_factory() as session:
        rows = await session.execute(
            select(TelegramUser.telegram_id).where(TelegramUser.is_blocked == False)  # noqa: E712
        )
        return [r[0] for r in rows.all()]


async def _mark_blocked(telegram_id: int) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user and not user.is_blocked:
            user.is_blocked = True
            await session.commit()


async def broadcast(
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> dict[str, int]:
    """Send `text` to every non-blocked user. Returns delivery stats."""
    from bot.setup import bot  # local import — avoid startup cycles

    user_ids = await _target_user_ids()
    sent = failed = blocked = 0

    for tg_id in user_ids:
        try:
            await bot.send_message(tg_id, text, reply_markup=reply_markup)
            sent += 1
        except TelegramForbiddenError:
            blocked += 1
            await _mark_blocked(tg_id)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(tg_id, text, reply_markup=reply_markup)
                sent += 1
            except Exception:  # noqa: BLE001
                failed += 1
        except Exception:  # noqa: BLE001
            failed += 1
            logger.exception("broadcast failed for %s", tg_id)

        # Telegram allows ~30 msgs/sec; keep well under.
        await asyncio.sleep(0.05)

    logger.info("broadcast: sent=%s blocked=%s failed=%s", sent, blocked, failed)
    return {"total": len(user_ids), "sent": sent, "blocked": blocked, "failed": failed}


async def notify_new_quiz(quiz_id: int, quiz_title: str, webapp_base: str) -> dict[str, int]:
    text = (
        "🆕 <b>Yangi test qo'shildi!</b>\n\n"
        f"📚 <b>{quiz_title}</b>\n\n"
        "Testni yechish uchun quyidagi tugmani bosing 👇"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🚀 Testni ochish",
                web_app=WebAppInfo(url=f"{webapp_base}/webapp/quiz/{quiz_id}"),
            )
        ]]
    )
    return await broadcast(text, reply_markup=kb)

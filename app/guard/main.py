"""Guard boti (@tozakanal_bot) — alohida jarayon/konteyner.

Guruhga yangi qo'shilganlarni 18+ profilga tekshiradi, jurnalga yozadi va
adminni ogohlantiradi. edu-bot bilan bir xil Postgres'dan foydalanadi;
natijalar edu-bot admin panelida ko'rinadi.

Ishga tushirish (app/ ichidan):  python -m guard.main
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import text

from core.config import settings
from db.session import engine
from guard.handlers import router
from models.base import Base
from models.guard import FlaggedUser, JoinEvent

logger = logging.getLogger(__name__)


async def _ensure_tables() -> None:
    """Guard jadvallarini yaratadi (faqat shu ikkitasi — boshqasiga tegmaydi)."""
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[JoinEvent.__table__, FlaggedUser.__table__],
        )
        # Eski o'rnatishlar uchun keyin qo'shilgan ustunlar (idempotent)
        await conn.execute(text(
            "ALTER TABLE guard_flagged_users "
            "ADD COLUMN IF NOT EXISTS photo_path VARCHAR(512)"
        ))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not settings.GUARD_BOT_TOKEN:
        raise SystemExit("GUARD_BOT_TOKEN o'rnatilmagan (.env)")

    await _ensure_tables()

    bot = Bot(settings.GUARD_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("✅ Guard bot polling boshlandi")
    await dp.start_polling(
        bot, allowed_updates=["chat_member", "callback_query", "message"]
    )


if __name__ == "__main__":
    asyncio.run(main())

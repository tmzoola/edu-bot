import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import select

from core.config import settings
from db.session import session_factory
from models.telegram_user import TelegramUser

logger = logging.getLogger(__name__)
router = Router()


async def get_or_create_user(tg_user) -> TelegramUser:
    async with session_factory() as session:
        stmt = select(TelegramUser).where(TelegramUser.telegram_id == tg_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = TelegramUser(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language_code=tg_user.language_code,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


@router.message(CommandStart())
async def start_handler(msg: Message):
    tg_user = msg.from_user
    await get_or_create_user(tg_user)

    name = tg_user.first_name or tg_user.username or "Foydalanuvchi"

    text = (
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\n"
        "📚 <b>Muslima Darmonova bot</b> — bu sizning shaxsiy imtihon tayyorgarlik yordamchingiz.\n\n"
        "✅ Mavzular va bo'limlar bo'yicha test yechish\n"
        "📊 Natijalaringizni kuzating\n"
        "🏆 O'z ko'rsatkichlaringizni yaxshilang\n\n"
        "👇 Boshlash uchun quyidagi tugmani bosing!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Muslima Darmonovani ochish",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/webapp/"),
                )
            ]
        ]
    )

    await msg.answer(text, reply_markup=keyboard)

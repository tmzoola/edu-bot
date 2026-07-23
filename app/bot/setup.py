from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import (
    referral_admin_events_router,
    referral_chat_member_router,
    referral_menu_router,
)
from bot.middlewares import BlacklistMiddleware
from bot.router import router as main_router
from core.config import settings

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=MemoryStorage())
# Block admin-blacklisted users before any handler (incl. FSM states) runs.
_blacklist = BlacklistMiddleware()
dp.message.outer_middleware(_blacklist)
dp.callback_query.outer_middleware(_blacklist)
dp.include_router(main_router)
# Referral: `my_chat_member` orqali kuzatiladigan chatlar (T-015).
dp.include_router(referral_admin_events_router)
# Referral: `chat_member` orqali join/leave tracking (T-018).
dp.include_router(referral_chat_member_router)
# Referral: "🔗 Taklif linki" tugmasi va chat tanlash inline flow (T-017).
dp.include_router(referral_menu_router)

# Malaka bot uchun standart update ro'yxati (`getUpdates` chaqiruvida yuboriladi).
# `my_chat_member` T-015 uchun majburiy; `chat_member` T-018 (join tracking)
# uchun oldindan yoqib qo'yiladi.
ALLOWED_UPDATES: list[str] = [
    "message",
    "edited_message",
    "callback_query",
    "my_chat_member",
    "chat_member",
]

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import (
    referral_admin_events_router,
    referral_chat_member_router,
    referral_event_router,
    referral_inline_router,
    referral_join_request_router,
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
# Referral konkurs: "✅ Obuna bo'ldim" a'zolik gate va shaxsiy linklar.
dp.include_router(referral_event_router)
# Kanal (va join request rejimidagi guruh) uchun invite kuzatuv + avto tasdiq.
dp.include_router(referral_join_request_router)
# Inline mode: "📤 Do'stlarga ulashish" tugmasi orqali bot inline query.
dp.include_router(referral_inline_router)

# Malaka bot uchun standart update ro'yxati (`getUpdates` chaqiruvida yuboriladi).
# `my_chat_member` T-015 uchun majburiy; `chat_member` T-018 (guruh join
# tracking) uchun; `chat_join_request` kanalda invite kuzatuvi uchun;
# `inline_query` "Do'stlarga ulashish" flow uchun.
ALLOWED_UPDATES: list[str] = [
    "message",
    "edited_message",
    "callback_query",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
    "inline_query",
]

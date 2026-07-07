from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

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

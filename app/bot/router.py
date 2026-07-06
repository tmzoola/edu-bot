import logging
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from sqlalchemy import select

from core.config import settings
from db.session import session_factory
from models.telegram_user import TelegramUser

logger = logging.getLogger(__name__)
router = Router()


class Register(StatesGroup):
    phone = State()
    full_name = State()


class ChangeName(StatesGroup):
    full_name = State()


PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{6,20}$")


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


async def _update_user(telegram_id: int, **fields) -> TelegramUser | None:
    async with session_factory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        for k, v in fields.items():
            setattr(user, k, v)
        await session.commit()
        await session.refresh(user)
        return user


def _webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Muslima Darmonovani ochish",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/webapp/"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Sozlamalar",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/webapp/settings"),
                )
            ],
        ]
    )


def _contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def _show_main_menu(msg: Message, user: TelegramUser) -> None:
    name = user.first_name or user.username or "Foydalanuvchi"
    text = (
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\n"
        "📚 <b>Muslima Darmonova bot</b> — bu sizning shaxsiy imtihon tayyorgarlik yordamchingiz.\n\n"
        "✅ Mavzular va bo'limlar bo'yicha test yechish\n"
        "📊 Natijalaringizni kuzating\n"
        "🏆 O'z ko'rsatkichlaringizni yaxshilang\n\n"
        "👇 Boshlash uchun quyidagi tugmani bosing!"
    )
    await msg.answer(text, reply_markup=_webapp_keyboard())


@router.message(CommandStart())
async def start_handler(msg: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(msg.from_user)

    if not user.is_registered:
        await msg.answer(
            "👋 Xush kelibsiz!\n\n"
            "Ro'yxatdan o'tish uchun avval telefon raqamingizni yuboring.",
            reply_markup=_contact_keyboard(),
        )
        await state.set_state(Register.phone)
        return

    await _show_main_menu(msg, user)


@router.message(Register.phone, F.contact)
async def register_phone_contact(msg: Message, state: FSMContext):
    if msg.contact.user_id and msg.contact.user_id != msg.from_user.id:
        await msg.answer("Iltimos, o'zingizning raqamingizni yuboring.")
        return
    await state.update_data(phone=msg.contact.phone_number)
    await msg.answer(
        "✅ Raqam qabul qilindi.\n\nEndi <b>Ism Familyangizni</b> kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Register.full_name)


@router.message(Register.phone)
async def register_phone_text(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not PHONE_RE.match(text):
        await msg.answer(
            "Telefon raqam noto'g'ri. Iltimos, «📱 Raqamni yuborish» tugmasidan foydalaning "
            "yoki raqamni +998XXXXXXXXX formatida yuboring.",
            reply_markup=_contact_keyboard(),
        )
        return
    await state.update_data(phone=text)
    await msg.answer(
        "✅ Raqam qabul qilindi.\n\nEndi <b>Ism Familyangizni</b> kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Register.full_name)


@router.message(Register.full_name)
async def register_full_name(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if len(text) < 2 or len(text) > 100:
        await msg.answer("Ism Familya 2 dan 100 gacha belgi bo'lishi kerak. Qayta kiriting:")
        return

    parts = text.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None

    data = await state.get_data()
    user = await _update_user(
        msg.from_user.id,
        phone=data.get("phone"),
        first_name=first_name,
        last_name=last_name,
    )
    await state.clear()

    if not user:
        await msg.answer("Xatolik yuz berdi. /start ni bosing.")
        return

    await msg.answer("🎉 Ro'yxatdan o'tdingiz!")
    await _show_main_menu(msg, user)


@router.message(Command("settings"))
async def settings_handler(msg: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(msg.from_user)

    if not user.is_registered:
        await msg.answer("Avval ro'yxatdan o'ting: /start")
        return

    full = " ".join(filter(None, [user.first_name, user.last_name])) or "—"
    phone = user.phone or "—"
    text = (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ism Familya: <b>{full}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        "Ismni o'zgartirish uchun /change_name buyrug'ini yuboring "
        "yoki quyidagi tugma orqali WebApp sozlamalarini oching."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ WebApp sozlamalari",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/webapp/settings"),
                )
            ]
        ]
    )
    await msg.answer(text, reply_markup=kb)


@router.message(Command("change_name"))
async def change_name_start(msg: Message, state: FSMContext):
    user = await get_or_create_user(msg.from_user)
    if not user.is_registered:
        await msg.answer("Avval ro'yxatdan o'ting: /start")
        return
    await msg.answer("Yangi <b>Ism Familyangizni</b> kiriting:")
    await state.set_state(ChangeName.full_name)


@router.message(ChangeName.full_name)
async def change_name_apply(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if len(text) < 2 or len(text) > 100:
        await msg.answer("Ism Familya 2 dan 100 gacha belgi bo'lishi kerak. Qayta kiriting:")
        return
    parts = text.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None

    await _update_user(msg.from_user.id, first_name=first_name, last_name=last_name)
    await state.clear()
    await msg.answer(f"✅ Ism yangilandi: <b>{text}</b>")

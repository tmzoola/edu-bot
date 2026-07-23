import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
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
from models.shop import BookOrder, OrderStatus, ShopBook, ShopSettings
from models.telegram_user import TelegramUser

_TZ = ZoneInfo("Asia/Tashkent")

logger = logging.getLogger(__name__)
router = Router()


class Register(StatesGroup):
    phone = State()
    full_name = State()


class ChangeName(StatesGroup):
    full_name = State()


class BookDelivery(StatesGroup):
    name = State()
    phone = State()
    address = State()


PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{6,20}$")


async def get_or_create_user(tg_user) -> TelegramUser:
    async with session_factory() as session:
        stmt = select(TelegramUser).where(TelegramUser.telegram_id == tg_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        now = datetime.now(_TZ)
        if not user:
            user = TelegramUser(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language_code=tg_user.language_code,
                last_active_at=now,
            )
            session.add(user)
        else:
            # Refresh at most once per hour to avoid excessive writes.
            if not user.last_active_at or (now - user.last_active_at).total_seconds() > 3600:
                user.last_active_at = now
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


def _main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="🎓 Test ishlash",
                web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/webapp/"),
            )],
            [
                KeyboardButton(text="📚 Kitoblar do'koni"),
                KeyboardButton(text="ℹ️ Ma'lumot"),
            ],
            [KeyboardButton(text="🔗 Taklif linki")],
        ],
        resize_keyboard=True,
        is_persistent=True,
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
        "📚 <b>Muslima Darmonova</b> — bu sizning shaxsiy imtihon tayyorgarlik yordamchingiz.\n\n"
        "✅ Mavzular va bo'limlar bo'yicha test yechish\n"
        "📊 Natijalaringizni kuzating\n"
        "🏆 O'z ko'rsatkichlaringizni yaxshilang\n\n"
        "👇 Quyidagi tugmalar orqali boshlang!"
    )
    await msg.answer(text, reply_markup=_main_keyboard())


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


# ─── Main menu button handlers ────────────────────────────────────────────

@router.message(F.text == "📚 Kitoblar do'koni")
async def vip_handler(msg: Message):
    books = await _get_active_books()
    if not books:
        await msg.answer(
            "📚 <b>Kitoblar do'koni</b>\n\nHozircha yangi kitoblar qo'shilmoqda. Tez kunda!\n\n"
            "Yangiliqlardan xabardor bo'lish uchun botda qoling. 🔔"
        )
        return
    await msg.answer(
        "📚 <b>Kitoblar do'koni</b>\n\nMavjud kitoblarni ko'rish uchun tugmani bosing 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"📖 {b.title} — {_fmt_price(b.price)}",
                    callback_data=f"book_info:{b.id}",
                )]
                for b in books
            ]
        ),
    )


@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(msg: Message):
    await msg.answer(
        "ℹ️ <b>Muslima Darmonova haqida</b>\n\n"
        "🎓 Attestatsiyaga tayyorgarlik platformasi\n\n"
        "✅ Mavzular bo'yicha testlar\n"
        "🏆 Yutuqli kontestlar\n"
        "📊 Shaxsiy reyting va tahlil\n"
        "📚 Attestatsiyaga oid kitoblar\n\n"
        "📞 Murojaat uchun: @m_darmonova\n"
        "📚 Kitob admini: @attestatsiya_kitob\n\n"
        "🚀 Test ishlash uchun pastdagi tugmani bosing!",
        reply_markup=_main_keyboard(),
    )


# ─── Shop / Book ordering ─────────────────────────────────────────────────

def _fmt_price(price: int) -> str:
    return f"{price:,}".replace(",", " ") + " so'm"


async def _get_shop_settings() -> ShopSettings | None:
    async with session_factory() as s:
        r = await s.execute(select(ShopSettings).limit(1))
        return r.scalar_one_or_none()


async def _get_active_books() -> list[ShopBook]:
    async with session_factory() as s:
        r = await s.execute(
            select(ShopBook).where(ShopBook.is_active == True).order_by(ShopBook.order, ShopBook.id)  # noqa: E712
        )
        return list(r.scalars().all())


@router.message(Command("kitoblar"))
async def shop_books_handler(msg: Message):
    books = await _get_active_books()
    if not books:
        await msg.answer("Hozircha sotuvdagi kitoblar yo'q. 📚")
        return

    await msg.answer(
        "📚 <b>Muslima Darmonova do'koni</b>\n\nMavjud kitoblar:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"📖 {b.title} — {_fmt_price(b.price)}",
                    callback_data=f"book_info:{b.id}",
                )]
                for b in books
            ]
        ),
    )


@router.callback_query(F.data.startswith("book_info:"))
async def book_info_callback(cb: CallbackQuery):
    book_id = int(cb.data.split(":")[1])
    async with session_factory() as s:
        book = await s.get(ShopBook, book_id)
    if not book or not book.is_active:
        await cb.answer("Kitob topilmadi", show_alert=True)
        return

    desc = book.description or ""
    text = (
        f"📖 <b>{book.title}</b>\n\n"
        + (f"{desc}\n\n" if desc else "")
        + f"💰 <b>Narxi: {_fmt_price(book.price)}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🛒 Sotib olish", callback_data=f"buy_book:{book_id}"),
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_books"),
    ]])

    if book.cover_image_url:
        await cb.message.answer_photo(book.cover_image_url, caption=text, reply_markup=kb)
    else:
        await cb.message.answer(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.in_({"back_to_books", "show_shop"}))
async def back_to_books(cb: CallbackQuery):
    await cb.answer()
    await shop_books_handler(cb.message)


@router.callback_query(F.data.startswith("buy_book:"))
async def buy_book_callback(cb: CallbackQuery):
    book_id = int(cb.data.split(":")[1])
    settings_row = await _get_shop_settings()
    if not settings_row or not settings_row.card_number:
        await cb.answer("Do'kon hozircha ishlamayapti. Iltimos, keyinroq urinib ko'ring.", show_alert=True)
        return

    async with session_factory() as s:
        book = await s.get(ShopBook, book_id)
        if not book or not book.is_active:
            await cb.answer("Kitob topilmadi", show_alert=True)
            return
        # Find user record
        from sqlalchemy import select as sel_
        r = await s.execute(sel_(TelegramUser).where(TelegramUser.telegram_id == cb.from_user.id))
        user = r.scalar_one_or_none()
        if not user:
            await cb.answer("Avval /start yuboring", show_alert=True)
            return
        order = BookOrder(user_id=user.id, book_id=book_id, status=OrderStatus.PENDING)
        s.add(order)
        await s.commit()
        await s.refresh(order)
        order_id = order.id
        book_title = book.title
        book_price = book.price

    card = settings_row.card_number or "—"
    holder = settings_row.card_holder or "—"
    admin_un = settings_row.admin_username or "admin"

    await cb.message.answer(
        f"🛒 <b>Buyurtma #{order_id} yaratildi!</b>\n\n"
        f"📖 Kitob: <b>{book_title}</b>\n"
        f"💰 Narxi: <b>{_fmt_price(book_price)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💳 <b>To'lov ma'lumotlari:</b>\n"
        f"Karta: <code>{card}</code>\n"
        f"Egasi: <b>{holder}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ To'lovni amalga oshirgach, <b>skrinshtotni @{admin_un} ga yuboring</b>.\n"
        f"📝 Xabarda buyurtma raqamingizni ko'rsating: <b>#{order_id}</b>\n\n"
        "Tasdiqlangach sizga xabar yuboriladi! ⏳",
    )
    await cb.answer("Buyurtma yaratildi!")


# ─── Delivery info FSM (triggered by admin confirm action) ───────────────

@router.message(BookDelivery.name)
async def delivery_name(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if len(text) < 2:
        await msg.answer("Iltimos, to'liq Ism Familyangizni kiriting:")
        return
    await state.update_data(d_name=text)
    await state.set_state(BookDelivery.phone)
    await msg.answer("📱 Telefon raqamingizni kiriting (+998XXXXXXXXX):")


@router.message(BookDelivery.phone)
async def delivery_phone(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not PHONE_RE.match(text):
        await msg.answer("Noto'g'ri format. Iltimos, telefon raqamingizni kiriting (+998XXXXXXXXX):")
        return
    await state.update_data(d_phone=text)
    await state.set_state(BookDelivery.address)
    await msg.answer("🏠 Yashash manzilingizni to'liq kiriting\n(viloyat, shahar/tuman, ko'cha, uy):")


@router.message(BookDelivery.address)
async def delivery_address(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if len(text) < 5:
        await msg.answer("Iltimos, to'liq manzilingizni kiriting:")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    await state.clear()

    if order_id:
        async with session_factory() as s:
            order = await s.get(BookOrder, int(order_id))
            if order:
                order.delivery_name = data.get("d_name")
                order.delivery_phone = data.get("d_phone")
                order.delivery_address = text
                order.status = OrderStatus.PROCESSING
                await s.commit()

    await msg.answer(
        "✅ <b>Ma'lumotlaringiz qabul qilindi!</b>\n\n"
        "📦 Kitobingiz tez kunda sizga yuboriladi.\n"
        "Yetkazib berish jarayonini <b>WebApp</b>da kuzatishingiz mumkin. 🚚",
    )

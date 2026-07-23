"""T-018 · Invite link orqali qo'shilish / chiqishlarni yozib borish servisi.

`chat_member` update handler tanasi yupqa bo'lishi uchun barcha DB logikasi shu
yerda joylashgan. `InviteJoin` yozuvi `UNIQUE(invite_link_id, joined_user_tg_id)`
orqali dublikatlardan himoyalangan, `InviteLink.join_count` esa atomik
`UPDATE ... SET join_count = join_count + 1` bilan yangilanadi.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.referral import InviteJoin, InviteLink, TrackedChat
from models.rewards import RewardTier
from models.telegram_user import TelegramUser
from services.referral.rewards import evaluate_user_rewards

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class JoinResult:
    """`record_join` natijasi.

    - `counted` — join hisoblanganmi (T-018 semantikasi, avvalgi `bool` qaytim).
    - `inviter_tg_id` — invite link egasining Telegram ID'si (tabriknoma yuborish uchun).
    - `newly_earned_rewards` — shu chaqiruvda yangi qozonilgan reward tier'lari.
    """

    counted: bool
    inviter_tg_id: int | None = None
    newly_earned_rewards: list[RewardTier] = field(default_factory=list)

    def __bool__(self) -> bool:  # eski `if await record_join(...)` chaqiruvlar uchun.
        return self.counted


async def record_join(
    session: AsyncSession,
    *,
    tracked_chat_tg_id: int,
    joined_user_tg_id: int,
    invite_link_str: str,
) -> JoinResult:
    """Foydalanuvchining ma'lum invite link orqali qo'shilishini yozadi.

    Args:
        session: Async DB sessiya (handler boshqaradi).
        tracked_chat_tg_id: Telegram chat_id (manfiy uzun raqam bo'lishi mumkin).
        joined_user_tg_id: Yangi a'zoning Telegram ID'si.
        invite_link_str: Telegram `chat_member` update'idagi `invite_link.invite_link`.

    Returns:
        `JoinResult` — `counted=True` bo'lsa yangi join yozildi va reward
        tier'lari (agar bor bo'lsa) `newly_earned_rewards` da qaytariladi.
        Handler shu ro'yxatni oladi va invite link egasiga tabriknoma yuboradi.
    """
    # 1) TrackedChat + InviteLink birgalikda topamiz.
    stmt = (
        select(InviteLink, TrackedChat)
        .join(TrackedChat, InviteLink.tracked_chat_id == TrackedChat.id)
        .where(
            TrackedChat.chat_id == tracked_chat_tg_id,
            InviteLink.invite_link == invite_link_str,
        )
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        logger.debug(
            "record_join: mos InviteLink topilmadi (chat_tg=%s link=%s)",
            tracked_chat_tg_id,
            invite_link_str,
        )
        return JoinResult(counted=False)
    invite_link: InviteLink = row[0]

    # 2) O'z-o'zini invite qilishni bloklash.
    owner = await session.get(TelegramUser, invite_link.user_id)
    if owner is not None and owner.telegram_id == joined_user_tg_id:
        logger.info(
            "record_join: o'z-o'ziga invite bloklandi (user_id=%s tg=%s)",
            invite_link.user_id,
            joined_user_tg_id,
        )
        return JoinResult(counted=False)

    # 3) Mavjud InviteJoin yozuvini tekshiramiz (qaytib qo'shilish holati).
    existing_stmt = select(InviteJoin).where(
        InviteJoin.invite_link_id == invite_link.id,
        InviteJoin.joined_user_tg_id == joined_user_tg_id,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()

    if existing is not None:
        if existing.is_counted and existing.left_at is None:
            # Allaqachon a'zo va hisoblangan — hech nima qilmaymiz.
            logger.debug(
                "record_join: dublikat, allaqachon counted "
                "(invite_link_id=%s tg=%s)",
                invite_link.id,
                joined_user_tg_id,
            )
            return JoinResult(counted=False)
        # Qaytib qo'shildi — reactivate.
        existing.left_at = None
        existing.is_counted = True
        await _increment_join_count(session, invite_link.id)
        new_rewards = await evaluate_user_rewards(session, invite_link.user_id)
        await session.commit()
        logger.info(
            "record_join: qayta qo'shildi (invite_link_id=%s tg=%s)",
            invite_link.id,
            joined_user_tg_id,
        )
        return JoinResult(
            counted=True,
            inviter_tg_id=owner.telegram_id if owner is not None else None,
            newly_earned_rewards=new_rewards,
        )

    # 4) Yangi InviteJoin.
    session.add(
        InviteJoin(
            invite_link_id=invite_link.id,
            joined_user_tg_id=joined_user_tg_id,
            left_at=None,
            is_counted=True,
        )
    )
    try:
        await session.flush()
    except IntegrityError:
        # UNIQUE (invite_link_id, joined_user_tg_id) — poyga holatida yutildi.
        await session.rollback()
        logger.info(
            "record_join: UNIQUE violation — dublikat yutildi "
            "(invite_link_id=%s tg=%s)",
            invite_link.id,
            joined_user_tg_id,
        )
        return JoinResult(counted=False)

    await _increment_join_count(session, invite_link.id)
    new_rewards = await evaluate_user_rewards(session, invite_link.user_id)
    await session.commit()
    logger.info(
        "record_join: yangi join yozildi (invite_link_id=%s tg=%s)",
        invite_link.id,
        joined_user_tg_id,
    )
    return JoinResult(
        counted=True,
        inviter_tg_id=owner.telegram_id if owner is not None else None,
        newly_earned_rewards=new_rewards,
    )


async def record_leave(
    session: AsyncSession,
    *,
    tracked_chat_tg_id: int,
    left_user_tg_id: int,
) -> None:
    """Foydalanuvchining chatdan chiqishini barcha mos InviteJoin'larda belgilaydi.

    Bitta foydalanuvchi bir vaqtda faqat bitta invite link orqali kelgan bo'ladi,
    lekin nazariy jihatdan bir necha `is_counted=True` yozuvlar bo'lishi mumkin
    (masalan, tarixiy migratsiyalardan) — barchasini decrement qilamiz.
    """
    stmt = (
        select(InviteJoin, InviteLink)
        .join(InviteLink, InviteJoin.invite_link_id == InviteLink.id)
        .join(TrackedChat, InviteLink.tracked_chat_id == TrackedChat.id)
        .where(
            TrackedChat.chat_id == tracked_chat_tg_id,
            InviteJoin.joined_user_tg_id == left_user_tg_id,
            InviteJoin.left_at.is_(None),
        )
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        logger.debug(
            "record_leave: mos aktiv InviteJoin topilmadi "
            "(chat_tg=%s tg=%s)",
            tracked_chat_tg_id,
            left_user_tg_id,
        )
        return

    now = datetime.now(timezone.utc)
    for join, invite_link in rows:
        was_counted = join.is_counted
        join.left_at = now
        join.is_counted = False
        if was_counted:
            await _decrement_join_count(session, invite_link.id)
    await session.commit()
    logger.info(
        "record_leave: %d ta InviteJoin yopildi (chat_tg=%s tg=%s)",
        len(rows),
        tracked_chat_tg_id,
        left_user_tg_id,
    )


async def _increment_join_count(session: AsyncSession, invite_link_id: int) -> None:
    """Atomik `UPDATE ... SET join_count = join_count + 1`."""
    await session.execute(
        update(InviteLink)
        .where(InviteLink.id == invite_link_id)
        .values(join_count=InviteLink.join_count + 1)
    )


async def _decrement_join_count(session: AsyncSession, invite_link_id: int) -> None:
    """Atomik `UPDATE ... SET join_count = join_count - 1` (0 dan pastga tushmaydi)."""
    await session.execute(
        update(InviteLink)
        .where(InviteLink.id == invite_link_id, InviteLink.join_count > 0)
        .values(join_count=InviteLink.join_count - 1)
    )

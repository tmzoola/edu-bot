"""Referral (taklif) tizimi uchun admin panel view'lari.

Modellar: TrackedChat, InviteLink, InviteJoin (`app/models/referral.py`).

Barcha view'lar ko'p jihatdan **read-only** — invite linklar va qo'shilish
hodisalari faqat Telegram / bot service tomonidan yaratiladi. TrackedChat
uchun faqat `is_active` toggle qilinishi mumkin.
"""
from admin.views.base import BaseAdminView
from starlette.requests import Request
from starlette_admin import (
    BooleanField,
    DateTimeField,
    HasOne,
    IntegerField,
    StringField,
    TextAreaField,
)


class TrackedChatAdminView(BaseAdminView):
    name = "Kuzatiladigan chat"
    label = "Referral: kuzatiladigan chatlar"
    icon = "fa fa-hashtag"

    fields = [
        "id",
        IntegerField("chat_id", label="Telegram chat ID", read_only=True),
        StringField("title", label="Nomi", read_only=True),
        StringField("type", label="Turi", read_only=True),
        StringField("username", label="Username", read_only=True),
        BooleanField("is_active", label="Faol"),
        "createdAt",
        "updatedAt",
    ]

    column_list = [
        "id",
        "chat_id",
        "title",
        "type",
        "username",
        "is_active",
        "createdAt",
        "updatedAt",
    ]
    column_searchable_list = ["title", "username", "chat_id"]
    column_sortable_list = ["createdAt", "is_active", "type"]
    fields_default_sort = [("createdAt", True)]

    def can_create(self, request: Request) -> bool:
        return False


class InviteLinkAdminView(BaseAdminView):
    name = "Taklif linki"
    label = "Referral: taklif linklari"
    icon = "fa fa-link"

    fields = [
        "id",
        HasOne("user", label="Foydalanuvchi", identity="foydalanuvchi"),
        HasOne("tracked_chat", label="Chat", identity="referral-tracked-chat"),
        StringField("invite_link", label="Invite link", read_only=True),
        StringField("telegram_link_name", label="Telegram link nomi", read_only=True),
        IntegerField("join_count", label="Qo'shilganlar soni", read_only=True),
        "createdAt",
        StringField("revoked_at", label="Bekor qilingan sana", read_only=True),
    ]

    column_list = [
        "id",
        "user",
        "tracked_chat",
        "invite_link",
        "telegram_link_name",
        "join_count",
        "createdAt",
        "revoked_at",
    ]
    column_searchable_list = ["telegram_link_name", "invite_link"]
    column_sortable_list = ["join_count", "createdAt", "revoked_at"]
    fields_default_sort = [("join_count", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class RewardTierAdminView(BaseAdminView):
    """T-021 · Reward tier CRUD — admin bosqichlarni sozlaydi."""

    name = "Sovg'a bosqichi"
    label = "Referral: sovg'a bosqichlari"
    icon = "fa fa-gift"

    fields = [
        "id",
        StringField("title", label="Nomi", required=True),
        TextAreaField("description", label="Tavsif", required=False),
        IntegerField(
            "required_invites",
            label="Kerakli takliflar soni",
            required=True,
        ),
        BooleanField("is_active", label="Faol"),
        StringField("image_url", label="Rasm URL (ixtiyoriy)", required=False),
        "createdAt",
        "updatedAt",
    ]

    column_list = [
        "id",
        "title",
        "required_invites",
        "is_active",
        "createdAt",
    ]
    column_searchable_list = ["title"]
    column_sortable_list = ["required_invites", "is_active", "createdAt"]
    fields_default_sort = [("required_invites", False)]


class UserRewardAdminView(BaseAdminView):
    """T-021 · User reward — read-only + `claimed_at`/`note` tahrirlash."""

    name = "Qozonilgan sovg'a"
    label = "Referral: qozonilgan sovg'alar"
    icon = "fa fa-trophy"

    fields = [
        "id",
        HasOne("user", label="Foydalanuvchi", identity="foydalanuvchi"),
        HasOne(
            "reward_tier",
            label="Sovg'a bosqichi",
            identity="referral-reward-tier",
        ),
        DateTimeField("earned_at", label="Qozonilgan sana", read_only=True),
        DateTimeField(
            "claimed_at",
            label="Yetkazilgan sana",
            required=False,
        ),
        TextAreaField("note", label="Admin izohi", required=False),
        "createdAt",
    ]

    column_list = [
        "id",
        "user",
        "reward_tier",
        "earned_at",
        "claimed_at",
        "note",
    ]
    column_sortable_list = ["earned_at", "claimed_at"]
    fields_default_sort = [("earned_at", True)]

    def can_create(self, request: Request) -> bool:
        return False


class InviteJoinAdminView(BaseAdminView):
    name = "Qo'shilish (referral)"
    label = "Referral: qo'shilishlar"
    icon = "fa fa-user-plus"

    fields = [
        "id",
        HasOne("invite_link", label="Taklif linki", identity="referral-invite-link"),
        IntegerField("joined_user_tg_id", label="Qo'shilgan foydalanuvchi (Telegram ID)", read_only=True),
        StringField("createdAt", label="Qo'shilgan sana", read_only=True),
        StringField("left_at", label="Tark etgan sana", read_only=True),
        BooleanField("is_counted", label="Hisoblangan", read_only=True),
        StringField("pending_until", label="Grace tugash sanasi", read_only=True),
        StringField("reject_reason", label="Rad etish sababi", read_only=True),
    ]

    column_list = [
        "id",
        "invite_link",
        "joined_user_tg_id",
        "createdAt",
        "left_at",
        "is_counted",
        "pending_until",
        "reject_reason",
    ]
    column_searchable_list = ["joined_user_tg_id", "reject_reason"]
    column_sortable_list = [
        "createdAt", "left_at", "is_counted", "pending_until"
    ]
    # T-022 · Admin `is_counted` bo'yicha filtrlashi uchun oddiy boolean filter.
    column_filters = ["is_counted"]
    fields_default_sort = [("createdAt", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

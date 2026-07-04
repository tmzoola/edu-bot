from pathlib import Path

from admin.auth import AdminAuth
from admin.views.module import ModuleAdminView
from admin.views.question import QuestionAdminView
from admin.views.quiz import QuizAdminView
from admin.views.telegram_user import TelegramUserAdminView
from admin.views.topic import TopicAdminView
from db.session import engine
from fastapi import FastAPI
from models.module import Module
from models.question import Question
from models.quiz import Quiz
from models.telegram_user import TelegramUser
from models.topic import Topic
from starlette_admin.contrib.sqla import Admin
from starlette_admin.views import Link

_TEMPLATES_DIR = str(Path(__file__).parent / "templates")


def setup_admin(app: FastAPI) -> None:
    admin = Admin(
        engine,
        title="Malaka — Admin",
        auth_provider=AdminAuth(),
        base_url="/admin/",
        templates_dir=_TEMPLATES_DIR,
    )

    admin.add_view(Link(
        label="Test yaratish",
        icon="fa fa-wand-magic-sparkles",
        url="/admin-tools/builder",
    ))
    admin.add_view(Link(
        label="Reyting",
        icon="fa fa-trophy",
        url="/admin-tools/leaderboard",
    ))
    admin.add_view(ModuleAdminView(Module, identity="modul"))
    admin.add_view(TopicAdminView(Topic, identity="mavzu"))
    admin.add_view(QuizAdminView(Quiz, identity="test"))
    admin.add_view(QuestionAdminView(Question, identity="savol"))
    admin.add_view(TelegramUserAdminView(TelegramUser, identity="foydalanuvchi"))

    admin.mount_to(app)

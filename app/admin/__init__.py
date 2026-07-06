from pathlib import Path

from admin.auth import AdminAuth
from admin.i18n_uz import install_uzbek
from admin.views.book import BookAdminView
from admin.views.module import ModuleAdminView
from admin.views.question import QuestionAdminView
from admin.views.quiz import QuizAdminView
from admin.views.telegram_user import TelegramUserAdminView
from admin.views.topic import TopicAdminView
from db.session import engine
from fastapi import FastAPI
from models.book import Book
from models.module import Module
from models.question import Question
from models.quiz import Quiz
from models.telegram_user import TelegramUser
from models.topic import Topic
from starlette_admin.contrib.sqla import Admin
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import Link

_TEMPLATES_DIR = str(Path(__file__).parent / "templates")


def setup_admin(app: FastAPI) -> None:
    # Register the Uzbek locale before building the admin so its Jinja env and
    # DataTables config pick it up.
    install_uzbek()

    admin = Admin(
        engine,
        title="Muslima Darmonova",
        auth_provider=AdminAuth(),
        base_url="/admin/",
        templates_dir=_TEMPLATES_DIR,
        # Force Uzbek; ignore the browser's Accept-Language so it doesn't flip
        # to en/ru. A language cookie (from the switcher) can still override.
        i18n_config=I18nConfig(default_locale="uz", language_header_name=None),
    )

    admin.add_view(Link(
        label="Test yaratish",
        icon="fa fa-wand-magic-sparkles",
        url="/admin-tools/builder",
    ))
    admin.add_view(Link(
        label="Yutuqli testlar",
        icon="fa fa-trophy",
        url="/admin-tools/contests",
    ))
    admin.add_view(Link(
        label="Kitob yuklash",
        icon="fa fa-file-arrow-up",
        url="/admin-tools/books",
    ))
    admin.add_view(Link(
        label="Reyting",
        icon="fa fa-trophy",
        url="/admin-tools/leaderboard",
    ))
    admin.add_view(Link(
        label="Motivatsiya",
        icon="fa fa-quote-left",
        url="/admin-tools/quotes",
    ))
    admin.add_view(Link(
        label="Xabar yuborish",
        icon="fa fa-bullhorn",
        url="/admin-tools/broadcast",
    ))
    admin.add_view(ModuleAdminView(Module, identity="modul"))
    admin.add_view(TopicAdminView(Topic, identity="mavzu"))
    admin.add_view(QuizAdminView(Quiz, identity="test"))
    admin.add_view(QuestionAdminView(Question, identity="savol"))
    admin.add_view(BookAdminView(Book, identity="kitob"))
    admin.add_view(TelegramUserAdminView(TelegramUser, identity="foydalanuvchi"))

    admin.mount_to(app)

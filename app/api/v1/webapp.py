import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl

from core.config import settings
from db.session import get_db
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.attempt import QuizAttempt
from models.module import Module
from models.question import Question
from models.quiz import Quiz
from models.telegram_user import TelegramUser
from models.topic import Topic
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# HTML pages
pages = APIRouter(prefix="/webapp", tags=["webapp-pages"])
# JSON API
api = APIRouter(prefix="/api/v1/webapp", tags=["webapp-api"])

templates = Jinja2Templates(directory="templates")


# ═══ HTML pages ══════════════════════════════════════════════════════

@pages.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@pages.get("/modules", response_class=HTMLResponse)
async def modules_page(request: Request):
    return templates.TemplateResponse("modules.html", {"request": request})


@pages.get("/modules/{module_id}", response_class=HTMLResponse)
async def module_topics_page(request: Request, module_id: int):
    return templates.TemplateResponse("topics.html", {"request": request, "module_id": module_id})


@pages.get("/topics/{topic_id}", response_class=HTMLResponse)
async def topic_quizzes_page(request: Request, topic_id: int):
    return templates.TemplateResponse("quizzes.html", {"request": request, "topic_id": topic_id})


@pages.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def quiz_page(request: Request, quiz_id: int):
    return templates.TemplateResponse("quiz.html", {"request": request, "quiz_id": quiz_id})


@pages.get("/results/{attempt_id}", response_class=HTMLResponse)
async def results_page(request: Request, attempt_id: int):
    return templates.TemplateResponse("results.html", {"request": request, "attempt_id": attempt_id})


@pages.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request):
    return templates.TemplateResponse("leaderboard.html", {"request": request})


@pages.get("/me", response_class=HTMLResponse)
async def me_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


# ═══ Telegram initData validation ════════════════════════════════════

def _verify_telegram_init_data(init_data: str) -> dict[str, Any] | None:
    """Return decoded user dict if HMAC matches, else None."""
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_from_client = parsed.pop("hash", None)
        if not hash_from_client:
            return None
        data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed))
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, hash_from_client):
            return None
        user_json = parsed.get("user")
        if not user_json:
            return None
        return json.loads(user_json)
    except Exception:  # noqa: BLE001
        logger.exception("initData verification failed")
        return None


async def _get_or_create_tg_user(db: AsyncSession, tg_data: dict[str, Any]) -> TelegramUser:
    tg_id = int(tg_data["id"])
    result = await db.execute(select(TelegramUser).where(TelegramUser.telegram_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        # Refresh basic fields
        user.first_name = tg_data.get("first_name") or user.first_name
        user.last_name = tg_data.get("last_name") or user.last_name
        user.username = tg_data.get("username") or user.username
        user.language_code = tg_data.get("language_code") or user.language_code
        return user
    user = TelegramUser(
        telegram_id=tg_id,
        first_name=tg_data.get("first_name"),
        last_name=tg_data.get("last_name"),
        username=tg_data.get("username"),
        language_code=tg_data.get("language_code"),
    )
    db.add(user)
    await db.flush()
    return user


async def _resolve_user(
    db: AsyncSession,
    x_init_data: str | None,
    x_tg_id: int | None,
) -> TelegramUser | None:
    """Prefer signed initData, fall back to plain telegram_id in dev."""
    if x_init_data:
        tg = _verify_telegram_init_data(x_init_data)
        if tg:
            user = await _get_or_create_tg_user(db, tg)
            await db.commit()
            return user
    if x_tg_id and settings.APP_MODE != "PRODUCTION":
        # Dev fallback so we can test without Telegram WebApp environment
        result = await db.execute(select(TelegramUser).where(TelegramUser.telegram_id == x_tg_id))
        user = result.scalar_one_or_none()
        if not user:
            user = TelegramUser(telegram_id=x_tg_id, first_name="Dev")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user
    return None


# ═══ Auth endpoint ═══════════════════════════════════════════════════

@api.post("/auth")
async def auth(payload: dict[str, Any], db: AsyncSession = Depends(get_db)):
    init_data = (payload or {}).get("init_data") or ""
    tg = _verify_telegram_init_data(init_data)

    if not tg and settings.APP_MODE != "PRODUCTION":
        # Dev fallback: accept a raw {"user": {...}}
        tg = (payload or {}).get("user")

    if not tg:
        raise HTTPException(401, "initData tekshiruvidan o'tmadi")

    user = await _get_or_create_tg_user(db, tg)
    await db.commit()

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }


# ═══ Public content ══════════════════════════════════════════════════

@api.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    topics_count = await db.scalar(
        select(func.count()).select_from(Topic).where(Topic.is_active == True)  # noqa: E712
    ) or 0
    questions_count = await db.scalar(select(func.count()).select_from(Question)) or 0
    modules_count = await db.scalar(
        select(func.count()).select_from(Module).where(Module.is_active == True)  # noqa: E712
    ) or 0
    return {
        "topics_count": topics_count,
        "questions_count": questions_count,
        "modules_count": modules_count,
    }


@api.get("/modules")
async def list_modules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order, Module.id)  # noqa: E712
    )
    modules = result.scalars().all()

    counts = {}
    if modules:
        ids = [m.id for m in modules]
        rows = await db.execute(
            select(Topic.module_id, func.count(Topic.id))
            .where(Topic.module_id.in_(ids), Topic.is_active == True)  # noqa: E712
            .group_by(Topic.module_id)
        )
        counts = dict(rows.all())

    return [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "icon": m.icon,
            "color": m.color,
            "topic_count": counts.get(m.id, 0),
        }
        for m in modules
    ]


@api.get("/modules/{module_id}/topics")
async def module_topics(module_id: int, db: AsyncSession = Depends(get_db)):
    module = await db.get(Module, module_id)
    if not module:
        raise HTTPException(404, "Modul topilmadi")

    result = await db.execute(
        select(Topic)
        .where(Topic.module_id == module_id, Topic.is_active == True)  # noqa: E712
        .order_by(Topic.order, Topic.id)
    )
    topics = result.scalars().all()

    quiz_counts = {}
    if topics:
        ids = [t.id for t in topics]
        rows = await db.execute(
            select(Quiz.topic_id, func.count(Quiz.id))
            .where(Quiz.topic_id.in_(ids), Quiz.is_active == True)  # noqa: E712
            .group_by(Quiz.topic_id)
        )
        quiz_counts = dict(rows.all())

    return {
        "module": {"id": module.id, "title": module.title, "description": module.description},
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "quiz_count": quiz_counts.get(t.id, 0),
            }
            for t in topics
        ],
    }


@api.get("/topics/{topic_id}/quizzes")
async def topic_quizzes(topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Mavzu topilmadi")

    result = await db.execute(
        select(Quiz)
        .where(Quiz.topic_id == topic_id, Quiz.is_active == True)  # noqa: E712
        .order_by(Quiz.id)
    )
    quizzes = result.scalars().all()

    q_counts = {}
    if quizzes:
        ids = [q.id for q in quizzes]
        rows = await db.execute(
            select(Question.quiz_id, func.count(Question.id))
            .where(Question.quiz_id.in_(ids))
            .group_by(Question.quiz_id)
        )
        q_counts = dict(rows.all())

    return {
        "topic": {"id": topic.id, "title": topic.title},
        "quizzes": [
            {
                "id": q.id,
                "title": q.title,
                "description": q.description,
                "time_limit_seconds": q.time_limit_seconds,
                "question_count": q_counts.get(q.id, 0),
            }
            for q in quizzes
        ],
    }


@api.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id, Quiz.is_active == True)  # noqa: E712
        .options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Test topilmadi")

    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "time_limit_seconds": quiz.time_limit_seconds,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                # correct_option intentionally omitted
            }
            for q in sorted(quiz.questions, key=lambda x: x.order)
        ],
    }


@api.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: int,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
    x_tg_id: int | None = Header(default=None, alias="X-Telegram-Id"),
):
    user = await _resolve_user(db, x_init_data, x_tg_id)
    if not user:
        raise HTTPException(401, "Foydalanuvchi aniqlanmadi")

    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, "Test topilmadi")

    answers: dict = payload.get("answers", {})
    time_taken = int(payload.get("time_taken_seconds") or 0)

    # Clamp to quiz time limit
    if time_taken <= 0 or time_taken > quiz.time_limit_seconds:
        time_taken = quiz.time_limit_seconds

    score = 0
    total = len(quiz.questions)
    for q in quiz.questions:
        chosen = answers.get(str(q.id))
        if chosen and chosen == q.correct_option.value:
            score += 1

    attempt = QuizAttempt(
        user_id=user.id,
        quiz_id=quiz_id,
        score=score,
        total=total,
        time_taken_seconds=time_taken,
        answers=answers,
        # completed_at column is TIMESTAMP WITHOUT TIME ZONE; use naive UTC.
        completed_at=datetime.utcnow(),
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "score": score,
        "total": total,
        "points": attempt.points,
        "time_taken_seconds": time_taken,
    }


@api.get("/results/{attempt_id}")
async def get_results(attempt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id)
        .options(selectinload(QuizAttempt.quiz).selectinload(Quiz.questions))
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(404, "Natija topilmadi")

    # ── Per-question review ─────────────────────────────────────────
    user_answers = attempt.answers or {}
    questions_review = []
    for q in sorted(attempt.quiz.questions, key=lambda x: x.order):
        chosen = user_answers.get(str(q.id))
        correct = q.correct_option.value
        questions_review.append({
            "id": q.id,
            "order": q.order,
            "text": q.text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "user_answer": chosen,
            "correct_answer": correct,
            "is_correct": chosen == correct,
            "answered": chosen is not None,
            "explanation": q.explanation,
        })

    # ── History: all attempts by same user on same quiz ────────────
    history_result = await db.execute(
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == attempt.user_id,
            QuizAttempt.quiz_id == attempt.quiz_id,
        )
        .order_by(QuizAttempt.createdAt.asc())
    )
    history_attempts = history_result.scalars().all()

    # Number them 1..N in chronological order, and mark the current one
    history = []
    current_index = 0
    best_points = 0
    for i, a in enumerate(history_attempts, start=1):
        if a.id == attempt.id:
            current_index = i
        best_points = max(best_points, a.points)
        history.append({
            "attempt_id": a.id,
            "attempt_number": i,
            "score": a.score,
            "total": a.total,
            "points": a.points,
            "percentage": a.percentage,
            "time_taken_seconds": a.time_taken_seconds,
            "date": a.createdAt.strftime("%d.%m.%Y %H:%M") if a.createdAt else "",
            "is_current": a.id == attempt.id,
        })

    # Trend vs previous attempt
    trend = None
    if current_index > 1:
        prev = history[current_index - 2]
        cur = history[current_index - 1]
        trend = {
            "points_delta": cur["points"] - prev["points"],
            "time_delta": cur["time_taken_seconds"] - prev["time_taken_seconds"],
        }

    return {
        "attempt_id": attempt.id,
        "attempt_number": current_index,
        "total_attempts": len(history),
        "is_best": attempt.points == best_points,
        "score": attempt.score,
        "total": attempt.total,
        "points": attempt.points,
        "percentage": attempt.percentage,
        "time_taken_seconds": attempt.time_taken_seconds,
        "quiz_id": attempt.quiz.id,
        "quiz_title": attempt.quiz.title,
        "questions": questions_review,
        "history": history,
        "trend": trend,
    }


# ═══ Leaderboard ═════════════════════════════════════════════════════

_PERIODS = {"day": 1, "week": 7, "month": 30}


def _period_since(period: str) -> datetime | None:
    days = _PERIODS.get(period)
    if not days:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


@api.get("/leaderboard")
async def leaderboard(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    period: str = "all",
):
    """
    Global leaderboard: sum of points per user (score * 2), tiebreaker by
    total time_taken_seconds ascending (faster = higher).
    Period filter: day / week / month / all — filters QuizAttempt.createdAt.
    """
    total_points = (func.sum(QuizAttempt.score) * 2).label("points")
    total_time = func.sum(QuizAttempt.time_taken_seconds).label("time_taken")
    attempts_n = func.count(QuizAttempt.id).label("attempts_n")

    stmt = (
        select(
            TelegramUser.id,
            TelegramUser.first_name,
            TelegramUser.last_name,
            TelegramUser.username,
            total_points,
            total_time,
            attempts_n,
        )
        .join(QuizAttempt, QuizAttempt.user_id == TelegramUser.id)
        .group_by(TelegramUser.id)
        .order_by(desc("points"), "time_taken")
        .limit(limit)
    )

    since = _period_since(period)
    if since is not None:
        stmt = stmt.where(QuizAttempt.createdAt >= since)

    rows = (await db.execute(stmt)).all()

    return [
        {
            "rank": i + 1,
            "user_id": r.id,
            "name": (r.first_name or r.username or f"#{r.id}"),
            "username": r.username,
            "points": int(r.points or 0),
            "time_taken_seconds": int(r.time_taken or 0),
            "attempts": int(r.attempts_n or 0),
        }
        for i, r in enumerate(rows)
    ]


@api.get("/me/progress")
async def my_progress(
    db: AsyncSession = Depends(get_db),
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
    x_tg_id: int | None = Header(default=None, alias="X-Telegram-Id"),
):
    user = await _resolve_user(db, x_init_data, x_tg_id)
    if not user:
        raise HTTPException(401, "Foydalanuvchi aniqlanmadi")

    result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user.id)
        .options(selectinload(QuizAttempt.quiz))
        .order_by(QuizAttempt.createdAt.desc())
        .limit(20)
    )
    attempts = result.scalars().all()

    total_points = sum(a.points for a in attempts)
    total_attempts = await db.scalar(
        select(func.count()).select_from(QuizAttempt).where(QuizAttempt.user_id == user.id)
    ) or 0

    return {
        "user": {
            "id": user.id,
            "name": user.first_name or user.username or f"#{user.telegram_id}",
            "username": user.username,
        },
        "total_points": total_points,
        "total_attempts": total_attempts,
        "recent": [
            {
                "attempt_id": a.id,
                "quiz_title": a.quiz.title,
                "score": a.score,
                "total": a.total,
                "points": a.points,
                "time_taken_seconds": a.time_taken_seconds,
                "percentage": a.percentage,
                "date": a.createdAt.strftime("%d.%m.%Y %H:%M") if a.createdAt else "",
            }
            for a in attempts
        ],
    }


# ═══ Admin stats (unchanged) ═════════════════════════════════════════

@api.get("/admin-stats")
async def admin_dashboard_stats(db: AsyncSession = Depends(get_db)):
    users     = await db.scalar(select(func.count()).select_from(TelegramUser)) or 0
    quizzes   = await db.scalar(select(func.count()).select_from(Quiz)) or 0
    questions = await db.scalar(select(func.count()).select_from(Question)) or 0
    topics    = await db.scalar(select(func.count()).select_from(Topic)) or 0
    modules   = await db.scalar(select(func.count()).select_from(Module)) or 0
    active_q  = await db.scalar(select(func.count()).select_from(Quiz).where(Quiz.is_active == True)) or 0  # noqa: E712
    active_t  = await db.scalar(select(func.count()).select_from(Topic).where(Topic.is_active == True)) or 0  # noqa: E712
    attempts  = await db.scalar(select(func.count()).select_from(QuizAttempt)) or 0

    result = await db.execute(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.user), selectinload(QuizAttempt.quiz))
        .order_by(QuizAttempt.createdAt.desc())
        .limit(6)
    )
    recent = result.scalars().all()

    return {
        "users": users, "quizzes": quizzes, "questions": questions,
        "topics": topics, "modules": modules,
        "active_quizzes": active_q, "active_topics": active_t,
        "total_attempts": attempts,
        "recent_attempts": [
            {
                "user": a.user.first_name or a.user.username or f"#{a.user.telegram_id}",
                "quiz": a.quiz.title,
                "score": a.score,
                "total": a.total,
                "percentage": a.percentage,
                "date": a.completed_at.strftime("%d.%m.%Y %H:%M") if a.completed_at else "—",
            }
            for a in recent
        ],
    }

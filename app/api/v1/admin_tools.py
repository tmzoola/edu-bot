import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import ALLOWED_BOOK_EXT, MAX_BOOK_SIZE, MEDIA_ROOT
from db.session import get_db
from models.book import Book
from models.module import Module
from models.question import CorrectOption, Question
from models.quiz import Quiz
from models.topic import Topic

router = APIRouter(prefix="/admin-tools", tags=["admin-tools"])
templates = Jinja2Templates(directory="templates")

BOOKS_DIR = MEDIA_ROOT / "books"


@router.get("/leaderboard", response_class=HTMLResponse)
async def admin_leaderboard_page(request: Request):
    return templates.TemplateResponse("admin_leaderboard.html", {"request": request})


@router.get("/builder", response_class=HTMLResponse)
async def builder_page(request: Request, db: AsyncSession = Depends(get_db)):
    modules = (await db.execute(select(Module).order_by(Module.order, Module.id))).scalars().all()
    topics = (await db.execute(select(Topic).order_by(Topic.order, Topic.id))).scalars().all()
    return templates.TemplateResponse(
        "admin_builder.html",
        {
            "request": request,
            "modules": [{"id": m.id, "title": m.title} for m in modules],
            "topics": [{"id": t.id, "title": t.title, "module_id": t.module_id} for t in topics],
        },
    )


@router.post("/builder/save")
async def builder_save(payload: dict[str, Any], db: AsyncSession = Depends(get_db)):
    # ── Module (optional but recommended) ──────────────────────────
    module_id = payload.get("module_id")
    new_module_title = (payload.get("new_module_title") or "").strip()

    if new_module_title:
        module = Module(title=new_module_title, is_active=True, order=0)
        db.add(module)
        await db.flush()
        module_id = module.id
    elif module_id:
        module_id = int(module_id)
        if not await db.get(Module, module_id):
            raise HTTPException(400, "Modul topilmadi")
    else:
        module_id = None

    # ── Topic (existing id OR new) ─────────────────────────────────
    topic_id = payload.get("topic_id")
    new_topic_title = (payload.get("new_topic_title") or "").strip()

    if not topic_id and not new_topic_title:
        raise HTTPException(400, "Mavzu tanlanmagan yoki kiritilmagan")

    if new_topic_title:
        topic = Topic(
            title=new_topic_title,
            module_id=module_id,
            is_active=True,
            order=0,
        )
        db.add(topic)
        await db.flush()
        topic_id = topic.id
    else:
        topic_id = int(topic_id)
        existing = await db.get(Topic, topic_id)
        if not existing:
            raise HTTPException(400, "Mavzu topilmadi")
        # If admin chose a module and topic wasn't linked, link it
        if module_id and not existing.module_id:
            existing.module_id = module_id

    # ── Quiz ───────────────────────────────────────────────────────
    title = (payload.get("quiz_title") or "").strip()
    if not title:
        raise HTTPException(400, "Test sarlavhasi kiritilmagan")

    time_limit = int(payload.get("time_limit_seconds") or 300)

    quiz = Quiz(
        topic_id=topic_id,
        title=title,
        description=(payload.get("quiz_description") or "").strip() or None,
        time_limit_seconds=time_limit,
        is_active=True,
    )
    db.add(quiz)
    await db.flush()

    # ── Questions ──────────────────────────────────────────────────
    questions_in: list[dict] = payload.get("questions") or []
    if not questions_in:
        raise HTTPException(400, "Kamida bitta savol kerak")

    saved = 0
    for i, q in enumerate(questions_in, start=1):
        text = (q.get("text") or "").strip()
        a = (q.get("option_a") or "").strip()
        b = (q.get("option_b") or "").strip()
        c = (q.get("option_c") or "").strip()
        d = (q.get("option_d") or "").strip()
        correct = (q.get("correct") or "A").strip().upper()

        if not (text and a and b and c and d):
            continue
        if correct not in ("A", "B", "C", "D"):
            correct = "A"

        db.add(Question(
            quiz_id=quiz.id,
            order=i,
            text=text,
            option_a=a, option_b=b, option_c=c, option_d=d,
            correct_option=CorrectOption(correct),
            explanation=(q.get("explanation") or "").strip() or None,
        ))
        saved += 1

    if saved == 0:
        raise HTTPException(400, "Hech qanday to'liq savol kiritilmagan")

    # Capture ids BEFORE commit — attributes expire after commit and would
    # trigger a sync lazy-load on an async session.
    quiz_id = quiz.id
    await db.commit()

    return {
        "ok": True,
        "topic_id": topic_id,
        "quiz_id": quiz_id,
        "questions_saved": saved,
    }


# ═══ Books upload tool ═════════════════════════════════════════════

@router.get("/books", response_class=HTMLResponse)
async def books_page(request: Request, db: AsyncSession = Depends(get_db)):
    topics = (await db.execute(select(Topic).order_by(Topic.order, Topic.id))).scalars().all()
    books = (await db.execute(select(Book).order_by(Book.createdAt.desc()))).scalars().all()
    categories = sorted({b.category for b in books if b.category})
    return templates.TemplateResponse(
        "admin_books.html",
        {
            "request": request,
            "topics": [{"id": t.id, "title": t.title} for t in topics],
            "categories": categories,
            "books": [
                {
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "category": b.category,
                    "topic_id": b.topic_id,
                    "file_name": b.file_name,
                    "file_size": b.file_size,
                    "downloads": b.downloads,
                    "is_active": b.is_active,
                }
                for b in books
            ],
        },
    )


@router.post("/books/upload")
async def books_upload(
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(""),
    category: str = Form(""),
    description: str = Form(""),
    topic_id: str = Form(""),
):
    title = title.strip()
    if not title:
        raise HTTPException(400, "Sarlavha kiritilmagan")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_BOOK_EXT:
        raise HTTPException(400, f"Fayl turi qo'llab-quvvatlanmaydi: {ext or 'nomaʼlum'}")

    data = await file.read()
    if len(data) > MAX_BOOK_SIZE:
        raise HTTPException(400, "Fayl juda katta (maks. 100 MB)")
    if not data:
        raise HTTPException(400, "Fayl bo'sh")

    tid: int | None = None
    if topic_id.strip():
        tid = int(topic_id)
        if not await db.get(Topic, tid):
            raise HTTPException(400, "Mavzu topilmadi")

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"books/{uuid.uuid4().hex}{ext}"
    (MEDIA_ROOT / stored).write_bytes(data)

    book = Book(
        title=title,
        author=author.strip() or None,
        category=category.strip() or None,
        description=description.strip() or None,
        topic_id=tid,
        file_path=stored,
        file_name=file.filename or f"kitob{ext}",
        file_size=len(data),
        is_active=True,
        downloads=0,
        order=0,
    )
    db.add(book)
    await db.commit()
    return {"ok": True, "id": book.id}


@router.post("/books/{book_id}/delete")
async def books_delete(book_id: int, db: AsyncSession = Depends(get_db)):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Kitob topilmadi")
    try:
        (MEDIA_ROOT / book.file_path).unlink(missing_ok=True)
    except OSError:
        pass
    await db.delete(book)
    await db.commit()
    return {"ok": True}


@router.post("/builder/parse")
async def builder_parse(payload: dict[str, Any]):
    """Parse a bulk-pasted questions block into structured questions."""
    text = payload.get("text") or ""
    return {"questions": _parse_bulk(text)}


# ── helpers ────────────────────────────────────────────────────────

_OPT_RE = re.compile(r"^\s*([A-D])[\)\.\:\-]\s*(.+?)\s*$", re.IGNORECASE)
_ANS_RE = re.compile(r"^\s*(?:answer|javob|to['`]?g['`]?ri)\s*[:\-]\s*([A-D])\s*$", re.IGNORECASE)


def _parse_bulk(raw: str) -> list[dict]:
    """
    Parse blocks like:

        1. What is 2+2?
        A) 3
        B) 4
        C) 5
        D) 6
        Answer: B

    Questions are separated by blank line or a `---` line.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in raw.splitlines():
        s = line.rstrip()
        if not s.strip() or s.strip() == "---":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(s)
    if current:
        blocks.append(current)

    out: list[dict] = []
    for block in blocks:
        q: dict[str, str] = {"text": "", "option_a": "", "option_b": "",
                             "option_c": "", "option_d": "", "correct": "A"}
        text_lines: list[str] = []
        for line in block:
            m_ans = _ANS_RE.match(line)
            if m_ans:
                q["correct"] = m_ans.group(1).upper()
                continue
            m_opt = _OPT_RE.match(line)
            if m_opt:
                letter = m_opt.group(1).upper()
                q[f"option_{letter.lower()}"] = m_opt.group(2)
                continue
            text_lines.append(line)

        text = " ".join(l.strip() for l in text_lines).strip()
        # strip leading numbering like "1." / "1)"
        text = re.sub(r"^\s*\d+\s*[\.\)\-\:]\s*", "", text).strip()
        q["text"] = text

        if q["text"] and q["option_a"] and q["option_b"] and q["option_c"] and q["option_d"]:
            out.append(q)

    return out

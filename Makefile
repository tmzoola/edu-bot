.PHONY: up down logs shell migrate makemigrations install run

# ─── Docker ───────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f app

shell:
	docker compose exec app bash

# ─── Database (run from project root so alembic.ini is found) ─────────────────
migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "$(msg)"

# ─── Local dev ────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

run:
	cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

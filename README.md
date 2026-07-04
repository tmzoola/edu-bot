# Samandar Market — POS

A supermarket Point-of-Sale system with a fast web cashier dashboard and a
full admin panel (product CRUD, daily / weekly reports, CSV export).

## Features

- **Cashier dashboard** — split layout (65% product grid · 35% live basket),
  category tabs, instant search, +/- quantity controls, cash-received with
  auto-calculated change + "exact cash" shortcut, big Checkout button, and a
  receipt modal with a Cancel/void option for mistakes. Every checkout is
  persisted to PostgreSQL.
- **Admin panel** at `/admin` — JWT cookie login, product CRUD with soft
  delete, daily report (date picker, summary cards, hourly bar chart,
  expandable transactions, CSV export), weekly overview (today-vs-yesterday,
  weekly chart, top-5 products). Charts are drawn on plain `<canvas>` — zero
  JS libraries.
- **Persistence** — PostgreSQL 15 + async SQLAlchemy + Alembic migrations.
  Seeds 24 sample products and a default admin (`admin` / `admin123`) on first
  startup.
- **Self-contained** — `docker compose up -d` brings up Postgres + the
  FastAPI app, runs migrations, and starts serving. One command.

## Tech stack

| Layer            | Library                                          |
|------------------|--------------------------------------------------|
| Web              | FastAPI + uvicorn                                |
| Database         | PostgreSQL 15, SQLAlchemy 2.x async + asyncpg    |
| Migrations       | Alembic (async env)                              |
| Auth             | JWT cookie (`python-jose`) + bcrypt passwords    |
| Frontend         | Plain HTML/CSS/JS — zero framework, two files    |

## Quick start (Docker)

```bash
git clone <your-repo-url> samandar_market
cd samandar_market

cp .env.example .env
# Defaults work out of the box. Optionally set JWT_SECRET (otherwise a random
# one is generated per process and admin sessions invalidate on restart).

docker compose up -d
```

- **Cashier dashboard**: <http://localhost:8000>
- **Admin panel**: <http://localhost:8000/admin>  — first login is
  `admin` / `admin123` (logged to the container on first startup).

### Logs / rebuild

```bash
docker compose logs -f app
docker compose up -d --build           # after Python or dependency changes
```

The `public/` folder is bind-mounted, so **frontend edits do not require a
rebuild** — just refresh the browser.

## Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # change DATABASE_URL host to localhost

# Start Postgres however you like (e.g. just the db service from compose):
docker compose up -d db

# Apply migrations:
alembic upgrade head

# Run the app (seeds run automatically in lifespan on first start):
uvicorn main:app --reload --port 8000
```

## Environment variables

| Key                          | Purpose                                                                  |
|------------------------------|--------------------------------------------------------------------------|
| `DATABASE_URL`               | Async SQLAlchemy URL — `postgresql+asyncpg://user:pass@host:port/db`.    |
| `POSTGRES_USER/PASSWORD/DB`  | Used by the Postgres container.                                          |
| `JWT_SECRET`                 | Admin session signing key. Random per-process if unset.                  |
| `ADMIN_DEFAULT_USERNAME`     | Seed admin username (default `admin`, used only on first start).         |
| `ADMIN_DEFAULT_PASSWORD`     | Seed admin password (default `admin123`, **change after first login**).  |

## Endpoints

### Public
| Method | Path                | Purpose                                              |
|--------|---------------------|------------------------------------------------------|
| GET    | `/`                 | Cashier dashboard.                                   |
| GET    | `/admin`            | Admin SPA (login + admin views).                     |
| GET    | `/health`           | `{"status": "ok"}`. Used by Docker healthcheck.      |
| GET    | `/api/products`     | Active products + category list.                     |
| POST   | `/api/checkout`     | `{items, cash_received}` → persisted transaction.    |
| DELETE | `/api/transactions/{id}` | Void a just-completed transaction (used by receipt modal). |

### Admin (require JWT cookie)
| Method | Path                                  | Purpose                                  |
|--------|---------------------------------------|------------------------------------------|
| POST   | `/admin/login`                        | `{username, password}` → sets cookie.    |
| GET    | `/admin/logout`                       | Clears the cookie.                       |
| GET    | `/admin/me`                           | Current admin (used by SPA to check auth).|
| GET    | `/admin/products`                     | All products (incl. inactive).           |
| POST   | `/api/products`                       | Create.                                  |
| PUT    | `/api/products/{id}`                  | Update.                                  |
| DELETE | `/api/products/{id}`                  | Soft delete (`is_active=false`).         |
| GET    | `/api/reports/daily?date=YYYY-MM-DD`  | Daily report.                            |
| GET    | `/api/reports/weekly`                 | Weekly overview.                         |
| GET    | `/api/reports/top-products?period=...`| Top 5 products (`day`/`week`/`month`).   |
| GET    | `/api/reports/export?date=YYYY-MM-DD` | CSV download for the given day.          |

## Project layout

```
main.py                FastAPI app — routes + seed lifecycle
database.py            Async SQLAlchemy engine + session factory
models.py              ORM models (Product, Transaction, TransactionItem, Admin)
schemas.py             Pydantic request/response models
crud.py                DB queries + report aggregates
auth.py                JWT cookie helpers, bcrypt, get_current_admin dep
seed.py                Initial products + default admin (runs in lifespan)
products.py            Static seed list (only used by seed.py)
alembic.ini            Alembic config
migrations/            Async Alembic env + initial schema
public/index.html      Cashier dashboard (single-file)
public/admin.html      Admin panel (single-file, plain canvas charts)
requirements.txt       Python dependencies
Dockerfile             python:3.11-slim → uvicorn on :8000
docker-compose.yml     db + app services, runs `alembic upgrade head` on boot
.env.example           Template — copy to .env
.dockerignore          Excludes secrets, caches, legacy files
```

## Adding products

Use the admin panel at `/admin` — log in, open the **Mahsulotlar** tab,
click **+ Yangi mahsulot**. New products appear in the cashier dashboard on
its next page load.

`products.py` is only used for the first-startup seed. Editing it after
seeding has no effect; the database is the source of truth.

## Notes

- Basket state lives **in the browser**, not on the server. Refreshing the
  page clears the basket — same as any cashier "new customer" reset.
- Money is stored as integer UZS (`BigInteger`) throughout. UZS has no minor
  unit in practice, so this avoids float / Decimal headaches.
- Day boundaries in reports are **Tashkent local** (UTC+5, no DST). A sale at
  23:30 May 14 belongs to May 14's report regardless of UTC.

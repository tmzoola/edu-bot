#!/bin/sh
set -e

echo "▶ Running database migrations..."
alembic upgrade head

echo "▶ Collecting static files..."
python app/collect_static.py

echo "▶ Starting server..."
cd app
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

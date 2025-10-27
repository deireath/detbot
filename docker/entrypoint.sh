#!/usr/bin/env bash
set -euo pipefail

echo "[bot] Waiting for Postgres and Redis via compose healthchecks..."
# Зависимости по healthcheck обеспечит docker-compose (depends_on с condition: service_healthy)

echo "[bot] Running migrations..."
# Если твой модуль миграций называется иначе — поправь строку ниже.
python -m migrations.create_tables

echo "[bot] Starting bot..."
exec python -m main
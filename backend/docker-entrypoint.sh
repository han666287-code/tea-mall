#!/bin/sh
set -e

# 启动前执行数据库迁移（Alembic），数据库未就绪时有限重试后明确失败退出
MAX_ATTEMPTS=20
DELAY=2
attempt=1

until alembic upgrade head; do
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "alembic upgrade head failed after ${MAX_ATTEMPTS} attempts; check DATABASE_URL and MySQL status" >&2
    exit 1
  fi
  echo "database not ready for migration (attempt ${attempt}/${MAX_ATTEMPTS}); retrying in ${DELAY}s" >&2
  attempt=$((attempt + 1))
  sleep "$DELAY"
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

# TeaMall 后端镜像：Python 3.13 + FastAPI + uvicorn
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先安装依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 业务代码（.env 与本地开发数据不复制进镜像）
COPY app ./app
COPY seed.py .
COPY alembic.ini .
COPY alembic ./alembic
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Moscow

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY app ./app

# Миграции применяются при каждом старте — это безопасно, alembic пропускает уже применённые.
CMD ["sh", "-c", "alembic upgrade head && python -m app.bot"]

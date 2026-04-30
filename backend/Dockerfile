FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install --prefix=/install -e .

COPY . .

# ---

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=prod \
    DEBUG=false

EXPOSE 8000

# Run migrations then start the API. Single replica only — APScheduler runs
# in-process; for multi-replica, switch to Celery beat or set
# SCHEDULER_ENABLED=false on extras and run a dedicated worker.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

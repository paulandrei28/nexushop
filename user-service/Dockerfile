# ── Build stage ────────────────────────────────────────────────
# Build context is the PROJECT ROOT (set in docker-compose.yml)
FROM python:3.12-slim AS builder

WORKDIR /build

COPY user-service/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────
FROM python:3.12-slim

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY user-service/app ./app
COPY shared ./shared

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app.main:create_app()"]

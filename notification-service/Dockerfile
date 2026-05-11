# Build context is the PROJECT ROOT
FROM python:3.12-slim AS builder

WORKDIR /build

COPY notification-service/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime ───────────────────────────────────────────────────
FROM python:3.12-slim

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY notification-service/app ./app
COPY shared ./shared

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

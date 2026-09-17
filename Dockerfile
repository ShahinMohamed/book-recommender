# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
    && apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
RUN addgroup --system --gid 10001 bookrecommender \
    && adduser --system --uid 10001 --ingroup bookrecommender --home /app bookrecommender \
    && chown -R bookrecommender:bookrecommender /app

FROM base AS runtime
USER bookrecommender
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

FROM base AS ingestion
USER root
COPY requirements-ingest.txt ./
RUN pip install --no-cache-dir -r requirements-ingest.txt
COPY scripts ./scripts
COPY data ./data
RUN chown -R bookrecommender:bookrecommender /app
USER bookrecommender
ENTRYPOINT ["python", "-m", "scripts.ingest"]

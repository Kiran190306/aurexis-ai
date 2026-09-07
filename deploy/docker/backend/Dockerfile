FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# libpq-dev supplies pg_config for PostgreSQL packages. Audio and magic
# libraries make every declared production dependency buildable in this stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev portaudio19-dev libsndfile1-dev libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

FROM base AS dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# This target intentionally contains build prerequisites and all dependencies.
# It is used by Compose's audit profile, not by the production runtime.
FROM dependencies AS audit
RUN pip install "pip-audit==2.7.3" "safety==2.3.5"
COPY scripts/audit-dependencies.sh /usr/local/bin/audit-dependencies
RUN chmod 0555 /usr/local/bin/audit-dependencies
ENTRYPOINT ["/usr/local/bin/audit-dependencies"]

FROM dependencies AS runtime
COPY . /app/
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app \
    && chmod +x /app/docker-entrypoint.sh
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl --fail http://localhost:8000/health/live || exit 1
CMD ["/app/docker-entrypoint.sh"]

# Separate review image; active trading Dockerfile/Compose stay unchanged.
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
COPY docs/research/ndx-strategy/postgres-v1/schema.sql \
    ./docs/research/ndx-strategy/postgres-v1/schema.sql
# Source import preserves the repository-relative schema identity path used by
# the recorder. No active config, credentials, migration runner or bot starts.
ENV PYTHONPATH=/app/src
ENV PATH=/app/.venv/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
RUN groupadd --gid 1001 ndxobserver \
    && useradd --uid 1001 --gid ndxobserver --no-create-home \
       --shell /usr/sbin/nologin ndxobserver
USER ndxobserver
CMD ["python", "-m", "butterfly_guy.research.ndx_observer_cli"]

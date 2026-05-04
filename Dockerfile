FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
RUN groupadd --gid 1001 butterfly \
    && useradd --uid 1001 --gid butterfly --create-home --shell /usr/sbin/nologin butterfly

# Activate venv for all subsequent RUN/CMD steps
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies (cached layer — only invalidates if pyproject.toml/uv.lock change)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY src/ ./src/
COPY configs/config.yaml configs/config.yaml
COPY tools/notify.py ./
RUN uv sync --frozen --no-dev --no-editable

# Ensure SQL migration files are present (uv may use a cached wheel that omits new .sql files)
RUN cp -r src/butterfly_guy/db/migrations/*.sql \
    .venv/lib/python3.12/site-packages/butterfly_guy/db/migrations/

RUN chown -R butterfly:butterfly /app
USER butterfly

# Default: run live trader. Override CMD for collector or backtest.
CMD ["python", "-m", "butterfly_guy.scripts.run_live"]

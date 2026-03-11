FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies (cached layer — only invalidates if pyproject.toml/uv.lock change)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY src/ ./src/
COPY config.yaml ./
RUN uv sync --frozen --no-dev --no-editable

# Default: run live trader. Override CMD for collector or backtest.
CMD ["uv", "run", "python", "-m", "butterfly_guy.scripts.run_live"]

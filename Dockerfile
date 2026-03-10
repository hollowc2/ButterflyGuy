FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/
COPY config.yaml ./

# Default: run live trader. Override CMD for collector or backtest.
CMD ["uv", "run", "python", "src/butterfly_guy/scripts/run_live.py"]

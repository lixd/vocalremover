FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy backend files
COPY backend/pyproject.toml backend/.python-version ./

# Install Python dependencies (including Spleeter)
RUN uv sync --no-dev

# Copy backend source
COPY backend/ ./

# Pre-download Spleeter model
RUN uv run python -c "\
from spleeter.separator import Separator; \
import numpy as np; \
s = Separator('spleeter:2stems'); \
s.separate(np.random.randn(44100 * 10, 2).astype(np.float32)); \
print('Model downloaded successfully')"

# Install gunicorn for production
RUN uv pip install gunicorn

# Create media directory
RUN mkdir -p /app/media

# Copy and configure entrypoint
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD [".venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4"]

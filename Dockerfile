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

# Pre-download Spleeter models
RUN uv run python -c "\
from spleeter.separator import Separator; \
import numpy as np; \
s2 = Separator('spleeter:2stems'); \
s2.separate(np.random.randn(44100 * 10, 2).astype(np.float32)); \
s4 = Separator('spleeter:4stems'); \
s4.separate(np.random.randn(44100 * 10, 2).astype(np.float32)); \
print('Models downloaded successfully')"

# Install gunicorn for production
RUN uv pip install gunicorn

# Create media directory
RUN mkdir -p /app/media

# Expose port
EXPOSE 8000

# Default command: gunicorn for production
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4"]

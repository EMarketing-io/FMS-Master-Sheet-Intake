# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Faster, unbuffered logs to Cloud Logging
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OS deps: ffmpeg for pydub, CA certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# App workspace
WORKDIR /app

# Install backend-only deps
# (We copy only the backend requirements first to leverage Docker layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the whole repo (backend imports reach config/, etc.)
COPY . .

# One-shot job entrypoint (processes all 'Processing' rows then exits)
CMD ["python", "backend/main.py"]
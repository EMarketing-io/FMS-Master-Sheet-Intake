# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Faster logs & smaller images
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# System deps: ffmpeg for pydub, CA certs, curl for debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# App workspace
WORKDIR /app

# Install Python deps first (leverages Docker layer cache)
# If your backend requirements list is at backend/requirements.txt (as in your cloudbuild):
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# If you keep a single requirements.txt at repo root instead, swap the two lines above for:
# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the whole repo (backend imports reach config/, etc.)
COPY . .

# One-shot job: processes all 'Processing' rows then exits
CMD ["python", "backend/main.py"]

# GOAT Platform API - Cloud Run
FROM python:3.11-slim

# Install ffmpeg for MoviePy (video assembly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY pyproject.toml .

# Cloud Run sets PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Use PORT from environment so Cloud Run can inject it
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

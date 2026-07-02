# Backend service — FastAPI application
#
# Kept deliberately simple (single-stage) for an academic project: the
# priority is a reproducible, easy-to-explain build, not a minimal
# production image. A multi-stage build would be a reasonable future
# improvement but adds complexity that isn't pedagogically necessary here.

FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; add build-essential only if a future dependency
# needs to compile C extensions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Production-profile default: no --reload, and the port is read from $PORT
# so the same image works on hosts that assign their own port (e.g. Render).
# docker-compose overrides this command with --reload for local development.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

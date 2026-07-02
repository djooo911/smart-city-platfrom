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

# --reload is intentionally used for the academic/dev context (docker-compose
# mounts the source as a volume). For a "production" profile this would be
# replaced with a plain `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

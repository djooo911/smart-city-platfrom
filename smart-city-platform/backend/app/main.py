"""
FastAPI application entrypoint.

Responsibilities:
    - Construct the FastAPI app.
    - Wire up logging.
    - Wire up MongoDB connection lifecycle (connect + ensure indexes on
      startup, close on shutdown).
    - Register all routers: system (health), auth, lamps, alerts, and the
      blockchain explorer.
    - Enable permissive CORS so the static HTML/JS dashboard (served from a
      different port/container) can call the API during local development.
    - Translate a concurrent blockchain-append race (see
      IngestTelemetryUseCase and friends -- two requests both mining onto
      the same previous block) into a clean 409 instead of a raw 500: the
      unique index on `blockchain.index` (Milestone 3) is what actually
      catches the race, this just gives the client a sane response.

`/traffic/*` and `/system/energy-savings` are NOT registered -- see
docs/architecture.md and this milestone's plan for why (no backing data
pipeline exists yet).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from app.api.routers import alerts, auth, blockchain, lamps, system
from app.config import get_settings
from app.infrastructure.mongo.client import close_mongo_connection, connect_to_mongo, get_database
from app.infrastructure.mongo.indexes import ensure_indexes
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s", get_settings().app_name)
    connect_to_mongo()
    await ensure_indexes(get_database())
    yield
    logger.info("Shutting down %s", get_settings().app_name)
    close_mongo_connection()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Smart City Public Lighting and Traffic Monitoring platform "
            "with Blockchain Traceability."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "conflict", "message": "Concurrent write conflict, retry"}},
        )

    app.include_router(system.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(lamps.router, prefix=settings.api_v1_prefix)
    app.include_router(alerts.router, prefix=settings.api_v1_prefix)
    app.include_router(blockchain.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

"""
FastAPI application entrypoint.

Milestone 0 responsibilities ONLY:
    - Construct the FastAPI app.
    - Wire up logging.
    - Wire up MongoDB connection lifecycle (connect on startup, close on shutdown).
    - Register the `system` router (health check) so the stack is verifiable
      end-to-end via Docker Compose.
    - Enable permissive CORS so the static HTML/JS dashboard (served from a
      different port/container) can call the API during local development.

No business routers (lamps, traffic, alerts, blockchain) are registered
yet — those arrive with their respective milestones, once the underlying
use cases and repositories exist.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import system
from app.config import get_settings
from app.infrastructure.mongo.client import close_mongo_connection, connect_to_mongo
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s", get_settings().app_name)
    connect_to_mongo()
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
            "with Blockchain Traceability. Milestone 0: project scaffold."
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

    app.include_router(system.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

"""
System-level endpoints: health checks and basic app metadata.

This router exists in Milestone 0 purely as *infrastructure scaffolding* —
it lets us verify that Docker Compose, FastAPI, and MongoDB are wired
together correctly, before any domain/business logic exists. It is not
part of the "business logic" excluded from this milestone; it's the
equivalent of a smoke test for the environment itself.

Endpoints:
    GET /api/v1/system/health -> overall service + dependency status
"""

import logging

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.config import Settings, get_settings
from app.infrastructure.mongo.client import ping_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check(
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    mongo_ok = await ping_database()

    status = "ok" if mongo_ok else "degraded"

    return {
        "data": {
            "status": status,
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "dependencies": {
                "mongodb": "ok" if mongo_ok else "unreachable",
            },
        },
        "meta": {},
    }

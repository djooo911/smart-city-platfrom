"""
Shared FastAPI dependencies.

Milestone 0 only needs a database dependency for the health check router.
As use cases are introduced (Milestone 1+), this module will grow to expose
dependency-injected use case instances to routers, e.g.:

    def get_process_telemetry_use_case(
        db: AsyncIOMotorDatabase = Depends(get_db),
    ) -> ProcessTelemetryUseCase:
        ...

Keeping all `Depends(...)` providers in one place makes it easy to see, at
a glance, everything a router is allowed to depend on.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.mongo.client import get_database


def get_db() -> AsyncIOMotorDatabase:
    return get_database()

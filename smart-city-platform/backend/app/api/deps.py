"""
Shared FastAPI dependencies.

Repository factories wrap the concrete Mongo implementations behind the
domain Protocols, so routers/use cases never import `app.infrastructure`
directly. Use-case factories chain off the repository factories via
FastAPI's dependency injection. Auth/RBAC dependencies (`get_current_user`,
`require_role`) live in app.security.rbac -- routers import them from
there directly rather than through a re-export here, since they're not
tied to the database dependency chain the rest of this file wires up.
"""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.application.use_cases.acknowledge_anomaly import AcknowledgeAnomalyUseCase
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.ingest_telemetry import IngestTelemetryUseCase
from app.application.use_cases.override_lighting import OverrideLightingUseCase
from app.application.use_cases.update_lamp_config import UpdateLampConfigUseCase
from app.domain.interfaces.anomaly_repository import AnomalyRepository
from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.domain.interfaces.lamp_repository import LampRepository
from app.domain.interfaces.sensor_reading_repository import SensorReadingRepository
from app.domain.interfaces.user_repository import UserRepository
from app.infrastructure.mongo.client import get_database
from app.infrastructure.mongo.repositories.anomaly_repository import MongoAnomalyRepository
from app.infrastructure.mongo.repositories.blockchain_repository import MongoBlockchainRepository
from app.infrastructure.mongo.repositories.lamp_repository import MongoLampRepository
from app.infrastructure.mongo.repositories.sensor_reading_repository import (
    MongoSensorReadingRepository,
)
from app.infrastructure.mongo.repositories.user_repository import MongoUserRepository


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_lamp_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> LampRepository:
    return MongoLampRepository(db)


def get_sensor_reading_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> SensorReadingRepository:
    return MongoSensorReadingRepository(db)


def get_anomaly_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AnomalyRepository:
    return MongoAnomalyRepository(db)


def get_blockchain_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BlockchainRepository:
    return MongoBlockchainRepository(db)


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return MongoUserRepository(db)


def get_authenticate_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(user_repository)


def get_ingest_telemetry_use_case(
    sensor_reading_repository: SensorReadingRepository = Depends(get_sensor_reading_repository),
    lamp_repository: LampRepository = Depends(get_lamp_repository),
    anomaly_repository: AnomalyRepository = Depends(get_anomaly_repository),
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
) -> IngestTelemetryUseCase:
    return IngestTelemetryUseCase(
        sensor_reading_repository, lamp_repository, anomaly_repository, blockchain_repository
    )


def get_override_lighting_use_case(
    lamp_repository: LampRepository = Depends(get_lamp_repository),
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
) -> OverrideLightingUseCase:
    return OverrideLightingUseCase(lamp_repository, blockchain_repository)


def get_update_lamp_config_use_case(
    lamp_repository: LampRepository = Depends(get_lamp_repository),
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
) -> UpdateLampConfigUseCase:
    return UpdateLampConfigUseCase(lamp_repository, blockchain_repository)


def get_acknowledge_anomaly_use_case(
    anomaly_repository: AnomalyRepository = Depends(get_anomaly_repository),
) -> AcknowledgeAnomalyUseCase:
    return AcknowledgeAnomalyUseCase(anomaly_repository)

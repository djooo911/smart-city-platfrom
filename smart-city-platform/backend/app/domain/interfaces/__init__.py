from app.domain.interfaces.anomaly_repository import AnomalyRepository
from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.domain.interfaces.lamp_repository import LampRepository
from app.domain.interfaces.sensor_reading_repository import SensorReadingRepository
from app.domain.interfaces.user_repository import UserRepository

__all__ = [
    "AnomalyRepository",
    "BlockchainRepository",
    "LampRepository",
    "SensorReadingRepository",
    "UserRepository",
]

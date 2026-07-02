"""
Centralized logging configuration.

Why this exists as its own module:
- Keeps `main.py` focused on wiring the FastAPI app together.
- Gives every layer (domain, application, infrastructure, api) a single,
  consistent logging format via `logging.getLogger(__name__)`, which will
  matter once we start logging anomaly detections, blockchain writes, and
  MQTT/HTTP ingestion events in later milestones.
- Log level is environment-driven (see config.py) so it can be turned up
  for debugging without a code change.
"""

import logging
import sys

from app.config import get_settings


def configure_logging() -> None:
    settings = get_settings()

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    logging.basicConfig(
        level=settings.log_level.upper(),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # ensures reconfiguration works cleanly under reload/tests
    )

    # Quiet down noisy third-party loggers by default; raise back to DEBUG
    # locally if you need to inspect driver-level behavior.
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logging.getLogger(__name__).info(
        "Logging configured (level=%s, env=%s)",
        settings.log_level.upper(),
        settings.app_env,
    )

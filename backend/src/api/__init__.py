"""
Módulo de API.

Proporciona la aplicación FastAPI y schemas.
"""

from .app import app
from .schemas import (
    PredictionBase,
    PredictionDetail,
    PredictionResponse,
    Top5Response,
    AccuracyStats,
    ModelMetrics,
    DailyStats,
    StatsResponse,
    FixtureInfo,
    UpcomingFixturesResponse,
    SyncRequest,
    SyncResponse,
    HealthCheck,
    ErrorResponse,
)


__all__ = [
    "app",
    # Schemas
    "PredictionBase",
    "PredictionDetail",
    "PredictionResponse",
    "Top5Response",
    "AccuracyStats",
    "ModelMetrics",
    "DailyStats",
    "StatsResponse",
    "FixtureInfo",
    "UpcomingFixturesResponse",
    "SyncRequest",
    "SyncResponse",
    "HealthCheck",
    "ErrorResponse",
]

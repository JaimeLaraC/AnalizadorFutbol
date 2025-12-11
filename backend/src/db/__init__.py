"""
Módulo de base de datos.

Proporciona modelos SQLAlchemy, conexión y repositorios.
"""

from .database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
)
from .models import (
    League,
    Team,
    Fixture,
    Standing,
    FixtureStatistics,
    TeamStatistics,
    Prediction,
    HeadToHead,
)
from .repositories import (
    LeagueRepository,
    TeamRepository,
    FixtureRepository,
    StandingRepository,
    PredictionRepository,
)


__all__ = [
    # Database
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "init_db",
    
    # Models
    "League",
    "Team",
    "Fixture",
    "Standing",
    "FixtureStatistics",
    "TeamStatistics",
    "Prediction",
    "HeadToHead",
    
    # Repositories
    "LeagueRepository",
    "TeamRepository",
    "FixtureRepository",
    "StandingRepository",
    "PredictionRepository",
]

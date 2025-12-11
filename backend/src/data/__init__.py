"""
Módulo de recopilación de datos y feature engineering.

Proporciona collectors para sincronizar datos y pipeline de features.
"""

from .league_collector import LeagueCollector, TOP_LEAGUES
from .team_collector import TeamCollector
from .fixture_collector import FixtureCollector
from .standings_collector import StandingsCollector
from .master_collector import MasterCollector, quick_sync

# Feature engineering
from .features import (
    FormCalculator,
    StandingsCalculator,
    H2HCalculator,
    FeaturePipeline,
    MatchFeatures,
)


__all__ = [
    # Collectors individuales
    "LeagueCollector",
    "TeamCollector",
    "FixtureCollector",
    "StandingsCollector",
    
    # Orquestador
    "MasterCollector",
    
    # Utilidades
    "quick_sync",
    "TOP_LEAGUES",
    
    # Feature engineering
    "FormCalculator",
    "StandingsCalculator",
    "H2HCalculator",
    "FeaturePipeline",
    "MatchFeatures",
]

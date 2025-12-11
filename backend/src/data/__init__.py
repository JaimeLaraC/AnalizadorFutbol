"""
Módulo de recopilación de datos.

Proporciona collectors para sincronizar datos desde API-Football a PostgreSQL.
"""

from .league_collector import LeagueCollector, TOP_LEAGUES
from .team_collector import TeamCollector
from .fixture_collector import FixtureCollector
from .standings_collector import StandingsCollector
from .master_collector import MasterCollector, quick_sync


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
]

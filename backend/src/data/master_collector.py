"""
Master Collector - Orquestador de recopilación de datos.

Coordina la sincronización de todos los datos desde API-Football.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime

from loguru import logger

from ..api_client import CachedAPIClient
from .league_collector import LeagueCollector, TOP_LEAGUES
from .team_collector import TeamCollector
from .fixture_collector import FixtureCollector
from .standings_collector import StandingsCollector


class MasterCollector:
    """
    Orquestador de recopilación de datos.
    
    Coordina todos los collectors para sincronizar datos completos.
    """
    
    def __init__(self, client: Optional[CachedAPIClient] = None):
        """
        Inicializa el master collector.
        
        Args:
            client: Cliente compartido de API-Football
        """
        self.client = client or CachedAPIClient()
        self._owns_client = client is None
        
        # Inicializar collectors compartiendo el cliente
        self.leagues = LeagueCollector(self.client)
        self.teams = TeamCollector(self.client)
        self.fixtures = FixtureCollector(self.client)
        self.standings = StandingsCollector(self.client)
    
    def sync_full_season(
        self,
        season: int,
        league_ids: Optional[List[int]] = None,
        include_standings: bool = True
    ) -> Dict[str, Any]:
        """
        Sincroniza una temporada completa.
        
        Args:
            season: Año de la temporada
            league_ids: Ligas a sincronizar (usa TOP_LEAGUES si None)
            include_standings: Si incluir clasificaciones
            
        Returns:
            Resumen de sincronización
        """
        if league_ids is None:
            league_ids = list(TOP_LEAGUES.keys())
        
        logger.info(f"Iniciando sincronización de temporada {season}")
        logger.info(f"Ligas a sincronizar: {len(league_ids)}")
        
        results = {
            "season": season,
            "leagues": 0,
            "teams": {},
            "fixtures": {},
            "standings": {},
            "totals": {
                "teams": 0,
                "fixtures": 0,
                "standings": 0,
            },
            "errors": []
        }
        
        try:
            # 1. Sincronizar ligas
            logger.info("Paso 1/4: Sincronizando ligas...")
            results["leagues"] = self.leagues.sync_leagues_to_db(
                season=season, 
                only_top=True
            )
            
            # 2. Sincronizar equipos
            logger.info("Paso 2/4: Sincronizando equipos...")
            results["teams"] = self.teams.sync_all_leagues(league_ids, season)
            results["totals"]["teams"] = sum(results["teams"].values())
            
            # 3. Sincronizar partidos
            logger.info("Paso 3/4: Sincronizando partidos...")
            results["fixtures"] = self.fixtures.sync_historical_season(
                league_ids, 
                season
            )
            results["totals"]["fixtures"] = sum(results["fixtures"].values())
            
            # 4. Sincronizar clasificaciones
            if include_standings:
                logger.info("Paso 4/4: Sincronizando clasificaciones...")
                results["standings"] = self.standings.sync_all_leagues(
                    league_ids, 
                    season
                )
                results["totals"]["standings"] = sum(results["standings"].values())
            
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            results["errors"].append(str(e))
        
        logger.info(
            f"Sincronización completada: "
            f"{results['totals']['teams']} equipos, "
            f"{results['totals']['fixtures']} partidos, "
            f"{results['totals']['standings']} posiciones"
        )
        
        return results
    
    def sync_today_fixtures(self) -> Dict[str, Any]:
        """
        Sincroniza partidos del día actual.
        
        Returns:
            Resumen de sincronización
        """
        today = date.today()
        logger.info(f"Sincronizando partidos de hoy: {today}")
        
        count = self.fixtures.sync_fixtures_by_date(today)
        
        return {
            "date": today.isoformat(),
            "fixtures": count
        }
    
    def sync_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Sincroniza partidos de un rango de fechas.
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            
        Returns:
            Resumen de sincronización
        """
        logger.info(f"Sincronizando rango: {start_date} a {end_date}")
        
        results = self.fixtures.sync_date_range(start_date, end_date)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "by_date": results,
            "total": sum(results.values())
        }
    
    def update_standings(
        self,
        season: int,
        league_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Actualiza clasificaciones actuales.
        
        Args:
            season: Temporada actual
            league_ids: Ligas a actualizar
            
        Returns:
            Resumen de sincronización
        """
        if league_ids is None:
            league_ids = list(TOP_LEAGUES.keys())
        
        logger.info(f"Actualizando clasificaciones temporada {season}")
        
        results = self.standings.sync_all_leagues(league_ids, season)
        
        return {
            "season": season,
            "by_league": results,
            "total": sum(results.values())
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché de la API.
        
        Returns:
            Estadísticas de caché
        """
        return self.client.get_cache_stats()
    
    def close(self):
        """Cierra todos los recursos."""
        if self._owns_client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Función de conveniencia para sincronización rápida
def quick_sync(season: int, top_leagues_only: bool = True) -> Dict[str, Any]:
    """
    Sincroniza rápidamente una temporada.
    
    Args:
        season: Año de la temporada
        top_leagues_only: Si solo sincronizar ligas principales
        
    Returns:
        Resumen de sincronización
    """
    league_ids = list(TOP_LEAGUES.keys()) if top_leagues_only else None
    
    with MasterCollector() as collector:
        return collector.sync_full_season(season, league_ids)

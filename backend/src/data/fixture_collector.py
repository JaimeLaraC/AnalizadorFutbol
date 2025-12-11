"""
Collector de partidos (fixtures) desde API-Football.

Recopila partidos históricos y próximos para entrenamiento y predicción.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from loguru import logger

from ..api_client import CachedAPIClient
from ..db import get_db_session, FixtureRepository
from ..db.models import Fixture


class FixtureCollector:
    """
    Recopila partidos desde API-Football.
    """
    
    def __init__(self, client: Optional[CachedAPIClient] = None):
        """
        Inicializa el collector.
        
        Args:
            client: Cliente de API-Football
        """
        self.client = client or CachedAPIClient()
        self._owns_client = client is None
    
    def get_fixtures_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Obtiene partidos de una fecha específica.
        
        Args:
            target_date: Fecha a consultar
            
        Returns:
            Lista de partidos
        """
        date_str = target_date.strftime("%Y-%m-%d")
        logger.info(f"Obteniendo partidos del {date_str}")
        
        response = self.client.get_fixtures(date=date_str)
        
        if not response.success:
            logger.error(f"Error obteniendo partidos: {response.error}")
            return []
        
        logger.info(f"Obtenidos {response.results} partidos")
        return response.data
    
    def get_fixtures_by_league_season(
        self, 
        league_id: int, 
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de una liga y temporada.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Lista de partidos
        """
        logger.info(f"Obteniendo partidos: liga {league_id}, temporada {season}")
        
        response = self.client.get_fixtures(league=league_id, season=season)
        
        if not response.success:
            logger.error(f"Error obteniendo partidos: {response.error}")
            return []
        
        logger.info(f"Obtenidos {response.results} partidos")
        return response.data
    
    def _parse_fixture(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea datos de fixture de la API al formato de BD.
        
        Args:
            data: Datos crudos de la API
            
        Returns:
            Diccionario para insertar en BD
        """
        fixture = data.get("fixture", {})
        league = data.get("league", {})
        teams = data.get("teams", {})
        goals = data.get("goals", {})
        score = data.get("score", {})
        
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        
        # Calcular resultado para modelo binario
        result = None
        if home_goals is not None and away_goals is not None:
            if home_goals > away_goals:
                result = 1  # Local gana
            elif away_goals > home_goals:
                result = 0  # Visitante gana
            # Empate = None (excluido del modelo)
        
        return {
            "id": fixture.get("id"),
            "league_id": league.get("id"),
            "season": league.get("season"),
            "round": league.get("round"),
            "home_team_id": teams.get("home", {}).get("id"),
            "away_team_id": teams.get("away", {}).get("id"),
            "date": datetime.fromisoformat(fixture.get("date").replace("Z", "+00:00")) if fixture.get("date") else None,
            "timestamp": fixture.get("timestamp"),
            "status": fixture.get("status", {}).get("short"),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "home_goals_halftime": score.get("halftime", {}).get("home"),
            "away_goals_halftime": score.get("halftime", {}).get("away"),
            "result": result,
            "venue_name": fixture.get("venue", {}).get("name"),
            "venue_city": fixture.get("venue", {}).get("city"),
        }
    
    def sync_fixtures_by_date(self, target_date: date) -> int:
        """
        Sincroniza partidos de una fecha a la base de datos.
        
        Args:
            target_date: Fecha a sincronizar
            
        Returns:
            Número de partidos sincronizados
        """
        fixtures_data = self.get_fixtures_by_date(target_date)
        
        count = 0
        
        with get_db_session() as db:
            repo = FixtureRepository(db)
            
            for data in fixtures_data:
                try:
                    fixture_dict = self._parse_fixture(data)
                    repo.upsert(fixture_dict)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error parseando fixture: {e}")
                    continue
            
            db.commit()
        
        logger.info(f"Sincronizados {count} partidos del {target_date}")
        return count
    
    def sync_fixtures_by_league(
        self, 
        league_id: int, 
        season: int
    ) -> int:
        """
        Sincroniza todos los partidos de una liga y temporada.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Número de partidos sincronizados
        """
        fixtures_data = self.get_fixtures_by_league_season(league_id, season)
        
        count = 0
        finished = 0
        draws = 0
        
        with get_db_session() as db:
            repo = FixtureRepository(db)
            
            for data in fixtures_data:
                try:
                    fixture_dict = self._parse_fixture(data)
                    repo.upsert(fixture_dict)
                    count += 1
                    
                    # Contar estadísticas
                    if fixture_dict.get("status") == "FT":
                        finished += 1
                        if fixture_dict.get("result") is None:
                            draws += 1
                            
                except Exception as e:
                    logger.warning(f"Error parseando fixture: {e}")
                    continue
            
            db.commit()
        
        logger.info(
            f"Liga {league_id}: {count} partidos, "
            f"{finished} terminados, {draws} empates (excluidos)"
        )
        return count
    
    def sync_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, int]:
        """
        Sincroniza partidos de un rango de fechas.
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            
        Returns:
            Diccionario {fecha: num_partidos}
        """
        results = {}
        current = start_date
        
        while current <= end_date:
            try:
                count = self.sync_fixtures_by_date(current)
                results[current.isoformat()] = count
            except Exception as e:
                logger.error(f"Error en fecha {current}: {e}")
                results[current.isoformat()] = 0
            
            current += timedelta(days=1)
        
        total = sum(results.values())
        logger.info(f"Total sincronizado en rango: {total} partidos")
        return results
    
    def sync_historical_season(
        self, 
        league_ids: List[int], 
        season: int
    ) -> Dict[int, int]:
        """
        Sincroniza temporada histórica de múltiples ligas.
        
        Args:
            league_ids: Lista de IDs de ligas
            season: Año de la temporada
            
        Returns:
            Diccionario {league_id: num_partidos}
        """
        results = {}
        
        for league_id in league_ids:
            try:
                count = self.sync_fixtures_by_league(league_id, season)
                results[league_id] = count
            except Exception as e:
                logger.error(f"Error en liga {league_id}: {e}")
                results[league_id] = 0
        
        total = sum(results.values())
        logger.info(f"Total temporada {season}: {total} partidos")
        return results
    
    def close(self):
        """Cierra el cliente si es propio."""
        if self._owns_client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

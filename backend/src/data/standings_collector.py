"""
Collector de clasificaciones (standings) desde API-Football.

Recopila posiciones de liga para contexto del modelo.
"""

from typing import List, Optional, Dict, Any

from loguru import logger

from ..api_client import CachedAPIClient
from ..db import get_db_session, StandingRepository
from ..db.models import Standing


class StandingsCollector:
    """
    Recopila clasificaciones desde API-Football.
    """
    
    def __init__(self, client: Optional[CachedAPIClient] = None):
        """
        Inicializa el collector.
        
        Args:
            client: Cliente de API-Football
        """
        self.client = client or CachedAPIClient()
        self._owns_client = client is None
    
    def get_standings(
        self, 
        league_id: int, 
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene clasificación de una liga.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Lista de posiciones
        """
        logger.info(f"Obteniendo clasificación: liga {league_id}, temporada {season}")
        
        response = self.client.get_standings(league=league_id, season=season)
        
        if not response.success:
            logger.error(f"Error obteniendo standings: {response.error}")
            return []
        
        # La respuesta tiene estructura anidada
        standings = []
        for league_data in response.data:
            league_standings = league_data.get("league", {}).get("standings", [])
            for group in league_standings:
                standings.extend(group)
        
        logger.info(f"Obtenidas {len(standings)} posiciones")
        return standings
    
    def _parse_standing(
        self, 
        data: Dict[str, Any], 
        league_id: int, 
        season: int
    ) -> Dict[str, Any]:
        """
        Parsea datos de standing al formato de BD.
        
        Args:
            data: Datos crudos de la API
            league_id: ID de la liga
            season: Temporada
            
        Returns:
            Diccionario para insertar en BD
        """
        team = data.get("team", {})
        all_stats = data.get("all", {})
        home_stats = data.get("home", {})
        away_stats = data.get("away", {})
        
        return {
            "league_id": league_id,
            "season": season,
            "team_id": team.get("id"),
            "rank": data.get("rank"),
            "points": data.get("points"),
            "goals_diff": data.get("goalsDiff"),
            "group_name": data.get("group"),
            "form": data.get("form"),
            "status": data.get("status"),
            "description": data.get("description"),
            
            # Estadísticas totales
            "played": all_stats.get("played", 0),
            "win": all_stats.get("win", 0),
            "draw": all_stats.get("draw", 0),
            "lose": all_stats.get("lose", 0),
            "goals_for": all_stats.get("goals", {}).get("for", 0),
            "goals_against": all_stats.get("goals", {}).get("against", 0),
            
            # Como local
            "home_played": home_stats.get("played", 0),
            "home_win": home_stats.get("win", 0),
            "home_draw": home_stats.get("draw", 0),
            "home_lose": home_stats.get("lose", 0),
            "home_goals_for": home_stats.get("goals", {}).get("for", 0),
            "home_goals_against": home_stats.get("goals", {}).get("against", 0),
            
            # Como visitante
            "away_played": away_stats.get("played", 0),
            "away_win": away_stats.get("win", 0),
            "away_draw": away_stats.get("draw", 0),
            "away_lose": away_stats.get("lose", 0),
            "away_goals_for": away_stats.get("goals", {}).get("for", 0),
            "away_goals_against": away_stats.get("goals", {}).get("against", 0),
        }
    
    def sync_standings_to_db(
        self, 
        league_id: int, 
        season: int
    ) -> int:
        """
        Sincroniza clasificación a la base de datos.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Número de posiciones sincronizadas
        """
        standings_data = self.get_standings(league_id, season)
        
        count = 0
        
        with get_db_session() as db:
            repo = StandingRepository(db)
            
            for data in standings_data:
                try:
                    standing_dict = self._parse_standing(data, league_id, season)
                    repo.upsert(standing_dict)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error parseando standing: {e}")
                    continue
            
            db.commit()
        
        logger.info(f"Sincronizadas {count} posiciones de liga {league_id}")
        return count
    
    def sync_all_leagues(
        self, 
        league_ids: List[int], 
        season: int
    ) -> Dict[int, int]:
        """
        Sincroniza clasificaciones de múltiples ligas.
        
        Args:
            league_ids: Lista de IDs de ligas
            season: Año de la temporada
            
        Returns:
            Diccionario {league_id: num_posiciones}
        """
        results = {}
        
        for league_id in league_ids:
            try:
                count = self.sync_standings_to_db(league_id, season)
                results[league_id] = count
            except Exception as e:
                logger.error(f"Error en liga {league_id}: {e}")
                results[league_id] = 0
        
        total = sum(results.values())
        logger.info(f"Total posiciones sincronizadas: {total}")
        return results
    
    def close(self):
        """Cierra el cliente si es propio."""
        if self._owns_client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

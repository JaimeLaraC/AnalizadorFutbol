"""
Collector de equipos desde API-Football.

Recopila información de equipos por liga y temporada.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger

from ..api_client import CachedAPIClient
from ..db import get_db_session, TeamRepository
from ..db.models import Team


class TeamCollector:
    """
    Recopila información de equipos desde API-Football.
    """
    
    def __init__(self, client: Optional[CachedAPIClient] = None):
        """
        Inicializa el collector.
        
        Args:
            client: Cliente de API-Football
        """
        self.client = client or CachedAPIClient()
        self._owns_client = client is None
    
    def get_teams_by_league(
        self, 
        league_id: int, 
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los equipos de una liga y temporada.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Lista de equipos
        """
        logger.info(f"Obteniendo equipos de liga {league_id} temporada {season}")
        
        response = self.client.get_teams(league=league_id, season=season)
        
        if not response.success:
            logger.error(f"Error obteniendo equipos: {response.error}")
            return []
        
        logger.info(f"Obtenidos {response.results} equipos")
        return response.data
    
    def sync_teams_to_db(
        self, 
        league_id: int, 
        season: int
    ) -> int:
        """
        Sincroniza equipos de una liga a la base de datos.
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            
        Returns:
            Número de equipos sincronizados
        """
        teams_data = self.get_teams_by_league(league_id, season)
        
        count = 0
        
        with get_db_session() as db:
            repo = TeamRepository(db)
            
            for data in teams_data:
                team_info = data.get("team", {})
                venue_info = data.get("venue", {})
                
                team_dict = {
                    "id": team_info.get("id"),
                    "name": team_info.get("name"),
                    "code": team_info.get("code"),
                    "country": team_info.get("country"),
                    "logo": team_info.get("logo"),
                    "founded": team_info.get("founded"),
                    "venue_name": venue_info.get("name"),
                    "venue_capacity": venue_info.get("capacity"),
                    "league_id": league_id,
                }
                
                repo.upsert(team_dict)
                count += 1
                logger.debug(f"Equipo sincronizado: {team_dict['name']}")
            
            db.commit()
        
        logger.info(f"Sincronizados {count} equipos de liga {league_id}")
        return count
    
    def sync_all_leagues(
        self, 
        league_ids: List[int], 
        season: int
    ) -> Dict[int, int]:
        """
        Sincroniza equipos de múltiples ligas.
        
        Args:
            league_ids: Lista de IDs de ligas
            season: Año de la temporada
            
        Returns:
            Diccionario {league_id: num_equipos}
        """
        results = {}
        
        for league_id in league_ids:
            try:
                count = self.sync_teams_to_db(league_id, season)
                results[league_id] = count
            except Exception as e:
                logger.error(f"Error sincronizando liga {league_id}: {e}")
                results[league_id] = 0
        
        total = sum(results.values())
        logger.info(f"Total equipos sincronizados: {total}")
        return results
    
    def close(self):
        """Cierra el cliente si es propio."""
        if self._owns_client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

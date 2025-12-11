"""
Collector de ligas disponibles en API-Football.

Recopila y almacena información de ligas para el sistema.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger

from ..api_client import CachedAPIClient
from ..db import get_db_session, LeagueRepository
from ..db.models import League


# Ligas principales europeas para priorizar
TOP_LEAGUES = {
    # Top 5 europeas
    39: "Premier League",         # Inglaterra
    140: "La Liga",               # España
    135: "Serie A",               # Italia
    78: "Bundesliga",             # Alemania
    61: "Ligue 1",                # Francia
    
    # Otras importantes
    2: "Champions League",
    3: "Europa League",
    848: "Conference League",
    
    # Segundas divisiones top
    40: "Championship",           # Inglaterra
    141: "La Liga 2",             # España
    136: "Serie B",               # Italia
    
    # Otras ligas europeas
    88: "Eredivisie",             # Holanda
    94: "Primeira Liga",          # Portugal
    144: "Jupiler Pro League",    # Bélgica
    
    # Sudamérica
    71: "Brasileirão Serie A",
    128: "Liga Profesional Argentina",
}


class LeagueCollector:
    """
    Recopila información de ligas desde API-Football.
    """
    
    def __init__(self, client: Optional[CachedAPIClient] = None):
        """
        Inicializa el collector.
        
        Args:
            client: Cliente de API-Football (crea uno si no se proporciona)
        """
        self.client = client or CachedAPIClient()
        self._owns_client = client is None
    
    def get_all_leagues(self, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las ligas disponibles.
        
        Args:
            season: Filtrar por temporada
            
        Returns:
            Lista de ligas
        """
        logger.info(f"Obteniendo ligas para temporada {season or 'todas'}")
        
        response = self.client.get_leagues(season=season)
        
        if not response.success:
            logger.error(f"Error obteniendo ligas: {response.error}")
            return []
        
        logger.info(f"Obtenidas {response.results} ligas")
        return response.data
    
    def get_top_leagues(self, season: int) -> List[Dict[str, Any]]:
        """
        Obtiene solo las ligas principales definidas en TOP_LEAGUES.
        
        Args:
            season: Temporada
            
        Returns:
            Lista de ligas principales
        """
        all_leagues = self.get_all_leagues(season=season)
        
        top = []
        for league_data in all_leagues:
            league_id = league_data.get("league", {}).get("id")
            if league_id in TOP_LEAGUES:
                top.append(league_data)
        
        logger.info(f"Filtradas {len(top)} ligas principales")
        return top
    
    def sync_leagues_to_db(
        self, 
        season: int, 
        only_top: bool = True
    ) -> int:
        """
        Sincroniza ligas a la base de datos.
        
        Args:
            season: Temporada
            only_top: Si True, solo sincroniza ligas principales
            
        Returns:
            Número de ligas sincronizadas
        """
        if only_top:
            leagues_data = self.get_top_leagues(season)
        else:
            leagues_data = self.get_all_leagues(season)
        
        count = 0
        
        with get_db_session() as db:
            repo = LeagueRepository(db)
            
            for data in leagues_data:
                league_info = data.get("league", {})
                country_info = data.get("country", {})
                
                league_dict = {
                    "id": league_info.get("id"),
                    "name": league_info.get("name"),
                    "country": country_info.get("name"),
                    "country_code": country_info.get("code"),
                    "logo": league_info.get("logo"),
                    "type": league_info.get("type"),
                }
                
                repo.upsert(league_dict)
                count += 1
                logger.debug(f"Liga sincronizada: {league_dict['name']}")
            
            db.commit()
        
        logger.info(f"Sincronizadas {count} ligas a la base de datos")
        return count
    
    def close(self):
        """Cierra el cliente si es propio."""
        if self._owns_client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

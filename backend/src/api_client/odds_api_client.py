"""
Cliente para The Odds API - Odds Históricas

Este cliente obtiene odds históricas de casas de apuestas reales
para usar en simulaciones de backtesting.

Documentación: https://the-odds-api.com/liveapi/guides/v4/
"""

import os
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class OddsResponse:
    """Respuesta de la API de odds."""
    success: bool
    data: List[Dict[str, Any]]
    timestamp: Optional[str] = None
    previous_timestamp: Optional[str] = None
    next_timestamp: Optional[str] = None
    error: Optional[str] = None


class TheOddsAPIClient:
    """
    Cliente para The Odds API.
    
    Proporciona acceso a odds históricas de casas de apuestas.
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Mapeo de ligas API-Football a The Odds API
    LEAGUE_MAPPING = {
        140: "soccer_spain_la_liga",      # La Liga
        39: "soccer_epl",                  # Premier League
        135: "soccer_italy_serie_a",       # Serie A
        78: "soccer_germany_bundesliga",   # Bundesliga
        61: "soccer_france_ligue_one",     # Ligue 1
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente.
        
        Args:
            api_key: API key de The Odds API. Si no se proporciona,
                    se busca en la variable de entorno ODDS_API_KEY.
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("API key no proporcionada. Establece ODDS_API_KEY o pasa api_key.")
        
        self.session = requests.Session()
        self.remaining_requests = None
        logger.info("TheOddsAPIClient inicializado")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> OddsResponse:
        """Realiza una petición a la API."""
        params["apiKey"] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        logger.debug(f"Request: GET {url}")
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # Actualizar contador de requests
            self.remaining_requests = response.headers.get("x-requests-remaining")
            logger.debug(f"Requests restantes: {self.remaining_requests}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Respuesta histórica tiene estructura diferente
                if isinstance(data, dict) and "data" in data:
                    return OddsResponse(
                        success=True,
                        data=data["data"],
                        timestamp=data.get("timestamp"),
                        previous_timestamp=data.get("previous_timestamp"),
                        next_timestamp=data.get("next_timestamp")
                    )
                else:
                    return OddsResponse(success=True, data=data if isinstance(data, list) else [data])
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return OddsResponse(success=False, data=[], error=error_msg)
                
        except Exception as e:
            logger.error(f"Error en request: {e}")
            return OddsResponse(success=False, data=[], error=str(e))
    
    def get_sports(self) -> OddsResponse:
        """Obtiene lista de deportes disponibles."""
        return self._make_request("/sports", {})
    
    def get_odds(
        self,
        sport: str,
        regions: str = "eu",
        markets: str = "h2h",
        odds_format: str = "decimal"
    ) -> OddsResponse:
        """
        Obtiene odds actuales para un deporte.
        
        Args:
            sport: Código del deporte (ej: soccer_spain_la_liga)
            regions: Región de bookmakers (eu, uk, us, au)
            markets: Mercado de apuestas (h2h, spreads, totals)
            odds_format: Formato de odds (decimal, american)
        """
        params = {
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        return self._make_request(f"/sports/{sport}/odds", params)
    
    def get_historical_odds(
        self,
        sport: str,
        date: str,
        regions: str = "eu",
        markets: str = "h2h",
        odds_format: str = "decimal"
    ) -> OddsResponse:
        """
        Obtiene odds históricas para una fecha específica.
        
        Args:
            sport: Código del deporte
            date: Fecha en formato ISO8601 (ej: 2025-10-20T12:00:00Z)
            regions: Región de bookmakers
            markets: Mercado de apuestas
            odds_format: Formato de odds
        """
        params = {
            "date": date,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        return self._make_request(f"/historical/sports/{sport}/odds", params)
    
    def get_historical_events(
        self,
        sport: str,
        date: str
    ) -> OddsResponse:
        """
        Obtiene eventos históricos para una fecha.
        
        Args:
            sport: Código del deporte
            date: Fecha en formato ISO8601
        """
        return self._make_request(f"/historical/sports/{sport}/events", {"date": date})
    
    def get_odds_for_league(
        self,
        league_id: int,
        date: str,
        historical: bool = True
    ) -> OddsResponse:
        """
        Obtiene odds para una liga usando el ID de API-Football.
        
        Args:
            league_id: ID de la liga en API-Football (140, 39, etc.)
            date: Fecha en formato ISO8601
            historical: Si usar endpoint histórico o actual
        """
        sport = self.LEAGUE_MAPPING.get(league_id)
        if not sport:
            return OddsResponse(
                success=False, 
                data=[], 
                error=f"Liga {league_id} no soportada"
            )
        
        if historical:
            return self.get_historical_odds(sport, date)
        else:
            return self.get_odds(sport)
    
    def extract_match_odds(
        self,
        odds_data: List[Dict],
        home_team: str,
        away_team: str,
        similarity_threshold: float = 0.7
    ) -> Optional[Dict[str, float]]:
        """
        Extrae las odds de un partido específico por nombres de equipo.
        
        Args:
            odds_data: Lista de datos de odds de la API
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            similarity_threshold: Umbral de similitud para matching
            
        Returns:
            Dict con home_odds, draw_odds, away_odds o None si no se encuentra
        """
        from difflib import SequenceMatcher
        
        def similarity(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()
        
        for event in odds_data:
            home_sim = similarity(event.get("home_team", ""), home_team)
            away_sim = similarity(event.get("away_team", ""), away_team)
            
            if home_sim >= similarity_threshold and away_sim >= similarity_threshold:
                # Encontrado el partido, extraer odds del primer bookmaker
                bookmakers = event.get("bookmakers", [])
                if bookmakers:
                    # Preferir bet365 o pinnacle si están disponibles
                    bm = next(
                        (b for b in bookmakers if b["key"] in ["bet365", "pinnacle"]),
                        bookmakers[0]
                    )
                    
                    for market in bm.get("markets", []):
                        if market["key"] == "h2h":
                            outcomes = {o["name"]: o["price"] for o in market["outcomes"]}
                            
                            return {
                                "home_odds": outcomes.get(event["home_team"], 0),
                                "draw_odds": outcomes.get("Draw", 0),
                                "away_odds": outcomes.get(event["away_team"], 0),
                                "bookmaker": bm["title"]
                            }
        
        return None

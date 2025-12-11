"""
Cliente HTTP para API-Football.

Este módulo proporciona una interfaz para interactuar con la API de API-Football.
Incluye rate limiting, manejo de errores y logging.
"""

import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

import requests
from loguru import logger

from ..utils.config import settings


class APIFootballError(Exception):
    """Excepción base para errores de API-Football."""
    pass


class RateLimitError(APIFootballError):
    """Error cuando se excede el límite de requests."""
    pass


class AuthenticationError(APIFootballError):
    """Error de autenticación con la API."""
    pass


@dataclass
class APIResponse:
    """Respuesta estructurada de la API."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    results: int = 0
    
    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> "APIResponse":
        """Crea APIResponse desde la respuesta JSON de la API."""
        errors = response.get("errors", {})
        
        if errors:
            error_msg = str(errors)
            return cls(success=False, error=error_msg)
        
        return cls(
            success=True,
            data=response.get("response", []),
            results=response.get("results", 0)
        )


class APIFootballClient:
    """
    Cliente para la API de API-Football.
    
    Attributes:
        base_url: URL base de la API
        api_key: Clave de API
        requests_per_minute: Límite de requests por minuto
    """
    
    BASE_URL = "https://v3.football.api-sports.io"
    REQUESTS_PER_MINUTE = 100  # Plan Pro
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Inicializa el cliente de API-Football.
        
        Args:
            api_key: Clave de API (usa settings si no se proporciona)
            base_url: URL base (usa default si no se proporciona)
        """
        self.api_key = api_key or settings.api_football_key
        self.base_url = base_url or self.BASE_URL
        
        # Control de rate limiting
        self._request_times: list[float] = []
        self._min_interval = 60.0 / self.REQUESTS_PER_MINUTE
        
        # Headers para todas las requests
        self._headers = {
            "x-apisports-key": self.api_key
        }
        
        # Sesión HTTP reutilizable
        self._session = requests.Session()
        self._session.headers.update(self._headers)
        
        logger.info(f"APIFootballClient inicializado: {self.base_url}")
    
    def _wait_for_rate_limit(self) -> None:
        """Espera si es necesario para respetar el rate limit."""
        now = time.time()
        
        # Limpiar requests antiguas (más de 1 minuto)
        self._request_times = [
            t for t in self._request_times 
            if now - t < 60
        ]
        
        # Si hay demasiadas requests recientes, esperar
        if len(self._request_times) >= self.REQUESTS_PER_MINUTE:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.warning(f"Rate limit alcanzado, esperando {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Registrar esta request
        self._request_times.append(time.time())
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        Realiza una request a la API.
        
        Args:
            endpoint: Endpoint de la API (ej: "/fixtures")
            params: Parámetros de query string
            
        Returns:
            APIResponse con los datos o error
            
        Raises:
            AuthenticationError: Si la API key es inválida
            RateLimitError: Si se excede el límite
            APIFootballError: Para otros errores
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Request: GET {url} params={params}")
            
            response = self._session.get(url, params=params, timeout=30)
            
            # Verificar headers de rate limit
            remaining = response.headers.get("x-ratelimit-requests-remaining")
            if remaining:
                logger.debug(f"Requests restantes hoy: {remaining}")
            
            # Manejar códigos de error HTTP
            if response.status_code == 401:
                raise AuthenticationError("API key inválida")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit excedido")
            elif response.status_code >= 400:
                raise APIFootballError(f"Error HTTP {response.status_code}")
            
            # Parsear respuesta JSON
            data = response.json()
            api_response = APIResponse.from_response(data)
            
            logger.debug(f"Respuesta: {api_response.results} resultados")
            
            return api_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión: {e}")
            raise APIFootballError(f"Error de conexión: {e}") from e
    
    def get_status(self) -> APIResponse:
        """
        Obtiene el estado de la cuenta y uso de API.
        
        Returns:
            APIResponse con información de la cuenta
        """
        return self._make_request("/status")
    
    def get_fixtures(
        self,
        date: Optional[str] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team: Optional[int] = None,
        fixture_id: Optional[int] = None,
        live: Optional[str] = None,
        next_n: Optional[int] = None,
        last_n: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene partidos/fixtures.
        
        Args:
            date: Fecha en formato YYYY-MM-DD
            league: ID de la liga
            season: Año de la temporada
            team: ID del equipo
            fixture_id: ID específico del partido
            live: "all" para partidos en vivo
            next_n: Próximos N partidos
            last_n: Últimos N partidos
            
        Returns:
            APIResponse con lista de fixtures
        """
        params = {}
        
        if date:
            params["date"] = date
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if team:
            params["team"] = team
        if fixture_id:
            params["id"] = fixture_id
        if live:
            params["live"] = live
        if next_n:
            params["next"] = next_n
        if last_n:
            params["last"] = last_n
        
        return self._make_request("/fixtures", params)
    
    def get_fixture_statistics(
        self,
        fixture_id: int,
        team: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene estadísticas de un partido.
        
        Args:
            fixture_id: ID del partido
            team: ID del equipo (opcional, para filtrar)
            
        Returns:
            APIResponse con estadísticas del partido
        """
        params = {"fixture": fixture_id}
        if team:
            params["team"] = team
        
        return self._make_request("/fixtures/statistics", params)
    
    def get_standings(
        self,
        league: int,
        season: int
    ) -> APIResponse:
        """
        Obtiene la clasificación de una liga.
        
        Args:
            league: ID de la liga
            season: Año de la temporada
            
        Returns:
            APIResponse con clasificación
        """
        params = {"league": league, "season": season}
        return self._make_request("/standings", params)
    
    def get_teams(
        self,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team_id: Optional[int] = None,
        name: Optional[str] = None
    ) -> APIResponse:
        """
        Obtiene información de equipos.
        
        Args:
            league: ID de la liga
            season: Año de la temporada
            team_id: ID específico del equipo
            name: Nombre del equipo (búsqueda)
            
        Returns:
            APIResponse con equipos
        """
        params = {}
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if team_id:
            params["id"] = team_id
        if name:
            params["name"] = name
        
        return self._make_request("/teams", params)
    
    def get_team_statistics(
        self,
        team: int,
        league: int,
        season: int
    ) -> APIResponse:
        """
        Obtiene estadísticas de temporada de un equipo.
        
        Args:
            team: ID del equipo
            league: ID de la liga
            season: Año de la temporada
            
        Returns:
            APIResponse con estadísticas del equipo
        """
        params = {"team": team, "league": league, "season": season}
        return self._make_request("/teams/statistics", params)
    
    def get_head_to_head(
        self,
        team1: int,
        team2: int,
        last_n: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene historial de enfrentamientos entre dos equipos.
        
        Args:
            team1: ID del primer equipo
            team2: ID del segundo equipo
            last_n: Últimos N enfrentamientos
            
        Returns:
            APIResponse con historial H2H
        """
        params = {"h2h": f"{team1}-{team2}"}
        if last_n:
            params["last"] = last_n
        
        return self._make_request("/fixtures/headtohead", params)
    
    def get_odds(
        self,
        fixture: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        bookmaker: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene cuotas de apuestas.
        
        Args:
            fixture: ID del partido
            league: ID de la liga
            season: Año de la temporada
            bookmaker: ID de la casa de apuestas
            
        Returns:
            APIResponse con cuotas
        """
        params = {}
        if fixture:
            params["fixture"] = fixture
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if bookmaker:
            params["bookmaker"] = bookmaker
        
        return self._make_request("/odds", params)
    
    def get_predictions(self, fixture: int) -> APIResponse:
        """
        Obtiene predicciones de la API para un partido.
        
        Args:
            fixture: ID del partido
            
        Returns:
            APIResponse con predicciones
        """
        return self._make_request("/predictions", {"fixture": fixture})
    
    def get_injuries(
        self,
        fixture: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene información de lesiones.
        
        Args:
            fixture: ID del partido
            league: ID de la liga
            season: Año de la temporada
            team: ID del equipo
            
        Returns:
            APIResponse con lesiones
        """
        params = {}
        if fixture:
            params["fixture"] = fixture
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if team:
            params["team"] = team
        
        return self._make_request("/injuries", params)
    
    def get_leagues(
        self,
        league_id: Optional[int] = None,
        country: Optional[str] = None,
        season: Optional[int] = None
    ) -> APIResponse:
        """
        Obtiene información de ligas.
        
        Args:
            league_id: ID específico de la liga
            country: País
            season: Año de la temporada
            
        Returns:
            APIResponse con ligas
        """
        params = {}
        if league_id:
            params["id"] = league_id
        if country:
            params["country"] = country
        if season:
            params["season"] = season
        
        return self._make_request("/leagues", params)
    
    def close(self) -> None:
        """Cierra la sesión HTTP."""
        self._session.close()
        logger.info("Sesión de APIFootballClient cerrada")
    
    def __enter__(self) -> "APIFootballClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

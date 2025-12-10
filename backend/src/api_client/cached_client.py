"""
Cliente de API-Football con caché integrado.

Combina el cliente HTTP con el sistema de caché para optimizar requests.
"""

from typing import Any, Dict, Optional

from loguru import logger

from .client import APIFootballClient, APIResponse
from .cache import APICache, CacheTTL


class CachedAPIClient(APIFootballClient):
    """
    Cliente de API-Football con caché automático.
    
    Extiende APIFootballClient añadiendo caché transparente.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa el cliente con caché."""
        super().__init__(*args, **kwargs)
        self.cache = APICache()
        
        logger.info("CachedAPIClient inicializado con caché")
    
    def _cached_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        ttl: int,
        force_refresh: bool = False
    ) -> APIResponse:
        """
        Realiza request con caché.
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de query
            ttl: Tiempo de vida del caché
            force_refresh: Si True, ignora caché existente
            
        Returns:
            APIResponse con datos
        """
        params = params or {}
        
        # Intentar obtener del caché
        if not force_refresh:
            cached_data = self.cache.get(endpoint, params)
            if cached_data is not None:
                return APIResponse(
                    success=True,
                    data=cached_data,
                    results=len(cached_data) if isinstance(cached_data, list) else 1
                )
        
        # Hacer request a la API
        response = self._make_request(endpoint, params)
        
        # Guardar en caché si fue exitoso
        if response.success and response.data:
            self.cache.set(endpoint, params, response.data, ttl)
        
        return response
    
    # Override de métodos con caché
    
    def get_leagues(
        self,
        league_id: Optional[int] = None,
        country: Optional[str] = None,
        season: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene ligas con caché."""
        params = {}
        if league_id:
            params["id"] = league_id
        if country:
            params["country"] = country
        if season:
            params["season"] = season
        
        return self._cached_request(
            "/leagues", params, CacheTTL.LEAGUES, force_refresh
        )
    
    def get_teams(
        self,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team_id: Optional[int] = None,
        name: Optional[str] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene equipos con caché."""
        params = {}
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if team_id:
            params["id"] = team_id
        if name:
            params["name"] = name
        
        return self._cached_request(
            "/teams", params, CacheTTL.TEAMS, force_refresh
        )
    
    def get_standings(
        self,
        league: int,
        season: int,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene clasificación con caché."""
        params = {"league": league, "season": season}
        
        return self._cached_request(
            "/standings", params, CacheTTL.STANDINGS, force_refresh
        )
    
    def get_team_statistics(
        self,
        team: int,
        league: int,
        season: int,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene estadísticas de equipo con caché."""
        params = {"team": team, "league": league, "season": season}
        
        return self._cached_request(
            "/teams/statistics", params, CacheTTL.TEAM_STATISTICS, force_refresh
        )
    
    def get_fixtures(
        self,
        date: Optional[str] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team: Optional[int] = None,
        fixture_id: Optional[int] = None,
        live: Optional[str] = None,
        next_n: Optional[int] = None,
        last_n: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene fixtures con caché."""
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
        
        # Live no debe cachearse
        if live:
            return self._make_request("/fixtures", params)
        
        return self._cached_request(
            "/fixtures", params, CacheTTL.FIXTURES, force_refresh
        )
    
    def get_fixture_statistics(
        self,
        fixture_id: int,
        team: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene estadísticas de partido con caché."""
        params = {"fixture": fixture_id}
        if team:
            params["team"] = team
        
        return self._cached_request(
            "/fixtures/statistics", params, CacheTTL.FIXTURE_STATISTICS, force_refresh
        )
    
    def get_head_to_head(
        self,
        team1: int,
        team2: int,
        last_n: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene H2H con caché."""
        params = {"h2h": f"{team1}-{team2}"}
        if last_n:
            params["last"] = last_n
        
        return self._cached_request(
            "/fixtures/headtohead", params, CacheTTL.HEAD_TO_HEAD, force_refresh
        )
    
    def get_odds(
        self,
        fixture: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        bookmaker: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene cuotas con caché."""
        params = {}
        if fixture:
            params["fixture"] = fixture
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if bookmaker:
            params["bookmaker"] = bookmaker
        
        return self._cached_request(
            "/odds", params, CacheTTL.ODDS, force_refresh
        )
    
    def get_predictions(
        self,
        fixture: int,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene predicciones con caché."""
        return self._cached_request(
            "/predictions", {"fixture": fixture}, CacheTTL.PREDICTIONS, force_refresh
        )
    
    def get_injuries(
        self,
        fixture: Optional[int] = None,
        league: Optional[int] = None,
        season: Optional[int] = None,
        team: Optional[int] = None,
        force_refresh: bool = False
    ) -> APIResponse:
        """Obtiene lesiones con caché."""
        params = {}
        if fixture:
            params["fixture"] = fixture
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if team:
            params["team"] = team
        
        return self._cached_request(
            "/injuries", params, CacheTTL.INJURIES, force_refresh
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché."""
        return self.cache.get_stats()
    
    def clear_cache(self) -> int:
        """Limpia todo el caché."""
        return self.cache.clear()
    
    def cleanup_cache(self) -> int:
        """Limpia entradas expiradas."""
        return self.cache.cleanup_expired()

"""
Cliente de API-Football.

Este paquete proporciona un cliente completo para interactuar con API-Football,
incluyendo caché automático y rate limiting.

Uso básico:
    from src.api_client import CachedAPIClient
    
    client = CachedAPIClient()
    response = client.get_fixtures(date="2024-12-10")
    
    if response.success:
        for fixture in response.data:
            print(fixture)
"""

from .client import (
    APIFootballClient,
    APIFootballError,
    AuthenticationError,
    RateLimitError,
    APIResponse,
)
from .cache import APICache, CacheTTL, CacheEntry
from .cached_client import CachedAPIClient


__all__ = [
    # Cliente principal
    "CachedAPIClient",
    "APIFootballClient",
    
    # Respuesta
    "APIResponse",
    
    # Excepciones
    "APIFootballError",
    "AuthenticationError",
    "RateLimitError",
    
    # Caché
    "APICache",
    "CacheTTL",
    "CacheEntry",
]

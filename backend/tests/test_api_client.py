"""
Tests para el cliente de API-Football.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Tests para APIResponse
class TestAPIResponse:
    """Tests para la clase APIResponse."""
    
    def test_from_response_success(self):
        """Test creación de APIResponse exitosa."""
        from src.api_client.client import APIResponse
        
        mock_response = {
            "response": [{"id": 1}, {"id": 2}],
            "results": 2,
            "errors": {}
        }
        
        result = APIResponse.from_response(mock_response)
        
        assert result.success is True
        assert result.results == 2
        assert len(result.data) == 2
        assert result.error is None
    
    def test_from_response_with_error(self):
        """Test creación de APIResponse con error."""
        from src.api_client.client import APIResponse
        
        mock_response = {
            "response": [],
            "results": 0,
            "errors": {"token": "Invalid API key"}
        }
        
        result = APIResponse.from_response(mock_response)
        
        assert result.success is False
        assert result.error is not None
        assert "Invalid" in result.error


class TestCacheEntry:
    """Tests para CacheEntry."""
    
    def test_cache_entry_not_expired(self):
        """Test que entrada reciente no está expirada."""
        from src.api_client.cache import CacheEntry
        import time
        
        entry = CacheEntry(
            data={"test": True},
            timestamp=time.time(),
            ttl=3600,
            endpoint="/test",
            params={}
        )
        
        assert entry.is_expired() is False
    
    def test_cache_entry_expired(self):
        """Test que entrada antigua está expirada."""
        from src.api_client.cache import CacheEntry
        import time
        
        entry = CacheEntry(
            data={"test": True},
            timestamp=time.time() - 7200,  # Hace 2 horas
            ttl=3600,  # TTL de 1 hora
            endpoint="/test",
            params={}
        )
        
        assert entry.is_expired() is True
    
    def test_cache_entry_serialization(self):
        """Test serialización de CacheEntry."""
        from src.api_client.cache import CacheEntry
        import time
        
        entry = CacheEntry(
            data={"test": True},
            timestamp=time.time(),
            ttl=3600,
            endpoint="/test",
            params={"id": 1}
        )
        
        # Serializar y deserializar
        data = entry.to_dict()
        restored = CacheEntry.from_dict(data)
        
        assert restored.endpoint == entry.endpoint
        assert restored.ttl == entry.ttl


class TestAPICache:
    """Tests para el sistema de caché."""
    
    def test_cache_set_and_get(self):
        """Test guardar y recuperar del caché."""
        from src.api_client.cache import APICache
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = APICache(cache_dir=Path(tmpdir))
            
            # Guardar
            cache.set("/test", {"id": 1}, {"data": "value"}, ttl=3600)
            
            # Recuperar
            result = cache.get("/test", {"id": 1})
            
            assert result is not None
            assert result["data"] == "value"
    
    def test_cache_miss(self):
        """Test cache miss cuando no hay datos."""
        from src.api_client.cache import APICache
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = APICache(cache_dir=Path(tmpdir))
            
            result = cache.get("/nonexistent", {})
            
            assert result is None
    
    def test_cache_clear(self):
        """Test limpiar caché."""
        from src.api_client.cache import APICache
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = APICache(cache_dir=Path(tmpdir))
            
            # Guardar varias entradas
            cache.set("/test1", {}, {"data": 1}, ttl=3600)
            cache.set("/test2", {}, {"data": 2}, ttl=3600)
            
            # Limpiar
            count = cache.clear()
            
            assert count == 2
            assert cache.get("/test1", {}) is None
            assert cache.get("/test2", {}) is None
    
    def test_cache_stats(self):
        """Test estadísticas del caché."""
        from src.api_client.cache import APICache
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = APICache(cache_dir=Path(tmpdir))
            
            cache.set("/test", {}, {"data": 1}, ttl=3600)
            cache.get("/test", {})  # Hit
            cache.get("/nonexistent", {})  # Miss
            
            stats = cache.get_stats()
            
            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["total_entries"] == 1


class TestCacheTTL:
    """Tests para valores de TTL."""
    
    def test_ttl_values(self):
        """Test que los TTL tienen valores razonables."""
        from src.api_client.cache import CacheTTL
        
        # Datos estáticos deben tener TTL largo
        assert CacheTTL.LEAGUES >= 86400
        assert CacheTTL.TEAMS >= 86400
        
        # Datos dinámicos TTL más corto
        assert CacheTTL.ODDS <= 3600
        assert CacheTTL.FIXTURES <= 7200


class TestAPIFootballClient:
    """Tests para el cliente HTTP."""
    
    @patch('src.api_client.client.requests.Session')
    def test_client_initialization(self, mock_session):
        """Test inicialización del cliente."""
        from src.api_client.client import APIFootballClient
        
        with patch.dict('os.environ', {'API_FOOTBALL_KEY': 'test_key'}):
            client = APIFootballClient(api_key="test_key")
            
            assert client.api_key == "test_key"
            assert client.base_url == "https://v3.football.api-sports.io"
    
    @patch('src.api_client.client.requests.Session')
    def test_get_status_endpoint(self, mock_session):
        """Test endpoint /status."""
        from src.api_client.client import APIFootballClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {"account": {"email": "test@test.com"}},
            "results": 1,
            "errors": {}
        }
        mock_response.headers = {}
        
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = APIFootballClient(api_key="test_key")
        result = client.get_status()
        
        assert result.success is True


class TestCachedAPIClient:
    """Tests para el cliente con caché."""
    
    def test_cached_client_inherits_methods(self):
        """Test que CachedAPIClient tiene todos los métodos."""
        from src.api_client.cached_client import CachedAPIClient
        
        # Verificar que tiene los métodos principales
        assert hasattr(CachedAPIClient, 'get_fixtures')
        assert hasattr(CachedAPIClient, 'get_standings')
        assert hasattr(CachedAPIClient, 'get_teams')
        assert hasattr(CachedAPIClient, 'get_odds')
        assert hasattr(CachedAPIClient, 'get_predictions')
        assert hasattr(CachedAPIClient, 'get_head_to_head')
        assert hasattr(CachedAPIClient, 'get_cache_stats')

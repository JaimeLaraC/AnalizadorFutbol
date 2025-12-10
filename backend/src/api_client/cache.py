"""
Sistema de caché para API-Football.

Almacena respuestas de la API para reducir requests y respetar límites.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from loguru import logger

from ..utils.config import settings


@dataclass
class CacheEntry:
    """Entrada de caché con metadatos."""
    
    data: Dict[str, Any]
    timestamp: float
    ttl: int  # Time to live en segundos
    endpoint: str
    params: Dict[str, Any]
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        return time.time() - self.timestamp > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Crea CacheEntry desde diccionario."""
        return cls(**data)


class CacheTTL:
    """Tiempos de vida por tipo de datos."""
    
    # Datos que cambian poco
    LEAGUES = 86400 * 7  # 7 días
    TEAMS = 86400 * 7  # 7 días
    
    # Datos que cambian cada día
    STANDINGS = 3600 * 6  # 6 horas
    TEAM_STATISTICS = 3600 * 12  # 12 horas
    
    # Datos que cambian frecuentemente
    FIXTURES = 3600  # 1 hora
    FIXTURE_STATISTICS = 3600 * 2  # 2 horas (post-partido no cambia)
    
    # Datos muy dinámicos
    ODDS = 1800  # 30 minutos
    PREDICTIONS = 3600  # 1 hora
    INJURIES = 3600 * 6  # 6 horas
    
    # Head to head (histórico, cambia poco)
    HEAD_TO_HEAD = 86400  # 1 día
    
    # Status de cuenta
    STATUS = 3600  # 1 hora


class APICache:
    """
    Sistema de caché basado en archivos JSON.
    
    Almacena respuestas de API en disco para reducir requests.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Inicializa el sistema de caché.
        
        Args:
            cache_dir: Directorio para almacenar caché
        """
        self.cache_dir = cache_dir or settings.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._stats = {
            "hits": 0,
            "misses": 0,
            "expired": 0
        }
        
        logger.info(f"APICache inicializado en: {self.cache_dir}")
    
    def _generate_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Genera una clave única para el endpoint y parámetros.
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la query
            
        Returns:
            Hash MD5 como clave
        """
        # Ordenar params para consistencia
        sorted_params = sorted(params.items()) if params else []
        key_string = f"{endpoint}:{json.dumps(sorted_params)}"
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Obtiene la ruta del archivo de caché."""
        return self.cache_dir / f"{key}.json"
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos del caché si existen y no han expirado.
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la query
            
        Returns:
            Datos cacheados o None si no hay/expiró
        """
        params = params or {}
        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self._stats["misses"] += 1
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                entry_data = json.load(f)
            
            entry = CacheEntry.from_dict(entry_data)
            
            if entry.is_expired():
                self._stats["expired"] += 1
                cache_path.unlink()  # Eliminar archivo expirado
                logger.debug(f"Cache expirado: {endpoint}")
                return None
            
            self._stats["hits"] += 1
            logger.debug(f"Cache hit: {endpoint}")
            return entry.data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error leyendo caché: {e}")
            cache_path.unlink(missing_ok=True)
            return None
    
    def set(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        data: Dict[str, Any],
        ttl: int
    ) -> None:
        """
        Almacena datos en caché.
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la query
            data: Datos a cachear
            ttl: Tiempo de vida en segundos
        """
        params = params or {}
        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl,
            endpoint=endpoint,
            params=params
        )
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, indent=2)
            
            logger.debug(f"Cache guardado: {endpoint} (TTL: {ttl}s)")
            
        except IOError as e:
            logger.error(f"Error guardando caché: {e}")
    
    def invalidate(
        self,
        endpoint: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> int:
        """
        Invalida entradas de caché.
        
        Args:
            endpoint: Endpoint específico a invalidar
            pattern: Patrón para buscar y eliminar
            
        Returns:
            Número de entradas eliminadas
        """
        count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry_data = json.load(f)
                
                entry = CacheEntry.from_dict(entry_data)
                
                should_delete = False
                if endpoint and entry.endpoint == endpoint:
                    should_delete = True
                elif pattern and pattern in entry.endpoint:
                    should_delete = True
                
                if should_delete:
                    cache_file.unlink()
                    count += 1
                    
            except Exception:
                pass
        
        logger.info(f"Caché invalidado: {count} entradas eliminadas")
        return count
    
    def clear(self) -> int:
        """
        Limpia todo el caché.
        
        Returns:
            Número de entradas eliminadas
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        
        self._stats = {"hits": 0, "misses": 0, "expired": 0}
        logger.info(f"Caché limpiado: {count} entradas eliminadas")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Elimina entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry_data = json.load(f)
                
                entry = CacheEntry.from_dict(entry_data)
                
                if entry.is_expired():
                    cache_file.unlink()
                    count += 1
                    
            except Exception:
                # Archivo corrupto, eliminar
                cache_file.unlink(missing_ok=True)
                count += 1
        
        logger.info(f"Limpieza de caché: {count} entradas expiradas eliminadas")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas
        """
        total_files = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(
            f.stat().st_size 
            for f in self.cache_dir.glob("*.json")
        )
        
        hit_rate = 0.0
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            hit_rate = self._stats["hits"] / total_requests * 100
        
        return {
            **self._stats,
            "total_entries": total_files,
            "total_size_mb": total_size / (1024 * 1024),
            "hit_rate_percent": round(hit_rate, 2)
        }

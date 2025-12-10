"""
Configuración del proyecto AnalizadorFutbol.

Carga variables de entorno y configuración general.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # API-Football
    api_football_key: str = Field(..., env="API_FOOTBALL_KEY")
    api_football_host: str = Field(
        default="v3.football.api-sports.io",
        env="API_FOOTBALL_HOST"
    )
    
    # Base de datos
    database_url: str = Field(
        default="postgresql://localhost:5432/analizador_futbol",
        env="DATABASE_URL"
    )
    
    # Aplicación
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Modelo
    confidence_threshold: float = Field(default=0.75)
    top_predictions: int = Field(default=5)
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    models_dir: Path = base_dir / "models" / "trained"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Obtiene la instancia de configuración."""
    return Settings()


# Instancia global
settings = get_settings()

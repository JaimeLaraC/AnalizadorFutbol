"""
Configuración de logging para el proyecto.

Usa loguru para logging estructurado.
"""

import sys
from loguru import logger

from .config import settings


def setup_logger():
    """Configura el logger de la aplicación."""
    
    # Remover handler por defecto
    logger.remove()
    
    # Formato personalizado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Handler para consola
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )
    
    # Handler para archivo (rotación diaria)
    logger.add(
        "logs/analizador_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",  # Nueva archivo cada día
        retention="30 days",  # Mantener 30 días
        compression="zip",
    )
    
    return logger


# Configurar logger al importar
setup_logger()

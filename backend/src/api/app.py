"""
Aplicación FastAPI principal.

Configura la aplicación con todos los routers y middleware.
"""

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .routers import predictions, stats, fixtures, sync
from .schemas import HealthCheck
from ..utils.config import settings
from ..db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para FastAPI."""
    logger.info("🚀 Iniciando aplicación...")
    
    # Inicializar base de datos (solo en desarrollo)
    if settings.debug:
        try:
            init_db()
            logger.info("✅ Base de datos inicializada")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando BD: {e}")
    
    yield
    
    logger.info("🛑 Cerrando aplicación...")


app = FastAPI(
    title="AnalizadorFutbol API",
    description="API de predicción de partidos de fútbol con IA",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# Health Check
# =====================================

@app.get("/", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Verifica el estado de la API."""
    from ..api_client import CachedAPIClient
    
    cache_stats = None
    try:
        client = CachedAPIClient()
        cache_stats = client.get_cache_stats()
    except Exception:
        pass
    
    return HealthCheck(
        status="ok",
        version="1.0.0",
        database="postgresql",
        cache_stats=cache_stats
    )


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health():
    """Alias de health check."""
    return await health_check()


# =====================================
# Incluir Routers
# =====================================

app.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"]
)

app.include_router(
    stats.router,
    prefix="/stats",
    tags=["Statistics"]
)

app.include_router(
    fixtures.router,
    prefix="/fixtures",
    tags=["Fixtures"]
)

app.include_router(
    sync.router,
    prefix="/sync",
    tags=["Sync"]
)


# =====================================
# Manejo de Errores
# =====================================

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de errores."""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

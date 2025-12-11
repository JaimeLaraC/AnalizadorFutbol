"""
Router de sincronización.

Endpoints para sincronizar datos desde API-Football.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from ..schemas import SyncRequest, SyncResponse
from ...db import get_db
from ...data import MasterCollector, TOP_LEAGUES


router = APIRouter()


@router.post("/season", response_model=SyncResponse)
async def sync_season(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Sincroniza una temporada completa.
    
    Ejecuta en background para no bloquear.
    """
    logger.info(f"Solicitud de sincronización: temporada {request.season}")
    
    league_ids = request.league_ids or list(TOP_LEAGUES.keys())
    
    def sync_task():
        with MasterCollector() as collector:
            collector.sync_full_season(
                season=request.season,
                league_ids=league_ids
            )
    
    background_tasks.add_task(sync_task)
    
    return SyncResponse(
        status="started",
        message=f"Sincronización de temporada {request.season} iniciada en background",
        details={"league_ids": league_ids}
    )


@router.post("/today", response_model=SyncResponse)
async def sync_today():
    """
    Sincroniza los partidos de hoy.
    """
    logger.info("Sincronizando partidos de hoy...")
    
    try:
        with MasterCollector() as collector:
            result = collector.sync_today_fixtures()
        
        return SyncResponse(
            status="completed",
            message=f"Sincronizados {result['fixtures']} partidos de hoy",
            details=result
        )
    except Exception as e:
        logger.error(f"Error sincronizando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/standings", response_model=SyncResponse)
async def sync_standings(
    season: int = 2024,
    league_ids: Optional[list[int]] = None
):
    """
    Actualiza clasificaciones de las ligas.
    """
    logger.info(f"Actualizando clasificaciones temporada {season}...")
    
    league_ids = league_ids or list(TOP_LEAGUES.keys())
    
    try:
        with MasterCollector() as collector:
            result = collector.update_standings(season, league_ids)
        
        return SyncResponse(
            status="completed",
            message=f"Actualizadas {result['total']} posiciones",
            details=result
        )
    except Exception as e:
        logger.error(f"Error actualizando standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SyncResponse)
async def get_sync_status():
    """
    Obtiene el estado del caché de la API.
    """
    try:
        with MasterCollector() as collector:
            stats = collector.get_collection_stats()
        
        return SyncResponse(
            status="ok",
            message="Estadísticas del caché",
            details=stats
        )
    except Exception as e:
        return SyncResponse(
            status="error",
            message=str(e)
        )

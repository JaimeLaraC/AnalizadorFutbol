"""
Router de fixtures.

Endpoints para obtener información de partidos.
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from ..schemas import FixtureInfo, UpcomingFixturesResponse
from ...db import get_db, FixtureRepository
from ...db.models import Fixture, Team, League


router = APIRouter()


def _fixture_to_info(fixture: Fixture, db: Session) -> FixtureInfo:
    """Convierte un Fixture a FixtureInfo."""
    home_team = db.query(Team).filter(Team.id == fixture.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == fixture.away_team_id).first()
    league = db.query(League).filter(League.id == fixture.league_id).first()
    
    return FixtureInfo(
        id=fixture.id,
        home_team_id=fixture.home_team_id,
        away_team_id=fixture.away_team_id,
        home_team_name=home_team.name if home_team else None,
        away_team_name=away_team.name if away_team else None,
        league_name=league.name if league else None,
        date=fixture.date,
        status=fixture.status or "NS"
    )


@router.get("/today", response_model=UpcomingFixturesResponse)
async def get_today_fixtures(
    db: Session = Depends(get_db)
):
    """
    Obtiene los partidos de hoy.
    """
    today = date.today()
    
    repo = FixtureRepository(db)
    fixtures = repo.get_by_date(today)
    
    fixture_infos = [_fixture_to_info(f, db) for f in fixtures]
    
    return UpcomingFixturesResponse(
        date=today,
        fixtures=fixture_infos
    )


@router.get("/upcoming", response_model=list[UpcomingFixturesResponse])
async def get_upcoming_fixtures(
    days: int = Query(default=3, le=7),
    db: Session = Depends(get_db)
):
    """
    Obtiene partidos de los próximos días.
    
    Args:
        days: Número de días a consultar
    """
    repo = FixtureRepository(db)
    results = []
    
    for i in range(days):
        target_date = date.today() + timedelta(days=i)
        fixtures = repo.get_by_date(target_date)
        
        if fixtures:
            fixture_infos = [_fixture_to_info(f, db) for f in fixtures]
            results.append(UpcomingFixturesResponse(
                date=target_date,
                fixtures=fixture_infos
            ))
    
    return results


@router.get("/date/{target_date}", response_model=UpcomingFixturesResponse)
async def get_fixtures_by_date(
    target_date: date,
    db: Session = Depends(get_db)
):
    """
    Obtiene partidos de una fecha específica.
    
    Args:
        target_date: Fecha en formato YYYY-MM-DD
    """
    repo = FixtureRepository(db)
    fixtures = repo.get_by_date(target_date)
    
    fixture_infos = [_fixture_to_info(f, db) for f in fixtures]
    
    return UpcomingFixturesResponse(
        date=target_date,
        fixtures=fixture_infos
    )


@router.get("/league/{league_id}", response_model=list[FixtureInfo])
async def get_fixtures_by_league(
    league_id: int,
    season: int = Query(default=2024),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    Obtiene partidos de una liga y temporada.
    
    Args:
        league_id: ID de la liga
        season: Año de la temporada
        limit: Máximo de partidos
    """
    repo = FixtureRepository(db)
    fixtures = repo.get_by_league_season(league_id, season)
    
    fixtures = fixtures[:limit]
    
    return [_fixture_to_info(f, db) for f in fixtures]

"""
Router de predicciones.

Endpoints para obtener predicciones del día y históricas.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from ..schemas import (
    PredictionDetail, PredictionResponse, Top5Response
)
from ...db import get_db, PredictionRepository, FixtureRepository
from ...db.models import Prediction, Fixture, Team, League


router = APIRouter()


def _prediction_to_detail(
    prediction: Prediction,
    db: Session
) -> PredictionDetail:
    """Convierte un modelo Prediction a PredictionDetail."""
    fixture = prediction.fixture
    
    # Obtener nombres de equipos
    home_team = db.query(Team).filter(Team.id == fixture.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == fixture.away_team_id).first()
    league = db.query(League).filter(League.id == fixture.league_id).first()
    
    return PredictionDetail(
        fixture_id=prediction.fixture_id,
        predicted_winner=prediction.predicted_winner,
        probability_home=prediction.probability_home,
        probability_away=prediction.probability_away,
        confidence=prediction.confidence,
        home_team_name=home_team.name if home_team else None,
        away_team_name=away_team.name if away_team else None,
        home_team_logo=home_team.logo if home_team else None,
        away_team_logo=away_team.logo if away_team else None,
        league_name=league.name if league else None,
        match_date=fixture.date,
        odds_home=prediction.odds_home,
        odds_draw=prediction.odds_draw,
        odds_away=prediction.odds_away,
        api_predicted_winner=prediction.api_predicted_winner,
        api_advice=prediction.api_advice,
        actual_result=prediction.actual_result,
        is_correct=prediction.is_correct,
        rank_of_day=prediction.rank_of_day,
        is_top_5=prediction.is_top_5
    )


@router.get("/today", response_model=Top5Response)
async def get_today_predictions(
    db: Session = Depends(get_db)
):
    """
    Obtiene las Top 5 predicciones de hoy.
    
    Las predicciones están ordenadas por confianza descendente.
    """
    today = date.today()
    
    repo = PredictionRepository(db)
    predictions = repo.get_top_5_by_date(today)
    
    details = [_prediction_to_detail(p, db) for p in predictions]
    
    return Top5Response(
        date=today,
        predictions=details,
        model_version="1.0.0"
    )


@router.get("/date/{target_date}", response_model=PredictionResponse)
async def get_predictions_by_date(
    target_date: date,
    limit: int = Query(default=50, le=100),
    min_confidence: float = Query(default=0.0, ge=0, le=1),
    db: Session = Depends(get_db)
):
    """
    Obtiene predicciones de una fecha específica.
    
    Args:
        target_date: Fecha en formato YYYY-MM-DD
        limit: Máximo de predicciones a retornar
        min_confidence: Confianza mínima
    """
    repo = PredictionRepository(db)
    predictions = repo.get_predictions_by_date(target_date)
    
    # Filtrar por confianza
    if min_confidence > 0:
        predictions = [p for p in predictions if p.confidence >= min_confidence]
    
    # Limitar
    predictions = predictions[:limit]
    
    details = [_prediction_to_detail(p, db) for p in predictions]
    
    return PredictionResponse(
        date=target_date,
        total=len(details),
        predictions=details
    )


@router.get("/history", response_model=List[PredictionResponse])
async def get_prediction_history(
    days: int = Query(default=7, le=30),
    top_5_only: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    """
    Obtiene historial de predicciones.
    
    Args:
        days: Número de días hacia atrás
        top_5_only: Si solo incluir las Top 5 de cada día
    """
    repo = PredictionRepository(db)
    
    results = []
    end_date = date.today()
    
    for i in range(days):
        target_date = end_date - timedelta(days=i)
        
        if top_5_only:
            predictions = repo.get_top_5_by_date(target_date)
        else:
            predictions = repo.get_predictions_by_date(target_date)
        
        if predictions:
            details = [_prediction_to_detail(p, db) for p in predictions]
            results.append(PredictionResponse(
                date=target_date,
                total=len(details),
                predictions=details
            ))
    
    return results


@router.get("/{prediction_id}", response_model=PredictionDetail)
async def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalle de una predicción específica.
    
    Args:
        prediction_id: ID de la predicción
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Predicción no encontrada")
    
    return _prediction_to_detail(prediction, db)

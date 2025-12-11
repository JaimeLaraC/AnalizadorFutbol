"""
Router de estadísticas.

Endpoints para obtener métricas y estadísticas del modelo.
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from loguru import logger

from ..schemas import (
    AccuracyStats, ModelMetrics, DailyStats, StatsResponse
)
from ...db import get_db, PredictionRepository
from ...models import EnsemblePredictor
from ...utils.config import settings


router = APIRouter()


@router.get("/accuracy", response_model=AccuracyStats)
async def get_accuracy_stats(
    days: int = Query(default=30, le=365),
    top_5_only: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de precisión del modelo.
    
    Args:
        days: Días a considerar
        top_5_only: Si solo considerar Top 5
    """
    repo = PredictionRepository(db)
    
    start_date = date.today() - timedelta(days=days)
    
    stats = repo.get_accuracy_stats(
        start_date=start_date,
        top_5_only=top_5_only
    )
    
    # Calcular ROI estimado
    accuracy = stats.get("accuracy", 0)
    total = stats.get("total", 0)
    correct = stats.get("correct", 0)
    
    # ROI con cuota promedio de 1.9
    avg_odds = 1.9
    if total > 0:
        profit = (correct * avg_odds) - total
        roi = profit / total * 100
    else:
        profit = 0
        roi = 0
    
    return AccuracyStats(
        total_predictions=total,
        correct=correct,
        accuracy=accuracy,
        roi_percent=roi,
        profit=profit
    )


@router.get("/model", response_model=ModelMetrics)
async def get_model_metrics():
    """
    Obtiene las métricas del modelo actual.
    """
    try:
        # Intentar cargar modelo guardado
        model_path = settings.models_dir / "ensemble_model.pkl"
        
        if model_path.exists():
            predictor = EnsemblePredictor()
            predictor.load(model_path)
            
            metrics = predictor.get_metrics()
            
            return ModelMetrics(
                accuracy=metrics.get("accuracy", 0),
                precision=metrics.get("precision", 0),
                recall=metrics.get("recall", 0),
                f1_score=metrics.get("f1", 0),
                roc_auc=metrics.get("roc_auc", 0),
                brier_score=metrics.get("brier_score", 0),
                trained_at=predictor.metadata.get("trained_at"),
                model_version=predictor.metadata.get("version", "1.0.0")
            )
        else:
            # Métricas por defecto
            return ModelMetrics(
                accuracy=0,
                precision=0,
                recall=0,
                f1_score=0,
                roc_auc=0,
                brier_score=0,
                model_version="not_trained"
            )
            
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return ModelMetrics(
            accuracy=0,
            precision=0,
            recall=0,
            f1_score=0,
            roc_auc=0,
            brier_score=0,
            model_version="error"
        )


@router.get("/daily", response_model=list[DailyStats])
async def get_daily_stats(
    days: int = Query(default=14, le=60),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas diarias de los últimos N días.
    """
    repo = PredictionRepository(db)
    results = []
    
    for i in range(days):
        target_date = date.today() - timedelta(days=i)
        predictions = repo.get_top_5_by_date(target_date)
        
        if predictions:
            correct = sum(1 for p in predictions if p.is_correct)
            total = len(predictions)
            
            results.append(DailyStats(
                date=target_date,
                total_predictions=total,
                correct=correct,
                accuracy=correct / total if total > 0 else 0,
                avg_confidence=sum(p.confidence for p in predictions) / total
            ))
    
    return results


@router.get("/", response_model=StatsResponse)
async def get_all_stats(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las estadísticas combinadas.
    """
    accuracy = await get_accuracy_stats(days=days, db=db)
    model = await get_model_metrics()
    daily = await get_daily_stats(days=min(days, 14), db=db)
    
    return StatsResponse(
        overall=accuracy,
        model_metrics=model,
        daily_stats=daily
    )

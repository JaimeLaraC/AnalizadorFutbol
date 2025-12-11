"""
Schemas Pydantic para la API.

Define los modelos de entrada/salida para los endpoints.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# =====================================
# Schemas de Predicciones
# =====================================

class PredictionBase(BaseModel):
    """Predicción básica."""
    
    fixture_id: int
    predicted_winner: int = Field(..., description="1=home, 2=away")
    probability_home: float = Field(..., ge=0, le=1)
    probability_away: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)


class PredictionDetail(PredictionBase):
    """Predicción con detalles del partido."""
    
    home_team_name: Optional[str] = None
    away_team_name: Optional[str] = None
    home_team_logo: Optional[str] = None
    away_team_logo: Optional[str] = None
    league_name: Optional[str] = None
    match_date: Optional[datetime] = None
    
    # Cuotas
    odds_home: Optional[float] = None
    odds_draw: Optional[float] = None
    odds_away: Optional[float] = None
    
    # Predicción API-Football
    api_predicted_winner: Optional[int] = None
    api_advice: Optional[str] = None
    
    # Resultado (si ya terminó)
    actual_result: Optional[int] = None
    is_correct: Optional[bool] = None
    
    # Ranking
    rank_of_day: Optional[int] = None
    is_top_5: bool = False


class PredictionResponse(BaseModel):
    """Respuesta con lista de predicciones."""
    
    date: date
    total: int
    predictions: List[PredictionDetail]


class Top5Response(BaseModel):
    """Respuesta con Top 5 del día."""
    
    date: date
    predictions: List[PredictionDetail]
    model_version: Optional[str] = None


# =====================================
# Schemas de Estadísticas
# =====================================

class AccuracyStats(BaseModel):
    """Estadísticas de precisión del modelo."""
    
    total_predictions: int
    correct: int
    accuracy: float
    
    # Por confianza
    accuracy_75_plus: Optional[float] = None
    accuracy_80_plus: Optional[float] = None
    
    # ROI
    roi_percent: Optional[float] = None
    profit: Optional[float] = None


class ModelMetrics(BaseModel):
    """Métricas del modelo actual."""
    
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    brier_score: float
    
    trained_at: Optional[datetime] = None
    model_version: str


class DailyStats(BaseModel):
    """Estadísticas diarias."""
    
    date: date
    total_predictions: int
    correct: int
    accuracy: float
    avg_confidence: float


class StatsResponse(BaseModel):
    """Respuesta de estadísticas."""
    
    overall: AccuracyStats
    model_metrics: ModelMetrics
    daily_stats: List[DailyStats]


# =====================================
# Schemas de Fixtures
# =====================================

class FixtureInfo(BaseModel):
    """Información de un partido."""
    
    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: Optional[str] = None
    away_team_name: Optional[str] = None
    league_name: Optional[str] = None
    date: datetime
    status: str


class UpcomingFixturesResponse(BaseModel):
    """Respuesta de próximos partidos."""
    
    date: date
    fixtures: List[FixtureInfo]


# =====================================
# Schemas de Sincronización
# =====================================

class SyncRequest(BaseModel):
    """Request para sincronización."""
    
    season: int
    league_ids: Optional[List[int]] = None
    force_refresh: bool = False


class SyncResponse(BaseModel):
    """Respuesta de sincronización."""
    
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


# =====================================
# Schemas Generales
# =====================================

class HealthCheck(BaseModel):
    """Health check response."""
    
    status: str = "ok"
    version: str
    database: str
    cache_stats: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Respuesta de error."""
    
    error: str
    detail: Optional[str] = None

"""
Router de entrenamiento del modelo ML.

Endpoints para recopilar datos, generar features y entrenar modelos.
"""

import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


# =====================================
# Estado Global del Proceso
# =====================================

class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingState:
    """Estado global del proceso de entrenamiento."""
    
    def __init__(self):
        self.status: TaskStatus = TaskStatus.IDLE
        self.current_task: Optional[str] = None
        self.progress: int = 0
        self.logs: List[str] = []
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def start(self, task_name: str):
        self.status = TaskStatus.RUNNING
        self.current_task = task_name
        self.progress = 0
        self.logs = []
        self.error = None
        self.started_at = datetime.now()
        self.completed_at = None
        self.result = None
        self.log(f"🚀 Iniciando: {task_name}")
    
    def complete(self, result: Optional[Dict] = None):
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.completed_at = datetime.now()
        self.result = result
        self.log(f"✅ Completado: {self.current_task}")
    
    def fail(self, error: str):
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
        self.log(f"❌ Error: {error}")
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "current_task": self.current_task,
            "progress": self.progress,
            "logs": self.logs[-50:],  # Últimos 50 logs
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result
        }


# Estado global
training_state = TrainingState()


# =====================================
# Schemas
# =====================================

class CollectRequest(BaseModel):
    seasons: List[int] = [2023, 2024]
    leagues: Optional[List[int]] = None  # None = todas las configuradas


class FeaturesRequest(BaseModel):
    min_matches: int = 5  # Mínimo de partidos para incluir equipo
    include_h2h: bool = True
    include_form: bool = True
    include_standings: bool = True


class TrainRequest(BaseModel):
    test_size: float = 0.2
    calibrate: bool = True
    use_xgboost: bool = True
    use_lightgbm: bool = True


class StatusResponse(BaseModel):
    status: str
    current_task: Optional[str]
    progress: int
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


# =====================================
# Background Tasks
# =====================================

def run_collect_task(seasons: List[int], leagues: Optional[List[int]]):
    """Ejecuta la recopilación de datos en background."""
    try:
        training_state.log(f"📥 Recopilando temporadas: {seasons}")
        
        # Importar componentes usando imports absolutos
        from src.data import MasterCollector, TOP_LEAGUES
        from src.api_client import CachedAPIClient
        
        # Obtener ligas objetivo
        configured_leagues = list(TOP_LEAGUES.keys())
        target_leagues = leagues or configured_leagues
        
        training_state.log(f"🏟️ Ligas seleccionadas: {len(target_leagues)}")
        
        client = CachedAPIClient()
        collector = MasterCollector(client)
        
        total_fixtures = 0
        total_teams = 0
        
        for i, season in enumerate(seasons):
            training_state.progress = int(((i + 1) / len(seasons)) * 80)
            training_state.log(f"📅 Temporada {season}/{season+1}:")
            
            try:
                result = collector.sync_full_season(
                    season=season,
                    league_ids=target_leagues,
                    include_standings=True
                )
                
                fixtures = result.get("totals", {}).get("fixtures", 0)
                teams = result.get("totals", {}).get("teams", 0)
                total_fixtures += fixtures
                total_teams += teams
                
                training_state.log(f"   ✅ {teams} equipos, {fixtures} partidos")
                
                if result.get("errors"):
                    for err in result["errors"][:3]:
                        training_state.log(f"   ⚠️ {err[:50]}")
                        
            except Exception as e:
                training_state.log(f"   ❌ Error: {str(e)[:50]}")
        
        training_state.progress = 100
        collector.close()
        
        training_state.complete({
            "total_fixtures": total_fixtures,
            "total_teams": total_teams,
            "leagues": len(target_leagues),
            "seasons": seasons
        })
        
    except Exception as e:
        training_state.fail(str(e))


def run_features_task(min_matches: int):
    """Genera el dataset de features en background."""
    try:
        training_state.log("⚙️ Generando features...")
        
        from src.data.features import FeaturePipeline
        from src.db import get_db_session, Fixture
        
        # Contar partidos disponibles
        with get_db_session() as db:
            total = db.query(Fixture).filter(Fixture.status == "FT").count()
        
        training_state.log(f"📊 Partidos terminados en BD: {total}")
        
        if total < 100:
            training_state.fail(f"Insuficientes partidos ({total}). Mínimo 100 requeridos.")
            return
        
        training_state.progress = 20
        training_state.log("🔧 Inicializando pipeline de features...")
        
        pipeline = FeaturePipeline()
        
        training_state.progress = 40
        training_state.log("📐 Calculando features por partido...")
        
        df = pipeline.generate_training_dataset(exclude_draws=True)
        
        training_state.progress = 80
        training_state.log(f"💾 Dataset generado: {len(df)} filas, {len(df.columns)} columnas")
        
        # Guardar dataset
        output_path = "data/training_data.csv"
        df.to_csv(output_path, index=False)
        
        training_state.complete({
            "rows": len(df),
            "columns": len(df.columns),
            "features": list(df.columns),
            "output_path": output_path
        })
        
    except Exception as e:
        training_state.fail(str(e))


def run_train_task(test_size: float, calibrate: bool):
    """Entrena el modelo en background."""
    try:
        training_state.log("🤖 Iniciando entrenamiento...")
        
        from src.models import ModelTrainer
        from src.models.ensemble_predictor import EnsemblePredictor
        import pandas as pd
        
        # Cargar dataset
        training_state.progress = 10
        training_state.log("📂 Cargando dataset...")
        
        try:
            df = pd.read_csv("data/training_data.csv")
        except FileNotFoundError:
            training_state.fail("Dataset no encontrado. Ejecuta 'Generar Features' primero.")
            return
        
        training_state.log(f"   {len(df)} muestras cargadas")
        
        if len(df) < 50:
            training_state.fail(f"Dataset muy pequeño ({len(df)} muestras). Se necesitan al menos 50.")
            return
        
        # Crear predictor con calibración
        training_state.progress = 30
        training_state.log("🏋️ Entrenando XGBoost...")
        
        predictor = EnsemblePredictor(use_calibration=calibrate)
        trainer = ModelTrainer(predictor=predictor)
        
        training_state.progress = 50
        training_state.log("🏋️ Entrenando LightGBM...")
        
        # Entrenar (save_model=True guarda automáticamente)
        metrics = trainer.train(df, save_model=True)
        
        training_state.progress = 90
        training_state.log("💾 Modelo guardado")
        
        training_state.complete({
            "accuracy": metrics.get("accuracy", 0),
            "precision": metrics.get("precision", 0),
            "recall": metrics.get("recall", 0),
            "f1_score": metrics.get("f1_score", metrics.get("f1", 0)),
            "samples": len(df)
        })
        
    except Exception as e:
        training_state.fail(str(e))


# =====================================
# Endpoints
# =====================================

@router.get("/status")
async def get_training_status():
    """Obtiene el estado actual del proceso de entrenamiento."""
    return training_state.to_dict()


@router.get("/logs")
async def get_training_logs(limit: int = 50):
    """Obtiene los últimos logs del proceso."""
    return {
        "logs": training_state.logs[-limit:],
        "status": training_state.status.value
    }


@router.post("/collect")
async def start_collect(request: CollectRequest, background_tasks: BackgroundTasks):
    """
    Inicia la recopilación de datos históricos.
    
    - seasons: Lista de temporadas a recopilar [2023, 2024]
    - leagues: Lista de IDs de ligas (opcional, default = top 5)
    """
    if training_state.status == TaskStatus.RUNNING:
        raise HTTPException(400, "Ya hay un proceso en ejecución")
    
    training_state.start("Recopilación de Datos")
    
    # Ejecutar en thread separado para no bloquear
    thread = threading.Thread(
        target=run_collect_task,
        args=(request.seasons, request.leagues)
    )
    thread.start()
    
    return {
        "message": "Recopilación iniciada",
        "seasons": request.seasons
    }


@router.post("/features")
async def start_features(request: FeaturesRequest, background_tasks: BackgroundTasks):
    """
    Genera el dataset de features para entrenamiento.
    
    - min_matches: Mínimo de partidos históricos por equipo
    """
    if training_state.status == TaskStatus.RUNNING:
        raise HTTPException(400, "Ya hay un proceso en ejecución")
    
    training_state.start("Generación de Features")
    
    thread = threading.Thread(
        target=run_features_task,
        args=(request.min_matches,)
    )
    thread.start()
    
    return {
        "message": "Generación de features iniciada"
    }


@router.post("/train")
async def start_training(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    Inicia el entrenamiento del modelo.
    
    - test_size: Proporción de datos para test (0.2 = 20%)
    - calibrate: Si calibrar probabilidades con Platt Scaling
    """
    if training_state.status == TaskStatus.RUNNING:
        raise HTTPException(400, "Ya hay un proceso en ejecución")
    
    training_state.start("Entrenamiento del Modelo")
    
    thread = threading.Thread(
        target=run_train_task,
        args=(request.test_size, request.calibrate)
    )
    thread.start()
    
    return {
        "message": "Entrenamiento iniciado"
    }


@router.post("/cancel")
async def cancel_training():
    """Cancela el proceso actual (si es posible)."""
    if training_state.status != TaskStatus.RUNNING:
        raise HTTPException(400, "No hay proceso en ejecución")
    
    training_state.fail("Cancelado por el usuario")
    return {"message": "Proceso cancelado"}


@router.delete("/reset")
async def reset_state():
    """Resetea el estado del proceso."""
    global training_state
    training_state = TrainingState()
    return {"message": "Estado reseteado"}

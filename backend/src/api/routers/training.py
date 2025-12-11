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


class TrainRequest(BaseModel):
    test_size: float = 0.2
    calibrate: bool = True


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
        
        # Importar componentes
        from ..data.collector import HistoricalCollector
        from ..api_client import CachedAPIClient
        
        client = CachedAPIClient()
        collector = HistoricalCollector(client)
        
        # Obtener ligas configuradas
        configured_leagues = [
            140,  # La Liga
            39,   # Premier League
            135,  # Serie A
            78,   # Bundesliga
            61,   # Ligue 1
        ]
        
        target_leagues = leagues or configured_leagues
        total_fixtures = 0
        
        for i, league_id in enumerate(target_leagues):
            training_state.progress = int((i / len(target_leagues)) * 100)
            training_state.log(f"📊 Liga {league_id}: recopilando...")
            
            for season in seasons:
                try:
                    fixtures = collector.collect_league_season(league_id, season)
                    total_fixtures += len(fixtures) if fixtures else 0
                    training_state.log(f"   Temporada {season}: {len(fixtures) if fixtures else 0} partidos")
                except Exception as e:
                    training_state.log(f"   ⚠️ Error en {league_id}/{season}: {str(e)[:50]}")
        
        training_state.complete({
            "total_fixtures": total_fixtures,
            "leagues": len(target_leagues),
            "seasons": seasons
        })
        
    except Exception as e:
        training_state.fail(str(e))


def run_features_task(min_matches: int):
    """Genera el dataset de features en background."""
    try:
        training_state.log("⚙️ Generando features...")
        
        from ..data.features import FeaturePipeline
        from ..db import get_db_session, FixtureRepository
        
        # Contar partidos disponibles
        with get_db_session() as db:
            repo = FixtureRepository(db)
            total = db.query(repo.model).filter(repo.model.status == "FT").count()
        
        training_state.log(f"📊 Partidos terminados en BD: {total}")
        
        if total < 100:
            training_state.fail(f"Insuficientes partidos ({total}). Mínimo 100 requeridos.")
            return
        
        training_state.progress = 20
        training_state.log("🔧 Inicializando pipeline de features...")
        
        pipeline = FeaturePipeline()
        
        training_state.progress = 40
        training_state.log("📐 Calculando features por partido...")
        
        df = pipeline.build_training_dataset(min_matches=min_matches)
        
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
        
        from ..models import ModelTrainer
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
        
        # Entrenar
        training_state.progress = 30
        training_state.log("🏋️ Entrenando XGBoost...")
        
        trainer = ModelTrainer()
        
        training_state.progress = 50
        training_state.log("🏋️ Entrenando LightGBM...")
        
        metrics = trainer.train(df, test_size=test_size, calibrate=calibrate)
        
        training_state.progress = 90
        training_state.log("💾 Guardando modelo...")
        
        trainer.save()
        
        training_state.complete({
            "accuracy": metrics.get("accuracy", 0),
            "precision": metrics.get("precision", 0),
            "recall": metrics.get("recall", 0),
            "f1_score": metrics.get("f1_score", 0),
            "model_version": metrics.get("version", "v1")
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

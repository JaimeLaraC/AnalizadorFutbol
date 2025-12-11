"""
Scheduler de tareas automáticas.

Programa la ejecución de tareas diarias usando APScheduler.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Callable, List
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from ..data import MasterCollector, FeaturePipeline, TOP_LEAGUES
from ..models import EnsemblePredictor, ModelTrainer
from ..db import get_db_session, PredictionRepository, FixtureRepository
from ..utils.config import settings


class PredictionScheduler:
    """
    Scheduler para tareas automáticas de predicción.
    
    Tareas programadas:
    - 06:00: Sincronizar fixtures del día
    - 08:00: Generar predicciones Top 5
    - 23:00: Verificar resultados
    """
    
    def __init__(self):
        """Inicializa el scheduler."""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        self._setup_jobs()
    
    def _setup_jobs(self) -> None:
        """Configura los jobs programados."""
        # Job 1: Sincronizar fixtures (06:00)
        self.scheduler.add_job(
            self.sync_daily_fixtures,
            CronTrigger(hour=6, minute=0),
            id="sync_fixtures",
            name="Sincronizar fixtures del día",
            replace_existing=True
        )
        
        # Job 2: Generar predicciones (08:00)
        self.scheduler.add_job(
            self.generate_daily_predictions,
            CronTrigger(hour=8, minute=0),
            id="generate_predictions",
            name="Generar predicciones Top 5",
            replace_existing=True
        )
        
        # Job 3: Verificar resultados (23:00)
        self.scheduler.add_job(
            self.verify_predictions,
            CronTrigger(hour=23, minute=0),
            id="verify_predictions",
            name="Verificar resultados",
            replace_existing=True
        )
        
        # Job 4: Actualizar standings (cada 6 horas)
        self.scheduler.add_job(
            self.update_standings,
            IntervalTrigger(hours=6),
            id="update_standings",
            name="Actualizar clasificaciones",
            replace_existing=True
        )
        
        logger.info("Jobs programados configurados")
    
    def start(self) -> None:
        """Inicia el scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("🚀 Scheduler iniciado")
    
    def stop(self) -> None:
        """Detiene el scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🛑 Scheduler detenido")
    
    def sync_daily_fixtures(self) -> None:
        """Sincroniza los fixtures del día."""
        logger.info("📅 Sincronizando fixtures del día...")
        
        try:
            with MasterCollector() as collector:
                result = collector.sync_today_fixtures()
            
            logger.info(f"✅ Sincronizados {result['fixtures']} fixtures")
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando fixtures: {e}")
    
    def generate_daily_predictions(self) -> None:
        """Genera las predicciones Top 5 del día."""
        logger.info("🎯 Generando predicciones del día...")
        
        try:
            today = date.today()
            
            # Obtener fixtures del día
            with get_db_session() as db:
                repo = FixtureRepository(db)
                fixtures = repo.get_pending_fixtures(today)
            
            if not fixtures:
                logger.warning("No hay fixtures pendientes para hoy")
                return
            
            logger.info(f"Encontrados {len(fixtures)} fixtures pendientes")
            
            # Cargar modelo
            model_path = settings.models_dir / "ensemble_model.pkl"
            if not model_path.exists():
                logger.error("Modelo no encontrado. Por favor entrena el modelo primero.")
                return
            
            predictor = EnsemblePredictor()
            predictor.load(model_path)
            
            # Generar features
            pipeline = FeaturePipeline()
            match_features = pipeline.generate_prediction_features(fixtures)
            
            if not match_features:
                logger.warning("No se pudieron generar features")
                return
            
            # Crear DataFrame de features
            import pandas as pd
            
            data = []
            for mf in match_features:
                row = {"fixture_id": mf.fixture_id, **mf.features}
                data.append(row)
            
            df = pd.DataFrame(data)
            fixture_ids = df["fixture_id"].values
            X = df.drop(columns=["fixture_id"])
            X = X.fillna(0)
            
            # Predecir
            preds_df = predictor.get_predictions_with_confidence(
                X, min_confidence=0.75
            )
            
            if len(preds_df) == 0:
                logger.warning("No hay predicciones con confianza >= 75%")
                return
            
            # Guardar Top 5
            top_5 = preds_df.head(5)
            
            with get_db_session() as db:
                pred_repo = PredictionRepository(db)
                
                for rank, (idx, row) in enumerate(top_5.iterrows(), 1):
                    fixture_id = fixture_ids[idx]
                    
                    prediction_data = {
                        "fixture_id": int(fixture_id),
                        "predicted_winner": int(row["predicted_winner"]),
                        "probability_home": float(row["prob_home"]),
                        "probability_away": float(row["prob_away"]),
                        "confidence": float(row["confidence"]),
                        "is_top_5": True,
                        "rank_of_day": rank,
                        "model_version": predictor.metadata.get("version", "1.0.0")
                    }
                    
                    pred_repo.create(prediction_data)
                
                db.commit()
            
            logger.info(f"✅ Generadas {len(top_5)} predicciones Top 5")
            
        except Exception as e:
            logger.error(f"❌ Error generando predicciones: {e}")
    
    def verify_predictions(self) -> None:
        """Verifica los resultados de las predicciones."""
        logger.info("🔍 Verificando resultados...")
        
        try:
            # Sincronizar resultados de ayer
            yesterday = date.today() - timedelta(days=1)
            
            with MasterCollector() as collector:
                collector.fixtures.sync_fixtures_by_date(yesterday)
            
            # Verificar predicciones
            with get_db_session() as db:
                pred_repo = PredictionRepository(db)
                fixture_repo = FixtureRepository(db)
                
                unverified = pred_repo.get_unverified()
                verified_count = 0
                
                for prediction in unverified:
                    fixture = fixture_repo.get_by_id(prediction.fixture_id)
                    
                    if fixture and fixture.result is not None:
                        actual_result = 1 if fixture.result == 1 else 2
                        pred_repo.verify(prediction.id, actual_result)
                        verified_count += 1
                
                db.commit()
            
            logger.info(f"✅ Verificadas {verified_count} predicciones")
            
        except Exception as e:
            logger.error(f"❌ Error verificando predicciones: {e}")
    
    def update_standings(self) -> None:
        """Actualiza las clasificaciones."""
        logger.info("📊 Actualizando clasificaciones...")
        
        try:
            current_season = datetime.now().year
            if datetime.now().month < 8:
                current_season -= 1
            
            with MasterCollector() as collector:
                result = collector.update_standings(
                    season=current_season,
                    league_ids=list(TOP_LEAGUES.keys())
                )
            
            logger.info(f"✅ Actualizadas {result['total']} posiciones")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando standings: {e}")
    
    def run_now(self, job_id: str) -> None:
        """Ejecuta un job inmediatamente."""
        jobs = {
            "sync_fixtures": self.sync_daily_fixtures,
            "generate_predictions": self.generate_daily_predictions,
            "verify_predictions": self.verify_predictions,
            "update_standings": self.update_standings
        }
        
        if job_id in jobs:
            logger.info(f"Ejecutando job manualmente: {job_id}")
            jobs[job_id]()
        else:
            logger.warning(f"Job no encontrado: {job_id}")
    
    def get_jobs_status(self) -> List[dict]:
        """Obtiene el estado de los jobs."""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]


# Instancia global del scheduler
scheduler = PredictionScheduler()

"""
Trainer - Módulo de entrenamiento y evaluación de modelos.

Proporciona funcionalidades para entrenar, evaluar y hacer backtesting.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from loguru import logger

from .base_predictor import BasePredictor
from .ensemble_predictor import EnsemblePredictor
from ..data.features import FeaturePipeline
from ..utils.config import settings


class ModelTrainer:
    """
    Entrenador de modelos con soporte para backtesting temporal.
    """
    
    def __init__(
        self,
        predictor: Optional[BasePredictor] = None,
        feature_pipeline: Optional[FeaturePipeline] = None
    ):
        """
        Inicializa el trainer.
        
        Args:
            predictor: Predictor a usar (default: EnsemblePredictor)
            feature_pipeline: Pipeline de features
        """
        self.predictor = predictor or EnsemblePredictor()
        self.feature_pipeline = feature_pipeline or FeaturePipeline()
        
        self.training_history: List[Dict[str, Any]] = []
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepara datos para entrenamiento.
        
        Args:
            df: DataFrame con features y target
            feature_columns: Columnas a usar (detecta automáticamente si None)
            
        Returns:
            Tuple de (X, y)
        """
        # Eliminar filas sin target
        df = df.dropna(subset=["target"])
        
        # Identificar columnas de features
        if feature_columns is None:
            exclude_cols = [
                "fixture_id", "home_team_id", "away_team_id",
                "league_id", "season", "date", "target"
            ]
            feature_columns = [c for c in df.columns if c not in exclude_cols]
        
        X = df[feature_columns]
        y = df["target"].astype(int)
        
        # Rellenar NaN con 0 o mediana
        X = X.fillna(0)
        
        logger.info(f"Datos preparados: {len(X)} muestras, {len(feature_columns)} features")
        
        return X, y
    
    def train(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None,
        save_model: bool = True,
        **kwargs
    ) -> Dict[str, float]:
        """
        Entrena el modelo con el dataset proporcionado.
        
        Args:
            df: DataFrame con features y target
            feature_columns: Columnas de features
            save_model: Si guardar el modelo después
            **kwargs: Argumentos adicionales para fit()
            
        Returns:
            Métricas del modelo
        """
        logger.info("Iniciando entrenamiento...")
        
        X, y = self.prepare_data(df, feature_columns)
        
        # Entrenar
        self.predictor.fit(X, y, **kwargs)
        
        # Guardar métricas en historial
        metrics = self.predictor.get_metrics()
        self.training_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "samples": len(X),
            "features": len(X.columns),
            "metrics": metrics
        })
        
        # Guardar modelo
        if save_model:
            model_path = self.predictor.save()
            logger.info(f"Modelo guardado: {model_path}")
        
        return metrics
    
    def cross_validate(
        self,
        df: pd.DataFrame,
        n_splits: int = 5,
        feature_columns: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Realiza validación cruzada temporal.
        
        Args:
            df: DataFrame con features y target
            n_splits: Número de splits
            feature_columns: Columnas de features
            
        Returns:
            Métricas promedio de CV
        """
        logger.info(f"Iniciando cross-validation con {n_splits} splits...")
        
        X, y = self.prepare_data(df, feature_columns)
        
        # Ordenar por fecha si está disponible
        if "date" in df.columns:
            indices = df.dropna(subset=["target"]).sort_values("date").index
            X = X.loc[indices]
            y = y.loc[indices]
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        fold_metrics = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            logger.info(f"Procesando fold {fold + 1}/{n_splits}...")
            
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Crear predictor nuevo para cada fold
            fold_predictor = EnsemblePredictor(name=f"cv_fold_{fold}")
            fold_predictor.fit(X_train, y_train)
            
            fold_metrics.append(fold_predictor.get_metrics())
        
        # Promediar métricas
        avg_metrics = {}
        for key in fold_metrics[0].keys():
            values = [m[key] for m in fold_metrics]
            avg_metrics[key] = np.mean(values)
            avg_metrics[f"{key}_std"] = np.std(values)
        
        logger.info("Cross-validation completado:")
        for k, v in avg_metrics.items():
            if not k.endswith("_std"):
                std = avg_metrics.get(f"{k}_std", 0)
                logger.info(f"  {k}: {v:.4f} ± {std:.4f}")
        
        return avg_metrics
    
    def backtest(
        self,
        df: pd.DataFrame,
        min_train_samples: int = 500,
        test_window_days: int = 30,
        min_confidence: float = 0.75,
        top_n: int = 5,
        feature_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Realiza backtesting simulando predicciones día a día.
        
        Args:
            df: DataFrame con features y target
            min_train_samples: Mínimo de muestras para empezar
            test_window_days: Días en cada ventana de test
            min_confidence: Confianza mínima para considerar
            top_n: Top N predicciones por ventana
            feature_columns: Columnas de features
            
        Returns:
            DataFrame con resultados del backtest
        """
        logger.info("Iniciando backtesting...")
        
        # Asegurar que está ordenado por fecha
        df = df.sort_values("date").reset_index(drop=True)
        
        X, y = self.prepare_data(df, feature_columns)
        dates = df.dropna(subset=["target"])["date"]
        
        results = []
        
        # Punto de inicio
        start_idx = min_train_samples
        
        while start_idx < len(X):
            # Ventana de train y test
            train_end = start_idx
            test_end = min(start_idx + test_window_days, len(X))
            
            X_train = X.iloc[:train_end]
            y_train = y.iloc[:train_end]
            X_test = X.iloc[train_end:test_end]
            y_test = y.iloc[train_end:test_end]
            dates_test = dates.iloc[train_end:test_end]
            
            if len(X_test) == 0:
                break
            
            logger.debug(
                f"Backtest window: train={len(X_train)}, test={len(X_test)}"
            )
            
            # Entrenar modelo
            predictor = EnsemblePredictor(name="backtest")
            predictor.fit(X_train, y_train)
            
            # Predecir
            preds_df = predictor.get_predictions_with_confidence(
                X_test, min_confidence=min_confidence
            )
            
            if len(preds_df) > 0:
                # Seleccionar top N
                top_preds = preds_df.head(top_n)
                
                for idx in top_preds.index:
                    local_idx = idx - train_end if idx >= train_end else idx
                    if local_idx < len(y_test):
                        actual = y_test.iloc[local_idx]
                        pred_winner = 1 if top_preds.loc[idx, "predicted_winner"] == 1 else 0
                        
                        results.append({
                            "date": dates_test.iloc[local_idx],
                            "predicted": top_preds.loc[idx, "predicted_winner"],
                            "actual": 1 if actual == 1 else 2,
                            "confidence": top_preds.loc[idx, "confidence"],
                            "prob_home": top_preds.loc[idx, "prob_home"],
                            "prob_away": top_preds.loc[idx, "prob_away"],
                            "correct": pred_winner == actual,
                            "train_size": len(X_train)
                        })
            
            start_idx = test_end
        
        results_df = pd.DataFrame(results)
        
        if len(results_df) > 0:
            accuracy = results_df["correct"].mean()
            logger.info(f"Backtest completado:")
            logger.info(f"  Total predicciones: {len(results_df)}")
            logger.info(f"  Accuracy: {accuracy:.4f}")
            logger.info(f"  Confianza media: {results_df['confidence'].mean():.4f}")
        
        return results_df
    
    def calculate_roi(
        self,
        backtest_results: pd.DataFrame,
        odds_home: Optional[pd.Series] = None,
        odds_away: Optional[pd.Series] = None,
        stake: float = 1.0
    ) -> Dict[str, float]:
        """
        Calcula ROI del backtest.
        
        Args:
            backtest_results: Resultados del backtest
            odds_home: Cuotas de local (opcional)
            odds_away: Cuotas de visitante (opcional)
            stake: Cantidad apostada por predicción
            
        Returns:
            Métricas de ROI
        """
        if len(backtest_results) == 0:
            return {"roi": 0.0, "profit": 0.0}
        
        # Sin cuotas, usar cuota promedio estimada de 1.9
        if odds_home is None:
            avg_odds = 1.9
        else:
            avg_odds = odds_home.mean()
        
        correct = backtest_results["correct"].sum()
        total = len(backtest_results)
        
        # Profit = (aciertos * cuota - total) / total
        profit = (correct * avg_odds * stake) - (total * stake)
        roi = profit / (total * stake) * 100
        
        return {
            "total_bets": total,
            "correct": correct,
            "accuracy": correct / total,
            "total_staked": total * stake,
            "profit": profit,
            "roi_percent": roi,
            "avg_confidence": backtest_results["confidence"].mean()
        }

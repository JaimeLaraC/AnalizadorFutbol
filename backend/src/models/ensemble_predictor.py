"""
Ensemble Predictor - Combina múltiples modelos para predicción.

Usa XGBoost, LightGBM y Logistic Regression con votación ponderada.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, log_loss, brier_score_loss
)
from loguru import logger

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost no disponible")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("LightGBM no disponible")

from .base_predictor import BasePredictor


class EnsemblePredictor(BasePredictor):
    """
    Predictor ensemble que combina múltiples modelos.
    
    Modelos incluidos:
    - XGBoost (si está disponible)
    - LightGBM (si está disponible)
    - Logistic Regression (siempre)
    """
    
    def __init__(
        self,
        name: str = "ensemble",
        use_calibration: bool = True,
        calibration_method: str = "isotonic"
    ):
        """
        Inicializa el ensemble.
        
        Args:
            name: Nombre del modelo
            use_calibration: Si aplicar calibración de probabilidades
            calibration_method: "isotonic" o "sigmoid" (Platt)
        """
        super().__init__(name)
        
        self.use_calibration = use_calibration
        self.calibration_method = calibration_method
        
        self.scaler = StandardScaler()
        self.models: Dict[str, Any] = {}
        self.weights: Dict[str, float] = {}
        self.calibrated_models: Dict[str, Any] = {}
    
    def _init_models(self) -> None:
        """Inicializa los modelos base."""
        # Logistic Regression (siempre)
        self.models["logreg"] = LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            random_state=42
        )
        self.weights["logreg"] = 0.2
        
        # XGBoost
        if HAS_XGBOOST:
            self.models["xgboost"] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss"
            )
            self.weights["xgboost"] = 0.4
        
        # LightGBM
        if HAS_LIGHTGBM:
            self.models["lightgbm"] = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1
            )
            self.weights["lightgbm"] = 0.4
        
        # Normalizar pesos
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        logger.info(f"Modelos inicializados: {list(self.models.keys())}")
        logger.info(f"Pesos: {self.weights}")
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: float = 0.2,
        **kwargs
    ) -> "EnsemblePredictor":
        """
        Entrena el ensemble.
        
        Args:
            X: Features de entrenamiento
            y: Target (1=home, 0=away)
            validation_split: Proporción para validación
            
        Returns:
            self
        """
        logger.info(f"Entrenando ensemble con {len(X)} muestras...")
        
        self._init_models()
        self.feature_names = list(X.columns)
        
        # Separar train/val para calibración
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Escalar features (solo para LogReg)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Entrenar cada modelo
        for name, model in self.models.items():
            logger.info(f"Entrenando {name}...")
            
            if name == "logreg":
                # LogReg usa features escaladas
                model.fit(X_train_scaled, y_train)
            else:
                # Tree models usan features originales
                model.fit(X_train, y_train)
            
            # Calcular score de validación
            if name == "logreg":
                val_score = model.score(X_val_scaled, y_val)
            else:
                val_score = model.score(X_val, y_val)
            
            logger.info(f"{name} validation accuracy: {val_score:.4f}")
        
        # Calibración de probabilidades
        if self.use_calibration:
            logger.info("Aplicando calibración de probabilidades...")
            self._calibrate_models(X_val, y_val)
        
        # Calcular métricas finales
        self._calculate_metrics(X_val, y_val)
        
        self.is_fitted = True
        self.metadata["trained_at"] = datetime.utcnow().isoformat()
        
        logger.info("Entrenamiento completado")
        return self
    
    def _calibrate_models(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> None:
        """Calibra las probabilidades de cada modelo."""
        X_val_scaled = self.scaler.transform(X_val)
        
        for name, model in self.models.items():
            try:
                if name == "logreg":
                    # LogReg ya está bien calibrado normalmente
                    self.calibrated_models[name] = model
                else:
                    calibrated = CalibratedClassifierCV(
                        model,
                        method=self.calibration_method,
                        cv="prefit"
                    )
                    calibrated.fit(X_val, y_val)
                    self.calibrated_models[name] = calibrated
                    
                logger.debug(f"Calibración de {name} completada")
                
            except Exception as e:
                logger.warning(f"Error calibrando {name}: {e}")
                self.calibrated_models[name] = model
    
    def predict_proba(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """
        Predice probabilidades combinando todos los modelos.
        
        Args:
            X: Features para predicción
            
        Returns:
            Array de probabilidades [P(away), P(home)]
        """
        if not self.is_fitted:
            raise ValueError("El modelo no está entrenado")
        
        X_scaled = self.scaler.transform(X)
        
        # Obtener probabilidades de cada modelo
        all_probas = []
        all_weights = []
        
        models_to_use = self.calibrated_models if self.use_calibration else self.models
        
        for name, model in models_to_use.items():
            try:
                if name == "logreg":
                    probas = model.predict_proba(X_scaled)
                else:
                    probas = model.predict_proba(X)
                
                all_probas.append(probas)
                all_weights.append(self.weights[name])
                
            except Exception as e:
                logger.warning(f"Error prediciendo con {name}: {e}")
        
        if not all_probas:
            raise ValueError("Ningún modelo pudo hacer predicciones")
        
        # Promedio ponderado
        all_probas = np.array(all_probas)
        all_weights = np.array(all_weights)
        all_weights = all_weights / all_weights.sum()  # Renormalizar
        
        weighted_probas = np.average(all_probas, axis=0, weights=all_weights)
        
        return weighted_probas
    
    def _calculate_metrics(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> None:
        """Calcula métricas del modelo en validación."""
        probas = self.predict_proba(X_val)
        predictions = self.predict(X_val)
        
        metrics = {
            "accuracy": accuracy_score(y_val, predictions),
            "precision": precision_score(y_val, predictions, zero_division=0),
            "recall": recall_score(y_val, predictions, zero_division=0),
            "f1": f1_score(y_val, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_val, probas[:, 1]),
            "log_loss": log_loss(y_val, probas),
            "brier_score": brier_score_loss(y_val, probas[:, 1]),
        }
        
        # Accuracy por nivel de confianza
        confidences = self.get_confidence(X_val)
        for threshold in [0.60, 0.65, 0.70, 0.75, 0.80]:
            mask = confidences >= threshold
            if mask.sum() > 0:
                metrics[f"accuracy_conf_{int(threshold*100)}"] = accuracy_score(
                    y_val[mask], predictions[mask]
                )
                metrics[f"coverage_conf_{int(threshold*100)}"] = mask.sum() / len(y_val)
        
        self.set_metrics(metrics)
        
        logger.info(f"Métricas calculadas:")
        for k, v in metrics.items():
            logger.info(f"  {k}: {v:.4f}")
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene importancia de features de los modelos tree-based.
        
        Returns:
            DataFrame con importancias
        """
        importances = {}
        
        for name in ["xgboost", "lightgbm"]:
            if name in self.models:
                model = self.models[name]
                if hasattr(model, "feature_importances_"):
                    importances[name] = model.feature_importances_
        
        if not importances:
            return pd.DataFrame()
        
        df = pd.DataFrame(importances, index=self.feature_names)
        df["mean"] = df.mean(axis=1)
        df = df.sort_values("mean", ascending=False)
        
        return df

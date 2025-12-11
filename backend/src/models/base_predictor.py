"""
Base Predictor - Clase base para modelos de predicción.

Define la interfaz común para todos los modelos.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from loguru import logger

from ..utils.config import settings


class BasePredictor(ABC):
    """
    Clase base abstracta para predictores.
    
    Define la interfaz que todos los modelos deben implementar.
    """
    
    def __init__(self, name: str = "base"):
        """
        Inicializa el predictor.
        
        Args:
            name: Nombre identificador del modelo
        """
        self.name = name
        self.model = None
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.metadata: Dict[str, Any] = {
            "created_at": None,
            "trained_at": None,
            "version": "1.0.0",
            "metrics": {}
        }
    
    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        **kwargs
    ) -> "BasePredictor":
        """
        Entrena el modelo.
        
        Args:
            X: Features de entrenamiento
            y: Target (1=home, 0=away)
            **kwargs: Argumentos adicionales
            
        Returns:
            self
        """
        pass
    
    @abstractmethod
    def predict_proba(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """
        Predice probabilidades.
        
        Args:
            X: Features para predicción
            
        Returns:
            Array de probabilidades [P(away), P(home)]
        """
        pass
    
    def predict(
        self,
        X: pd.DataFrame,
        threshold: float = 0.5
    ) -> np.ndarray:
        """
        Predice la clase ganadora.
        
        Args:
            X: Features para predicción
            threshold: Umbral de decisión
            
        Returns:
            Array de predicciones (1=home, 0=away)
        """
        probas = self.predict_proba(X)
        # probas[:, 1] es P(home gana)
        return (probas[:, 1] >= threshold).astype(int)
    
    def get_confidence(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """
        Obtiene el nivel de confianza de cada predicción.
        
        Args:
            X: Features para predicción
            
        Returns:
            Array con max(P(home), P(away)) para cada muestra
        """
        probas = self.predict_proba(X)
        return np.max(probas, axis=1)
    
    def get_predictions_with_confidence(
        self,
        X: pd.DataFrame,
        min_confidence: float = 0.75
    ) -> pd.DataFrame:
        """
        Obtiene predicciones filtradas por confianza.
        
        Args:
            X: Features
            min_confidence: Confianza mínima (default 75%)
            
        Returns:
            DataFrame con predicciones y confianza
        """
        probas = self.predict_proba(X)
        predictions = self.predict(X)
        confidence = self.get_confidence(X)
        
        df = pd.DataFrame({
            "predicted_winner": predictions.astype(int),
            "prob_home": probas[:, 1],
            "prob_away": probas[:, 0],
            "confidence": confidence
        })
        
        # Convertir predicted_winner: 1=home, 0=away a 1=home, 2=away
        df["predicted_winner"] = df["predicted_winner"].map({1: 1, 0: 2})
        
        # Filtrar por confianza
        df = df[df["confidence"] >= min_confidence]
        
        return df.sort_values("confidence", ascending=False)
    
    def save(self, path: Optional[Path] = None) -> Path:
        """
        Guarda el modelo en disco.
        
        Args:
            path: Ruta de guardado (usa default si None)
            
        Returns:
            Ruta donde se guardó
        """
        if path is None:
            path = settings.models_dir / f"{self.name}_model.pkl"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        save_data = {
            "model": self.model,
            "name": self.name,
            "is_fitted": self.is_fitted,
            "feature_names": self.feature_names,
            "metadata": self.metadata
        }
        
        with open(path, "wb") as f:
            pickle.dump(save_data, f)
        
        logger.info(f"Modelo guardado: {path}")
        return path
    
    def load(self, path: Path) -> "BasePredictor":
        """
        Carga el modelo desde disco.
        
        Args:
            path: Ruta del modelo
            
        Returns:
            self
        """
        with open(path, "rb") as f:
            save_data = pickle.load(f)
        
        self.model = save_data["model"]
        self.name = save_data["name"]
        self.is_fitted = save_data["is_fitted"]
        self.feature_names = save_data["feature_names"]
        self.metadata = save_data["metadata"]
        
        logger.info(f"Modelo cargado: {path}")
        return self
    
    def get_metrics(self) -> Dict[str, float]:
        """Retorna las métricas del modelo."""
        return self.metadata.get("metrics", {})
    
    def set_metrics(self, metrics: Dict[str, float]) -> None:
        """Actualiza las métricas del modelo."""
        self.metadata["metrics"] = metrics

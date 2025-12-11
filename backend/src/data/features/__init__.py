"""
Módulo de Feature Engineering.

Proporciona calculadores y pipeline para generar features de partidos.
"""

from .form_calculator import FormCalculator
from .standings_calculator import StandingsCalculator
from .h2h_calculator import H2HCalculator
from .pipeline import FeaturePipeline, MatchFeatures


__all__ = [
    # Calculadores
    "FormCalculator",
    "StandingsCalculator",
    "H2HCalculator",
    
    # Pipeline
    "FeaturePipeline",
    "MatchFeatures",
]

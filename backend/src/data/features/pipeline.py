"""
Pipeline principal de Feature Engineering.

Combina todos los calculadores para generar el dataset completo.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass

import pandas as pd
from loguru import logger

from .form_calculator import FormCalculator
from .standings_calculator import StandingsCalculator
from .h2h_calculator import H2HCalculator
from ...db import get_db_session, FixtureRepository
from ...db.models import Fixture


@dataclass
class MatchFeatures:
    """Features de un partido para predicción."""
    
    fixture_id: int
    home_team_id: int
    away_team_id: int
    league_id: int
    season: int
    date: datetime
    features: Dict[str, float]
    target: Optional[int] = None  # 1=home, 0=away, None=sin resultado


class FeaturePipeline:
    """
    Pipeline para generar features de partidos.
    
    Combina form, standings, h2h y otros calculadores.
    """
    
    def __init__(self):
        """Inicializa el pipeline."""
        self.form_calc = FormCalculator()
        self.standings_calc = StandingsCalculator()
        self.h2h_calc = H2HCalculator()
    
    def calculate_fixture_features(
        self,
        fixture: Fixture
    ) -> MatchFeatures:
        """
        Calcula todas las features para un partido.
        
        Args:
            fixture: Partido a procesar
            
        Returns:
            MatchFeatures con todas las features
        """
        features = {}
        
        home_id = fixture.home_team_id
        away_id = fixture.away_team_id
        match_date = fixture.date
        league_id = fixture.league_id
        season = fixture.season
        
        # 1. Features de forma
        logger.debug(f"Calculando forma para fixture {fixture.id}")
        
        home_form = self.form_calc.calculate_form_features(
            home_id, match_date, prefix="home_"
        )
        features.update(home_form)
        
        away_form = self.form_calc.calculate_form_features(
            away_id, match_date, prefix="away_"
        )
        features.update(away_form)
        
        # Forma específica local/visitante
        home_at_home = self.form_calc.calculate_home_away_form(
            home_id, match_date, is_home=True
        )
        features.update(home_at_home)
        
        away_at_away = self.form_calc.calculate_home_away_form(
            away_id, match_date, is_home=False
        )
        features.update(away_at_away)
        
        # 2. Features de standings (IMPORTANTE: usar match_date para evitar data leakage)
        logger.debug(f"Calculando standings para fixture {fixture.id}")
        
        standings_features = self.standings_calc.calculate_relative_features(
            home_id, away_id, league_id, season, before_date=match_date
        )
        features.update(standings_features)
        
        # 3. Features H2H
        logger.debug(f"Calculando H2H para fixture {fixture.id}")
        
        h2h_features = self.h2h_calc.calculate_h2h_features(
            home_id, away_id, match_date
        )
        features.update(h2h_features)
        
        # 4. Features derivadas
        features.update(self._calculate_derived_features(features))
        
        # Determinar target (si el partido está terminado)
        target = None
        if fixture.status == "FT" and fixture.result is not None:
            target = fixture.result
        
        return MatchFeatures(
            fixture_id=fixture.id,
            home_team_id=home_id,
            away_team_id=away_id,
            league_id=league_id,
            season=season,
            date=match_date,
            features=features,
            target=target
        )
    
    def _calculate_derived_features(
        self,
        features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calcula features derivadas de las existentes.
        
        Args:
            features: Features ya calculadas
            
        Returns:
            Features derivadas adicionales
        """
        derived = {}
        
        # Diferencias de forma
        if "home_points_last_5" in features and "away_points_last_5" in features:
            derived["diff_form_points_5"] = (
                features["home_points_last_5"] - features["away_points_last_5"]
            )
        
        if "home_goals_for_avg_5" in features and "away_goals_for_avg_5" in features:
            derived["diff_attack_strength"] = (
                features["home_goals_for_avg_5"] - features["away_goals_for_avg_5"]
            )
        
        if "home_goals_against_avg_5" in features and "away_goals_against_avg_5" in features:
            derived["diff_defense_strength"] = (
                features["away_goals_against_avg_5"] - features["home_goals_against_avg_5"]
            )
        
        # Índice de ataque vs defensa
        home_attack = features.get("home_goals_for_avg_5", 0)
        away_defense = features.get("away_goals_against_avg_5", 1)
        away_attack = features.get("away_goals_for_avg_5", 0)
        home_defense = features.get("home_goals_against_avg_5", 1)
        
        derived["home_attack_vs_away_defense"] = home_attack - away_defense
        derived["away_attack_vs_home_defense"] = away_attack - home_defense
        
        # Ventaja de posición relativa
        home_pos = features.get("home_position", 10)
        away_pos = features.get("away_position", 10)
        derived["position_advantage"] = away_pos - home_pos  # Positivo si local mejor
        
        # Momentum (tendencia de forma)
        home_points_5 = features.get("home_points_last_5", 0)
        home_points_10 = features.get("home_points_last_10", 0)
        if home_points_10 > 0:
            derived["home_momentum"] = home_points_5 / (home_points_10 / 2)
        else:
            derived["home_momentum"] = 1.0
        
        away_points_5 = features.get("away_points_last_5", 0)
        away_points_10 = features.get("away_points_last_10", 0)
        if away_points_10 > 0:
            derived["away_momentum"] = away_points_5 / (away_points_10 / 2)
        else:
            derived["away_momentum"] = 1.0
        
        return derived
    
    def generate_training_dataset(
        self,
        league_ids: Optional[List[int]] = None,
        season: Optional[int] = None,
        exclude_draws: bool = True
    ) -> pd.DataFrame:
        """
        Genera dataset de entrenamiento.
        
        Args:
            league_ids: Ligas a incluir
            season: Temporada
            exclude_draws: Si excluir empates (default True)
            
        Returns:
            DataFrame con features y target
        """
        logger.info("Generando dataset de entrenamiento...")
        
        data = []
        
        with get_db_session() as db:
            repo = FixtureRepository(db)
            fixtures = repo.get_finished_fixtures(exclude_draws=exclude_draws)
            
            if league_ids:
                fixtures = [f for f in fixtures if f.league_id in league_ids]
            if season:
                fixtures = [f for f in fixtures if f.season == season]
            
            logger.info(f"Procesando {len(fixtures)} partidos...")
            
            for i, fixture in enumerate(fixtures):
                try:
                    # Extraer datos del fixture mientras la sesión está activa
                    fixture_data = {
                        'id': fixture.id,
                        'home_team_id': fixture.home_team_id,
                        'away_team_id': fixture.away_team_id,
                        'league_id': fixture.league_id,
                        'season': fixture.season,
                        'date': fixture.date,
                        'status': fixture.status,
                        'result': fixture.result
                    }
                    
                    match_features = self.calculate_fixture_features(fixture)
                    
                    row = {
                        "fixture_id": match_features.fixture_id,
                        "home_team_id": match_features.home_team_id,
                        "away_team_id": match_features.away_team_id,
                        "league_id": match_features.league_id,
                        "season": match_features.season,
                        "date": match_features.date,
                        "target": match_features.target,
                        **match_features.features
                    }
                    data.append(row)
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Procesados {i + 1}/{len(fixtures)} partidos")
                        
                except Exception as e:
                    logger.warning(f"Error procesando fixture {fixture.id}: {e}")
                    continue
        
        df = pd.DataFrame(data)
        logger.info(f"Dataset generado: {len(df)} filas, {len(df.columns)} columnas")
        
        return df
    
    def generate_prediction_features(
        self,
        fixtures: List[Fixture]
    ) -> List[MatchFeatures]:
        """
        Genera features para predicción (partidos futuros).
        
        Args:
            fixtures: Lista de partidos a predecir
            
        Returns:
            Lista de MatchFeatures
        """
        results = []
        
        for fixture in fixtures:
            try:
                match_features = self.calculate_fixture_features(fixture)
                results.append(match_features)
            except Exception as e:
                logger.warning(f"Error en fixture {fixture.id}: {e}")
                continue
        
        return results
    
    def get_feature_names(self) -> List[str]:
        """Retorna lista de nombres de features."""
        # Generar un ejemplo para obtener nombres
        dummy_features = {
            # Form features
            "home_points_last_3": 0, "home_points_last_5": 0, "home_points_last_10": 0,
            "home_goals_for_avg_5": 0, "home_goals_against_avg_5": 0,
            "away_points_last_3": 0, "away_points_last_5": 0, "away_points_last_10": 0,
            "away_goals_for_avg_5": 0, "away_goals_against_avg_5": 0,
            # Standings
            "home_position": 0, "away_position": 0,
            "home_ppg": 0, "away_ppg": 0,
            "diff_position": 0, "diff_points": 0,
            # H2H
            "h2h_total_matches": 0, "h2h_home_win_rate": 0, "h2h_dominance": 0,
            # Derived
            "diff_form_points_5": 0, "diff_attack_strength": 0,
        }
        return list(dummy_features.keys())

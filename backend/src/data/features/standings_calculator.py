"""
Calculador de features de contexto de liga.

Genera features basadas en posiciones y estadísticas de temporada.
"""

from typing import Dict, Optional

from loguru import logger

from src.db import get_db_session, StandingRepository
from src.db.models import Standing


class StandingsCalculator:
    """
    Calcula features basadas en posiciones de liga.
    """
    
    def __init__(self):
        """Inicializa el calculador."""
        pass
    
    def _get_standing(
        self,
        team_id: int,
        league_id: int,
        season: int
    ) -> Optional[Dict]:
        """Obtiene la posición de un equipo en la liga como diccionario."""
        with get_db_session() as db:
            repo = StandingRepository(db)
            standing = repo.get_team_standing(team_id, league_id, season)
            if not standing:
                return None
            # Copiar datos a diccionario para evitar problemas de sesión
            return {
                'rank': standing.rank,
                'points': standing.points,
                'goals_diff': standing.goals_diff,
                'played': standing.played,
                'win': standing.win,
                'draw': standing.draw,
                'lose': standing.lose,
                'goals_for': standing.goals_for,
                'goals_against': standing.goals_against,
                'home_played': standing.home_played,
                'home_win': standing.home_win,
                'home_draw': standing.home_draw,
                'home_goals_for': standing.home_goals_for,
                'away_played': standing.away_played,
                'away_win': standing.away_win,
                'away_draw': standing.away_draw,
                'away_goals_for': standing.away_goals_for,
            }
    
    def calculate_standing_features(
        self,
        team_id: int,
        league_id: int,
        season: int,
        prefix: str = ""
    ) -> Dict[str, float]:
        """
        Calcula features de posición en liga.
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            season: Temporada
            prefix: Prefijo para nombres
            
        Returns:
            Diccionario de features
        """
        standing = self._get_standing(team_id, league_id, season)
        
        if not standing:
            # Sin datos, retornar valores por defecto
            return {
                f"{prefix}position": 10.0,  # Posición media por defecto
                f"{prefix}points": 0.0,
                f"{prefix}goal_diff": 0.0,
                f"{prefix}ppg": 0.0,
            }
        
        features = {}
        
        # Posición y puntos
        features[f"{prefix}position"] = float(standing['rank'] or 10)
        features[f"{prefix}points"] = float(standing['points'] or 0)
        features[f"{prefix}goal_diff"] = float(standing['goals_diff'] or 0)
        
        # Puntos por partido
        played = standing['played'] or 1
        features[f"{prefix}ppg"] = (standing['points'] or 0) / played
        
        # Estadísticas generales
        features[f"{prefix}played"] = float(standing['played'] or 0)
        features[f"{prefix}wins"] = float(standing['win'] or 0)
        features[f"{prefix}draws"] = float(standing['draw'] or 0)
        features[f"{prefix}losses"] = float(standing['lose'] or 0)
        features[f"{prefix}goals_for"] = float(standing['goals_for'] or 0)
        features[f"{prefix}goals_against"] = float(standing['goals_against'] or 0)
        
        # Ratios
        features[f"{prefix}win_ratio"] = (standing['win'] or 0) / played
        features[f"{prefix}goals_per_game"] = (standing['goals_for'] or 0) / played
        features[f"{prefix}conceded_per_game"] = (standing['goals_against'] or 0) / played
        
        # Stats como local
        home_played = standing['home_played'] or 1
        features[f"{prefix}home_wins"] = float(standing['home_win'] or 0)
        features[f"{prefix}home_ppg"] = (
            (standing['home_win'] or 0) * 3 + (standing['home_draw'] or 0)
        ) / home_played
        features[f"{prefix}home_goals_per_game"] = (standing['home_goals_for'] or 0) / home_played
        
        # Stats como visitante
        away_played = standing['away_played'] or 1
        features[f"{prefix}away_wins"] = float(standing['away_win'] or 0)
        features[f"{prefix}away_ppg"] = (
            (standing['away_win'] or 0) * 3 + (standing['away_draw'] or 0)
        ) / away_played
        features[f"{prefix}away_goals_per_game"] = (standing['away_goals_for'] or 0) / away_played
        
        return features
    
    def calculate_relative_features(
        self,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        season: int
    ) -> Dict[str, float]:
        """
        Calcula features relativas entre dos equipos.
        
        Args:
            home_team_id: ID del equipo local
            away_team_id: ID del equipo visitante
            league_id: ID de la liga
            season: Temporada
            
        Returns:
            Diccionario de features diferenciales
        """
        home_features = self.calculate_standing_features(
            home_team_id, league_id, season, "home_"
        )
        away_features = self.calculate_standing_features(
            away_team_id, league_id, season, "away_"
        )
        
        features = {}
        
        # Combinar features individuales
        features.update(home_features)
        features.update(away_features)
        
        # Calcular diferencias
        features["diff_position"] = (
            home_features["home_position"] - away_features["away_position"]
        )
        features["diff_points"] = (
            home_features["home_points"] - away_features["away_points"]
        )
        features["diff_goal_diff"] = (
            home_features["home_goal_diff"] - away_features["away_goal_diff"]
        )
        features["diff_ppg"] = (
            home_features["home_ppg"] - away_features["away_ppg"]
        )
        features["diff_win_ratio"] = (
            home_features["home_win_ratio"] - away_features["away_win_ratio"]
        )
        
        return features

"""
Calculador de features de contexto de liga.

Genera features basadas en posiciones y estadísticas de temporada.

IMPORTANTE: Este calculador ahora soporta cálculo de standings históricos
basados en la fecha del partido, lo que hace las predicciones reproducibles.
"""

from typing import Dict, Optional, List
from datetime import datetime
from collections import defaultdict

from loguru import logger
from sqlalchemy import and_, or_

from src.db import get_db_session, StandingRepository
from src.db.models import Standing, Fixture


class StandingsCalculator:
    """
    Calcula features basadas en posiciones de liga.
    
    Soporta dos modos:
    1. Standings actuales (de la tabla standings)
    2. Standings históricos (calculados dinámicamente desde fixtures)
    """
    
    def __init__(self, use_historical: bool = True):
        """
        Inicializa el calculador.
        
        Args:
            use_historical: Si True, calcula standings desde fixtures históricos.
                           Si False, usa la tabla standings actual.
        """
        self.use_historical = use_historical
    
    def _calculate_standing_from_fixtures(
        self,
        team_id: int,
        league_id: int,
        season: int,
        before_date: datetime
    ) -> Optional[Dict]:
        """
        Calcula el standing de un equipo basándose SOLO en partidos 
        anteriores a la fecha dada.
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            season: Temporada
            before_date: Solo considera partidos anteriores a esta fecha
            
        Returns:
            Diccionario con estadísticas del equipo o None si no hay datos
        """
        with get_db_session() as db:
            # Obtener todos los partidos del equipo en esa liga/temporada ANTES de la fecha
            fixtures = db.query(Fixture).filter(
                Fixture.league_id == league_id,
                Fixture.season == season,
                Fixture.date < before_date,
                Fixture.status == "FT",
                or_(
                    Fixture.home_team_id == team_id,
                    Fixture.away_team_id == team_id
                )
            ).all()
            
            if not fixtures:
                return None
            
            # Inicializar estadísticas
            stats = {
                'points': 0,
                'played': 0,
                'win': 0,
                'draw': 0,
                'lose': 0,
                'goals_for': 0,
                'goals_against': 0,
                'home_played': 0,
                'home_win': 0,
                'home_draw': 0,
                'home_lose': 0,
                'home_goals_for': 0,
                'home_goals_against': 0,
                'away_played': 0,
                'away_win': 0,
                'away_draw': 0,
                'away_lose': 0,
                'away_goals_for': 0,
                'away_goals_against': 0,
            }
            
            for f in fixtures:
                is_home = f.home_team_id == team_id
                home_goals = f.home_goals or 0
                away_goals = f.away_goals or 0
                
                stats['played'] += 1
                
                if is_home:
                    stats['home_played'] += 1
                    stats['goals_for'] += home_goals
                    stats['goals_against'] += away_goals
                    stats['home_goals_for'] += home_goals
                    stats['home_goals_against'] += away_goals
                    
                    if home_goals > away_goals:
                        stats['points'] += 3
                        stats['win'] += 1
                        stats['home_win'] += 1
                    elif home_goals == away_goals:
                        stats['points'] += 1
                        stats['draw'] += 1
                        stats['home_draw'] += 1
                    else:
                        stats['lose'] += 1
                        stats['home_lose'] += 1
                else:
                    stats['away_played'] += 1
                    stats['goals_for'] += away_goals
                    stats['goals_against'] += home_goals
                    stats['away_goals_for'] += away_goals
                    stats['away_goals_against'] += home_goals
                    
                    if away_goals > home_goals:
                        stats['points'] += 3
                        stats['win'] += 1
                        stats['away_win'] += 1
                    elif home_goals == away_goals:
                        stats['points'] += 1
                        stats['draw'] += 1
                        stats['away_draw'] += 1
                    else:
                        stats['lose'] += 1
                        stats['away_lose'] += 1
            
            stats['goals_diff'] = stats['goals_for'] - stats['goals_against']
            
            # El rank no lo podemos calcular sin conocer todos los equipos,
            # pero lo estimaremos basado en puntos por partido
            stats['rank'] = None  # Se calculará en calculate_relative_features
            
            return stats
    
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
        prefix: str = "",
        before_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calcula features de posición en liga.
        
        Args:
            team_id: ID del equipo
            league_id: ID de la liga
            season: Temporada
            prefix: Prefijo para nombres
            before_date: Si se proporciona y use_historical=True, calcula 
                        standings solo con partidos anteriores a esta fecha
            
        Returns:
            Diccionario de features
        """
        # Decidir qué método usar para obtener standings
        if self.use_historical and before_date:
            standing = self._calculate_standing_from_fixtures(
                team_id, league_id, season, before_date
            )
        else:
            standing = self._get_standing(team_id, league_id, season)
        
        if not standing:
            # Sin datos, retornar valores por defecto
            return {
                f"{prefix}position": 10.0,  # Posición media por defecto
                f"{prefix}points": 0.0,
                f"{prefix}goal_diff": 0.0,
                f"{prefix}ppg": 0.0,
                f"{prefix}played": 0.0,
                f"{prefix}wins": 0.0,
                f"{prefix}draws": 0.0,
                f"{prefix}losses": 0.0,
                f"{prefix}goals_for": 0.0,
                f"{prefix}goals_against": 0.0,
                f"{prefix}win_ratio": 0.0,
                f"{prefix}goals_per_game": 0.0,
                f"{prefix}conceded_per_game": 0.0,
                f"{prefix}home_wins": 0.0,
                f"{prefix}home_ppg": 0.0,
                f"{prefix}home_goals_per_game": 0.0,
                f"{prefix}away_wins": 0.0,
                f"{prefix}away_ppg": 0.0,
                f"{prefix}away_goals_per_game": 0.0,
            }
        
        features = {}
        
        # Posición - si es histórico, estimamos basado en puntos
        if standing.get('rank') is None:
            # Estimar posición basada en PPG (15 es media de liga)
            played = standing['played'] or 1
            ppg = (standing['points'] or 0) / played
            # PPG de 2.5+ = top 3, 2.0 = ~5, 1.5 = ~10, 1.0 = ~15, <0.5 = ~20
            estimated_rank = max(1, min(20, int(20 - (ppg * 6))))
            features[f"{prefix}position"] = float(estimated_rank)
        else:
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
        home_played = standing.get('home_played') or 1
        features[f"{prefix}home_wins"] = float(standing.get('home_win', 0) or 0)
        features[f"{prefix}home_ppg"] = (
            (standing.get('home_win', 0) or 0) * 3 + (standing.get('home_draw', 0) or 0)
        ) / home_played
        features[f"{prefix}home_goals_per_game"] = (standing.get('home_goals_for', 0) or 0) / home_played
        
        # Stats como visitante
        away_played = standing.get('away_played') or 1
        features[f"{prefix}away_wins"] = float(standing.get('away_win', 0) or 0)
        features[f"{prefix}away_ppg"] = (
            (standing.get('away_win', 0) or 0) * 3 + (standing.get('away_draw', 0) or 0)
        ) / away_played
        features[f"{prefix}away_goals_per_game"] = (standing.get('away_goals_for', 0) or 0) / away_played
        
        return features
    
    def calculate_relative_features(
        self,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        season: int,
        before_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calcula features relativas entre dos equipos.
        
        Args:
            home_team_id: ID del equipo local
            away_team_id: ID del equipo visitante
            league_id: ID de la liga
            season: Temporada
            before_date: Si se proporciona, calcula standings históricos
                        usando solo partidos anteriores a esta fecha
            
        Returns:
            Diccionario de features diferenciales
        """
        home_features = self.calculate_standing_features(
            home_team_id, league_id, season, "home_", before_date
        )
        away_features = self.calculate_standing_features(
            away_team_id, league_id, season, "away_", before_date
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

